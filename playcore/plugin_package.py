"""Validación y despliegue de un paquete Decky, sin ejecutar código del ZIP."""
import hashlib
import io
import json
import os
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

PLUGIN_NAME = "Launch Options"
PLUGIN_SPECS = {
    "Decky Launch Options": ("Launch Options", "Launch Options", "decky-launch-options"),
    "CSS Loader": ("SDH-CssLoader", "CSS Loader", "SDH-CssLoader"),
    "HLTB": ("hltb-for-deck", "HLTB for Deck", "hltb-for-deck"),
    "SteamGridDB": ("decky-steamgriddb", "SteamGridDB", "decky-steamgriddb"),
}
MAX_DOWNLOAD = 32 * 1024 * 1024
MAX_EXPANDED = 128 * 1024 * 1024


def validate_package(payload: bytes, digest: str, component="Decky Launch Options"):
    root, manifest_name, package_name = PLUGIN_SPECS[component]
    if not digest or hashlib.sha256(payload).hexdigest() != digest:
        raise ValueError("La suma SHA-256 del paquete no coincide con la publicación oficial.")
    if len(payload) > MAX_DOWNLOAD:
        raise ValueError("El paquete supera el tamaño permitido.")
    with zipfile.ZipFile(io.BytesIO(payload)) as archive:
        entries = archive.infolist()
        if len(entries) > 5000 or sum(e.file_size for e in entries) > MAX_EXPANDED:
            raise ValueError("El contenido descomprimido supera el límite permitido.")
        names = set()
        for entry in entries:
            path = PurePosixPath(entry.filename)
            mode = entry.external_attr >> 16
            if (path.is_absolute() or ".." in path.parts or "\\" in entry.filename
                    or not path.parts or path.parts[0] != root
                    or entry.filename.rstrip("/") != path.as_posix()
                    or stat.S_ISLNK(mode) or (stat.S_IFMT(mode) not in (0, stat.S_IFREG, stat.S_IFDIR))
                    or entry.filename in names or entry.flag_bits & 1):
                raise ValueError("El ZIP contiene una ruta o tipo de archivo no permitido.")
            names.add(entry.filename)
        # Decky también admite plugins solo de frontend (HLTB no lleva main.py).
        for filename in ("plugin.json", "package.json", "dist/index.js"):
            if f"{root}/{filename}" not in names:
                raise ValueError(f"Falta {filename} en el plugin compilado.")
        manifest = json.loads(archive.read(f"{root}/plugin.json"))
        if manifest.get("name") != manifest_name or "root" in manifest.get("flags", []):
            raise ValueError("La identidad o los permisos del plugin no son los esperados.")
        package = json.loads(archive.read(f"{root}/package.json"))
        if package.get("name") != package_name or package.get("remote_binary"):
            raise ValueError("El paquete necesita un método de instalación diferente. Usa Decky.")
        return package.get("version", "desconocida")


def deploy_package(payload: bytes, digest: str, plugins_dir: Path, owner=None,
                   component="Decky Launch Options"):
    """Despliegue atómico de un plugin nuevo; nunca sobrescribe otro plugin."""
    version = validate_package(payload, digest, component)
    root = PLUGIN_SPECS[component][0]
    target = plugins_dir / root
    if target.exists() or target.is_symlink():
        raise FileExistsError(f"{component} ya existe. Usa Decky para actualizarlo.")
    # La carpeta de plugins debe existir: no se instala Decky implícitamente.
    with tempfile.TemporaryDirectory(prefix=".playcore-", dir=plugins_dir) as temp:
        with zipfile.ZipFile(io.BytesIO(payload)) as archive:
            archive.extractall(temp)
        staged = Path(temp) / root
        for item in [staged, *staged.rglob("*")]:
            item.chmod(0o755 if item.is_dir() or item.suffix == ".sh" else 0o644)
            if owner is not None:
                os.chown(item, *owner)
        if owner is not None:
            os.chown(staged, 0, 0)
            os.chown(staged / "plugin.json", 0, 0)
        if target.exists() or target.is_symlink():
            raise FileExistsError("El plugin se instaló desde otra aplicación. Actualiza el inventario.")
        # El directorio temporal se crea bajo el mismo sistema de archivos.
        os.rename(staged, target)
    return version
