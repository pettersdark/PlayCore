"""Extracción controlada de temas y herramientas Proton en carpetas de usuario."""
import io
import json
import os
import re
import shutil
import stat
import tarfile
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def unpack_zip(payload, destination):
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        entries = archive.infolist()
        if len(entries) > 30000 or sum(e.file_size for e in entries) > 512 * 1024**2:
            raise ValueError("El ZIP de temas supera el límite permitido.")
        seen = set()
        for entry in entries:
            path = PurePosixPath(entry.filename)
            mode = entry.external_attr >> 16
            if (not path.parts or path.is_absolute() or ".." in path.parts
                    or "\\" in entry.filename or entry.filename.rstrip("/") != str(path)
                    or str(path) in seen or entry.flag_bits & 1
                    or stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR)):
                raise ValueError("El ZIP contiene rutas, enlaces o tipos de archivo no permitidos.")
            seen.add(str(path))
        archive.extractall(destination)


def publish_folder(source, destination):
    """Publica una carpeta nueva, sin mezclarla con instalaciones anteriores."""
    if destination.exists() or destination.is_symlink():
        return False
    with tempfile.TemporaryDirectory(prefix=".playcore-", dir=destination.parent) as temp:
        staged = Path(temp) / source.name
        shutil.copytree(source, staged)
        if destination.exists() or destination.is_symlink():
            return False
        os.rename(staged, destination)
    return True


def install_theme_zip(payload, themes_dir, expected_name):
    accepted_names = (expected_name,) if isinstance(expected_name, str) else expected_name
    themes_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="playcore-theme-") as temp:
        unpack_zip(payload, temp)
        matches = []
        for manifest in Path(temp).glob("*/theme.json"):
            if json.loads(manifest.read_text()).get("name") in accepted_names:
                matches.append(manifest.parent)
        if len(matches) != 1:
            raise ValueError(f"No se encuentra un único tema {expected_name} en el ZIP.")
        # No se admite contenido inesperado junto al tema solicitado.
        if any(p != matches[0] for p in Path(temp).iterdir()):
            raise ValueError("El ZIP contiene carpetas ajenas al tema solicitado.")
        return publish_folder(matches[0], themes_dir / matches[0].name)


def install_machine_zip(payload, themes_dir):
    themes_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix="playcore-machine-") as temp:
        unpack_zip(payload, temp)
        roots = list(Path(temp).iterdir())
        if len(roots) != 1 or not roots[0].is_dir():
            raise ValueError("El paquete de Machine Ready TV no tiene la estructura esperada.")
        root = roots[0]
        base = root / "Machine Ready/theme.json"
        if not base.is_file() or json.loads(base.read_text()).get("name") != "Machine Ready":
            raise ValueError("Falta el tema base Machine Ready.")
        sources = [p.parent for p in root.glob("*/theme.json")]
        sources += [p for p in (root / "Profiles").iterdir() if p.is_dir() and p.name.endswith(".profile")] if (root / "Profiles").is_dir() else []
        if len({p.name for p in sources}) != len(sources):
            raise ValueError("El paquete contiene nombres de tema o perfil duplicados.")
        added, skipped = [], []
        for source in sources:
            (added if publish_folder(source, themes_dir / source.name) else skipped).append(source.name)
        return added, skipped


def prepare_proton_latest(staged, component, metadata):
    """Mantiene el nombre fijo y el recibo que reconoce ProtonPlus."""
    manifest = staged / "compatibilitytool.vdf"
    content = manifest.read_text()
    tokens = list(re.finditer(r'"(?:\\.|[^"\\])*"|[{}]|//[^\n]*', content))
    tokens = [token for token in tokens if not token.group().startswith("//")]
    index, replacements, tools = 0, [], []

    def parse(path=()):
        nonlocal index
        while index < len(tokens) and tokens[index].group() != "}":
            key = tokens[index]
            if not key.group().startswith('"'):
                raise ValueError("Manifiesto Proton Latest no válido.")
            index += 1
            if index >= len(tokens):
                raise ValueError("Manifiesto Proton Latest incompleto.")
            value = tokens[index]
            index += 1
            current = (*path, key.group()[1:-1])
            if value.group() == "{":
                if path in (("compat_tools",), ("compatibilitytools", "compat_tools")):
                    tools.append(current)
                    replacements.append((key.start(), key.end()))
                parse(current)
                if index >= len(tokens) or tokens[index].group() != "}":
                    raise ValueError("Manifiesto Proton Latest incompleto.")
                index += 1
            elif value.group().startswith('"'):
                if path in tools and current[-1] == "display_name":
                    replacements.append((value.start(), value.end()))
            else:
                raise ValueError("Manifiesto Proton Latest no válido.")

    parse()
    if index != len(tokens) or len(tools) != 1 or len(replacements) != 2:
        raise ValueError("Se esperaba una única herramienta Proton con display_name.")
    for start, end in sorted(replacements, reverse=True):
        content = content[:start] + json.dumps(component + " Latest") + content[end:]
    manifest.write_text(content)
    (staged / ".protonplus").write_text(json.dumps(metadata, indent=2) + "\n")


def install_proton_archive(archive_path, steam_root, component="Proton-CachyOS", latest_metadata=None):
    prefixes = {"Proton-CachyOS": "proton-cachyos", "Proton-GE": "ge-proton"}
    prefix = prefixes[component]
    target_base = steam_root / "compatibilitytools.d"
    target_base.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(prefix=".playcore-", dir=target_base) as temp:
        with tarfile.open(archive_path, "r:*") as archive:
            members = archive.getmembers()
            if len(members) > 200000 or sum(m.size for m in members) > 5 * 1024**3:
                raise ValueError("El archivo Proton supera el límite permitido.")
            roots = set()
            for member in members:
                path = PurePosixPath(member.name)
                if not path.parts or path.is_absolute() or ".." in path.parts or "\\" in member.name:
                    raise ValueError("El archivo Proton contiene una ruta no permitida.")
                roots.add(path.parts[0])
                if not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                    raise ValueError("El archivo Proton contiene un tipo de archivo no permitido.")
                if member.issym() or member.islnk():
                    link = PurePosixPath(member.linkname)
                    if link.is_absolute():
                        raise ValueError("El archivo Proton contiene un enlace absoluto.")
                    relative = path.parent / link if member.issym() else link
                    normalized = os.path.normpath(str(relative)).split(os.sep)
                    if normalized[0] != path.parts[0] or "\\" in member.linkname:
                        raise ValueError("Un enlace de Proton sale de su carpeta.")
            if len(roots) != 1 or not next(iter(roots)).lower().startswith(prefix):
                raise ValueError(f"El archivo no contiene una única herramienta {component}.")
            # Además de las comprobaciones anteriores, aplica el filtro de seguridad
            # de tarfile. Disponible en las revisiones actuales de Python 3.11+.
            archive.extractall(temp, filter="data")
        staged = Path(temp) / next(iter(roots))
        if not (staged / "proton").is_file() or not (staged / "compatibilitytool.vdf").is_file():
            raise ValueError("Faltan los archivos de una herramienta de compatibilidad Steam.")
        if latest_metadata is not None:
            prepare_proton_latest(staged, component, latest_metadata)
        destination = target_base / (component + " Latest" if latest_metadata is not None else staged.name)
        if destination.exists() or destination.is_symlink():
            raise FileExistsError(f"Esta versión de {component} ya está instalada.")
        os.rename(staged, destination)
        return destination
