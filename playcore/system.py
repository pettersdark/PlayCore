"""Lectura de os-release y hostname; nunca ejecuta su contenido."""
import os
import platform
import shlex
import socket
from pathlib import Path

from .models import SystemInfo


def read_os_release(path: Path) -> dict[str, str]:
    result = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        key, sep, value = line.partition("=")
        if not sep or not key.strip() or key.lstrip().startswith("#"):
            continue
        try:
            parts = shlex.split(value, comments=True)
        except ValueError:
            continue
        result[key.strip()] = " ".join(parts)
    return result


def detect_system(root: Path = Path("/"), environ=None) -> SystemInfo:
    env = os.environ if environ is None else environ
    data = {}
    for relative in ("etc/os-release", "usr/lib/os-release"):
        try:
            data = read_os_release(root / relative)
            break
        except (OSError, UnicodeError):
            continue
    identifier = data.get("ID", "").lower()
    # Bazzite images may expose a variant through their image metadata.
    image = " ".join(data.get(k, "") for k in ("IMAGE_ID", "VARIANT_ID", "NAME")).lower()
    distribution = "bazzite" if "bazzite" in identifier or "bazzite" in image else identifier
    try:
        hostname = (root / "etc/hostname").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeError):
        hostname = ""
    return SystemInfo(
        distribution, data.get("PRETTY_NAME", "Sistema desconocido"),
        data.get("VERSION_ID", "Desconocida"), hostname or socket.gethostname(),
        platform.release(), env.get("XDG_CURRENT_DESKTOP", "Desconocido"),
        env.get("XDG_SESSION_TYPE", "Desconocida"),
    )
