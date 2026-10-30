"""Instaladores explícitos para el catálogo de PlayCore."""
import hashlib
import json
import os
import platform
import re
import shutil
import subprocess
import tempfile
import urllib.request
from urllib.parse import quote, urlencode
from pathlib import Path

from .catalog import APPLICATIONS, CSS_ALIASES, CSS_DEPENDENCIES, CSS_THEME_IDS
from .plugin_package import MAX_DOWNLOAD, PLUGIN_SPECS, validate_package
from .content_packages import install_machine_zip, install_proton_archive, install_theme_zip

REPOSITORY = "Wurielle/decky-launch-options"
RELEASE_API = f"https://api.github.com/repos/{REPOSITORY}/releases/latest"
FLATPAKS = {app.name: app.flatpak_id for app in APPLICATIONS}
DECKY_STORE = "https://plugins.deckbrew.xyz/plugins"
DECKY_CDN = "https://cdn.tzatzikiweeb.moe/file/steam-deck-homebrew/versions/"
CSS_API = "https://api.deckthemes.com"
MACHINE_REPOSITORY = "leoooorocha/Machine-Ready-TV"
INSTALLABLE = (*FLATPAKS, "Decky Loader", *PLUGIN_SPECS, "Proton-CachyOS", "Proton-GE",
               "Machine Ready TV", "Dependencias CSS", *CSS_DEPENDENCIES)


def fetch(url, limit=MAX_DOWNLOAD):
    request = urllib.request.Request(url, headers={"User-Agent": "PlayCore/1.0"})
    with urllib.request.urlopen(request, timeout=30) as response:
        data = response.read(limit + 1)
    if len(data) > limit:
        raise ValueError("La descarga supera el límite de tamaño.")
    return data


