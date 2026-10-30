"""Actualizaciones estables desde el repositorio oficial, sin dependencias extra."""
import hashlib
import json
import platform
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlsplit
from urllib.request import Request, urlopen

from . import __version__

REPOSITORY = "pettersdark/PlayCore"
API_URL = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
RELEASES_URL = f"https://github.com/{REPOSITORY}/releases"
MAX_INSTALLER = 512 * 1024**2


def version_tuple(value):
    if not isinstance(value, str) or not re.fullmatch(r"v?\d+\.\d+\.\d+", value):
        raise ValueError("La versión publicada no es una versión estable válida.")
    return tuple(int(part) for part in value.removeprefix("v").split("."))


@dataclass(frozen=True)
class Release:
    version: str
    notes: str
    url: str
    filename: str
    download_url: str
    checksum_url: str
    size: int
    digest: str = ""


def official_asset(url, tag, filename):
    expected = f"https://github.com/{REPOSITORY}/releases/download/{tag}/{filename}"
    if url != expected:
        raise ValueError("La descarga no pertenece a la versión oficial de PlayCore.")
    return url


def parse_release(data, current=__version__):
    if data.get("draft") or data.get("prerelease"):
        return None
    tag = data.get("tag_name", "")
    if version_tuple(tag) <= version_tuple(current):
        return None
    version = tag.removeprefix("v")
    filename = f"PlayCore-{version}-Bazzite-x86_64.run"
    assets = {asset["name"]: asset for asset in data.get("assets", [])}
    if filename not in assets or filename + ".sha256" not in assets:
        raise ValueError("La nueva versión todavía no incluye el instalador y su SHA-256. Inténtalo más tarde.")
    asset = assets[filename]
    size = asset.get("size", 0)
    if not isinstance(size, int) or not 0 < size <= MAX_INSTALLER:
        raise ValueError("El tamaño del instalador no es válido.")
    return Release(version, str(data.get("body") or "Sin notas de versión."),
                   f"{RELEASES_URL}/tag/{tag}", filename,
                   official_asset(asset.get("browser_download_url"), tag, filename),
                   official_asset(assets[filename + ".sha256"].get("browser_download_url"), tag, filename + ".sha256"),
                   size, asset.get("digest") or "")


def request(url):
    return urlopen(Request(url, headers={"User-Agent": f"PlayCore/{__version__}",
                                         "Accept": "application/vnd.github+json" if url == API_URL else "application/octet-stream"}),
                   timeout=30)


def check_latest():
    try:
        with request(API_URL) as response:
            raw = response.read(2 * 1024**2 + 1)
        if len(raw) > 2 * 1024**2:
            raise ValueError("La respuesta de GitHub es demasiado grande.")
        return parse_release(json.loads(raw))
    except HTTPError as exc:
        if exc.code == 404:
            raise RuntimeError("Todavía no hay una versión pública disponible en GitHub.") from exc
        if exc.code in (403, 429):
            raise RuntimeError("GitHub ha limitado las consultas. Vuelve a intentarlo más tarde.") from exc
        raise RuntimeError(f"No se pudo consultar GitHub (HTTP {exc.code}).") from exc
    except (URLError, TimeoutError) as exc:
        raise RuntimeError("No se pudo conectar con GitHub. Comprueba tu conexión e inténtalo de nuevo.") from exc


def installation_destination(module_path=None):
    """Solo autoactualizar instalaciones creadas por nuestro instalador."""
    source = Path(module_path or __file__).resolve()
    installation = source.parent.parent.parent
    if (source.parent.name == "playcore" and source.parent.parent.name == "app"
            and installation.parent.name == "versions"
            and (installation / "package.json").is_file()
            and (installation / "abrir-playcore.sh").is_file()):
        return installation.parent.parent
    return None


class Updater:
    def __init__(self):
        self.temporary = None

    def check(self):
        return check_latest()

    def download(self, release, progress):
        if platform.system() != "Linux" or platform.machine() != "x86_64":
            raise RuntimeError("El actualizador necesita Linux x86_64.")
        tag = release.url.rsplit("/", 1)[-1]
        official_asset(release.download_url, tag, release.filename)
        official_asset(release.checksum_url, tag, release.filename + ".sha256")
        self.cleanup()
        self.temporary = tempfile.TemporaryDirectory(prefix="playcore-update-")
        target = Path(self.temporary.name) / release.filename
        try:
            progress(0)
            with request(release.checksum_url) as response:
                checksum = response.read(4097).decode("ascii").strip()
            match = re.fullmatch(r"([a-fA-F0-9]{64})\s+\*?" + re.escape(release.filename), checksum)
            if not match:
                raise ValueError("El fichero SHA-256 no es válido.")
            expected = match[1].lower()
            if release.digest and release.digest != "sha256:" + expected:
                raise ValueError("El SHA-256 publicado por GitHub no coincide con el fichero de comprobación.")
            digest = hashlib.sha256()
            count = 0
            with request(release.download_url) as response, target.open("wb") as output:
                if urlsplit(response.geturl()).scheme != "https":
                    raise ValueError("La descarga debe utilizar HTTPS.")
                while chunk := response.read(1024 * 1024):
                    count += len(chunk)
                    if count > release.size or count > MAX_INSTALLER:
                        raise ValueError("El instalador supera el tamaño esperado.")
                    output.write(chunk)
                    digest.update(chunk)
                    progress(min(99, count * 100 // release.size))
            if count != release.size or digest.hexdigest() != expected:
                raise ValueError("El instalador está incompleto o su SHA-256 no coincide. No se ha instalado nada.")
            progress(100)
            return target
        except BaseException:
            self.cleanup()
            raise

    def cleanup(self):
        if self.temporary is not None:
            self.temporary.cleanup()
            self.temporary = None