def download_file(url, destination, digest, progress):
    """Proton se transmite a disco, sin mantener cientos de MB en memoria."""
    total, last_report = 0, 0
    sha = hashlib.sha256()
    request = urllib.request.Request(url, headers={"User-Agent": "PlayCore/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response, open(destination, "wb") as stream:
        while chunk := response.read(1024 * 1024):
            total += len(chunk)
            if total > 1024**3:
                raise ValueError("La descarga de Proton supera 1 GiB.")
            stream.write(chunk)
            sha.update(chunk)
            if total - last_report >= 16 * 1024**2:
                progress(f"Descargando Proton: {total / 1024**2:.0f} MiB…")
                last_report = total
    if sha.hexdigest() != digest:
        raise ValueError("El SHA-256 de Proton no coincide con la publicación oficial.")


def github_asset(release, repository, asset_name):
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Se esperaba una publicación estable.")
    for asset in release.get("assets", []):
        if asset.get("name") == asset_name:
            url, digest = asset.get("browser_download_url") or "", asset.get("digest") or ""
            if not url.startswith(f"https://github.com/{repository}/releases/download/"):
                raise ValueError("La publicación apunta a un origen no permitido.")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise ValueError("La publicación no proporciona un SHA-256 válido.")
            return url, digest[7:]
    raise ValueError(f"No se encuentra {asset_name} en la publicación estable.")


def steam_installations(home, environ=None):
    env = os.environ if environ is None else environ
    data = Path(env.get("XDG_DATA_HOME", str(home / ".local/share")))
    candidates = (data / "Steam", home / ".steam/steam", home / ".steam/root",
                  home / ".var/app/com.valvesoftware.Steam/data/Steam")
    return tuple(dict.fromkeys(p.resolve() for p in candidates if p.is_dir()))


def select_release_asset(release):
    if release.get("draft") or release.get("prerelease"):
        raise ValueError("Se esperaba una publicación estable.")
    for asset in release.get("assets", []):
        if asset.get("name") == "decky-launch-options.zip":
            url = asset.get("browser_download_url") or ""
            digest = asset.get("digest") or ""
            if not url.startswith(f"https://github.com/{REPOSITORY}/releases/download/"):
                raise ValueError("La publicación apunta a un origen no permitido.")
            if not re.fullmatch(r"sha256:[0-9a-f]{64}", digest):
                raise ValueError("La publicación no proporciona SHA-256. Usa la instalación desde Decky.")
            return url, digest.removeprefix("sha256:")
    raise ValueError("No se encuentra el ZIP compilado en la publicación estable.")


class Installer:
    def __init__(self, home=None, runner=subprocess.run, downloader=fetch, which=shutil.which,
                 file_downloader=download_file):
        self.home = Path.home() if home is None else Path(home)
        self.runner = runner
        self.downloader = downloader
        self.which = which
        self.file_downloader = file_downloader

    def json(self, url):
        return json.loads(self.downloader(url, 8 * 1024**2))

    def run_helper(self, component, payload, digest, progress):
        if not self.which("pkexec"):
            raise RuntimeError("PolicyKit (pkexec) no está disponible para solicitar permisos.")
        progress("Autoriza la instalación en la ventana del escritorio. Si no tienes contraseña, configúrala desde Sistema.")
        with tempfile.TemporaryDirectory(prefix="playcore-install-") as temp:
            archive = Path(temp) / "package"
            archive.write_bytes(payload)
            helper = Path(__file__).with_name("install_helper.py").resolve()
            return self.runner(["pkexec", "/usr/bin/python3", "-I", str(helper), component,
                                str(archive), digest], capture_output=True, text=True, timeout=900)

    def install_css(self, names, progress):
        themes = self.home / "homebrew/themes"
        if not (self.home / "homebrew/services/PluginLoader").is_file():
            raise RuntimeError("Instala primero Decky Loader y CSS Loader.")
        manifests = (self.home / "homebrew/plugins").glob("*/plugin.json")
        if not any(self.manifest_name(p) == "CSS Loader" for p in manifests):
            raise RuntimeError("Instala primero el plugin CSS Loader desde la sección Decky.")
        visited = set()
        installed = {self.manifest_name(p) for p in themes.glob("*/theme.json")}

        def install_one(name, theme_id=None):
            aliases = CSS_ALIASES.get(name, (name,))
            if name in visited or any(alias in installed for alias in aliases):
                progress(f"{name}: ya presente; se conserva.")
                return
            visited.add(name)
            progress(f"Consultando el tema {name} en DeckThemes…")
            theme_id = theme_id or CSS_THEME_IDS.get(name)
            if theme_id is None:
                query = self.json(CSS_API + "/themes?" + urlencode({"search": name, "perPage": 100}))
                matches = [item for item in query.get("items", []) if item.get("name") in aliases and item.get("type", "").lower() == "css"]
                if len(matches) != 1:
                    raise ValueError(f"No se encuentra una única coincidencia oficial para {name}.")
                theme_id = matches[0]["id"]
            detail = self.json(CSS_API + "/themes/" + quote(theme_id, safe=""))
            if detail.get("name") not in aliases or not detail.get("approved") or detail.get("disabled"):
                raise ValueError(f"El tema {name} no está aprobado o no está disponible.")
            blob_id = detail["download"]["id"]
            payload = self.downloader(CSS_API + "/blobs/" + quote(blob_id, safe=""))
            install_theme_zip(payload, themes, aliases)
            progress(f"{name}: archivos instalados; activación manual en CSS Loader.")
            for dependency in detail.get("dependencies", []):
                install_one(dependency["name"], dependency["id"])
        for name in names:
            install_one(name)

    @staticmethod
    def manifest_name(path):
        try:
            data = json.loads(path.read_text())
            return data.get("name") if isinstance(data, dict) else None
        except (OSError, ValueError, UnicodeError):
            return None

    def install(self, name, progress=lambda _: None, steam_target=None):
        if name in FLATPAKS:
            if not self.which("flatpak"):
                raise RuntimeError("Flatpak no está disponible en este equipo.")
            progress(f"Instalando {name} desde Flathub para tu usuario…")
            result = self.runner(
                ["flatpak", "install", "--user", "--noninteractive", "--assumeyes", "--or-update",
                 "https://flathub.org/repo/appstream/" + FLATPAKS[name] + ".flatpakref"],
                capture_output=True, text=True, timeout=1800,
            )
        elif name in PLUGIN_SPECS:
            if not (self.home / "homebrew/services/PluginLoader").is_file():
                raise RuntimeError("Necesitas Decky Loader instalado en ~/homebrew antes de instalar el plugin.")
            if not self.which("pkexec"):
                raise RuntimeError("PolicyKit (pkexec) no está disponible para solicitar permisos.")
            progress(f"Consultando la versión estable de {name}…")
            if name == "Decky Launch Options":
                release = json.loads(self.downloader(RELEASE_API, 1024 * 1024))
                url, digest = select_release_asset(release)
            else:
                plugins = self.json(DECKY_STORE)
                plugin = next((p for p in plugins if p.get("name") == PLUGIN_SPECS[name][1]), None)
                if not plugin or not plugin.get("versions"):
                    raise ValueError(f"{name} no está disponible en la tienda de Decky.")
                version = plugin["versions"][0]
                digest = version.get("hash", "")
                if not re.fullmatch("[0-9a-f]{64}", digest):
                    raise ValueError("La tienda no proporciona un SHA-256 válido.")
                url = version.get("artifact") or DECKY_CDN + digest + ".zip"
                if not url.startswith((DECKY_CDN, "https://github.com/")):
                    raise ValueError("El origen del paquete no es el esperado.")
            progress("Descargando el plugin y verificando SHA-256…")
            payload = self.downloader(url)
            validate_package(payload, digest, name)
            result = self.run_helper(name, payload, digest, progress)
        elif name == "Decky Loader":
            if (self.home / "homebrew/services/PluginLoader").exists():
                raise FileExistsError("Decky Loader ya está instalado; se conserva.")
            progress("Descargando el instalador estable oficial de Decky Loader…")
            repository = "SteamDeckHomebrew/decky-installer"
            release = self.json(f"https://api.github.com/repos/{repository}/releases/latest")
            url, digest = github_asset(release, repository, "install_release.sh")
            payload = self.downloader(url, 1024**2)
            if hashlib.sha256(payload).hexdigest() != digest:
                raise ValueError("No coincide el SHA-256 del instalador de Decky.")
            result = self.run_helper(name, payload, digest, progress)
        elif name in ("Proton-CachyOS", "Proton-GE"):
            targets = steam_installations(self.home)
            if not targets:
                raise RuntimeError("No se encuentra Steam. Abre Steam al menos una vez antes de instalar Proton.")
            if steam_target is None and len(targets) > 1:
                raise ValueError("Selecciona la instalación de Steam de destino.")
            target = Path(steam_target).resolve() if steam_target else targets[0]
            if target not in targets:
                raise ValueError("El destino no es una instalación de Steam detectada.")
            repository = "CachyOS/proton-cachyos" if name == "Proton-CachyOS" else "GloriousEggroll/proton-ge-custom"
            release = self.json(f"https://api.github.com/repos/{repository}/releases/latest")
            architecture = {"x86_64": "x86_64", "aarch64": "arm64", "arm64": "arm64"}.get(platform.machine())
            if not architecture:
                raise RuntimeError("Arquitectura no soportada por este instalador de Proton.")
            ge_arch = "x86_64" if architecture == "x86_64" else "aarch64"
            pattern = (rf"proton-cachyos-.*-slr-{architecture}\.tar\.xz" if name == "Proton-CachyOS"
                       else rf"GE-Proton[0-9][A-Za-z0-9._-]*-{ge_arch}\.tar\.gz")
            assets = [a for a in release.get("assets", []) if re.fullmatch(pattern, a.get("name", ""))]
            if not assets and name == "Proton-GE" and architecture == "x86_64":
                assets = [a for a in release.get("assets", [])
                          if re.fullmatch(r"GE-Proton[0-9]+-[0-9]+\.tar\.gz", a.get("name", ""))]
            if len(assets) != 1:
                raise ValueError(f"No se encuentra una única publicación de {name} para esta arquitectura.")
            url, digest = github_asset(release, repository, assets[0]["name"])
            required = assets[0].get("size", 0) + 5 * 1024**3
            if shutil.disk_usage(target).free < required:
                raise RuntimeError("Necesitas espacio para la descarga y al menos 5 GiB para descomprimir Proton.")
            with tempfile.TemporaryDirectory(prefix="playcore-proton-", dir=target) as temp:
                archive = Path(temp) / "proton.tar.xz"
                self.file_downloader(url, archive, digest, progress)
                progress(f"Extrayendo {name} en la instalación de Steam elegida…")
                destination = install_proton_archive(archive, target, name)
            return f"Instalación de {name} completada.\nInstalado en {destination}. Reinicia Steam y selecciona {name} manualmente en Compatibilidad."
        elif name == "Machine Ready TV":
            self.install_css((), progress)  # Comprueba Decky y CSS Loader antes de escribir.
            progress("Consultando una revisión fija del repositorio Machine Ready TV…")
            commit = self.json(f"https://api.github.com/repos/{MACHINE_REPOSITORY}/commits/main")["sha"]
            if not re.fullmatch("[0-9a-f]{40}", commit):
                raise ValueError("La revisión del repositorio no es válida.")
            payload = self.downloader(f"https://codeload.github.com/{MACHINE_REPOSITORY}/zip/{commit}", 256 * 1024**2)
            added, skipped = install_machine_zip(payload, self.home / "homebrew/themes")
            progress(f"Machine Ready TV: {len(added)} carpetas añadidas y {len(skipped)} existentes conservadas.")
            self.install_css(CSS_DEPENDENCIES, progress)
            return "Instalación de Machine Ready TV completada.\nActiva Nav Patch, pulsa Refresh y elige manualmente el perfil en CSS Loader."
        elif name == "Dependencias CSS" or name in CSS_DEPENDENCIES:
            self.install_css(CSS_DEPENDENCIES if name == "Dependencias CSS" else (name,), progress)
            return f"Instalación de {name} completada.\nPulsa Refresh en CSS Loader; la activación es manual."
        else:
            raise ValueError("Este componente todavía requiere instalación manual.")
        if result.returncode:
            if result.returncode in (126, 127) and name in (*PLUGIN_SPECS, "Decky Loader"):
                raise RuntimeError("No se autorizó la instalación. El plugin no se ha instalado.")
            raise RuntimeError((result.stderr or result.stdout or "La instalación falló.").strip()[-8000:])
        return (result.stdout.strip()[-8000:] + f"\nInstalación de {name} completada.").strip()
