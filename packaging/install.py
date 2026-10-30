#!/usr/bin/env python3
"""Instala el paquete offline en el espacio del usuario, sin sudo ni ensurepip."""
import argparse
import hashlib
import json
import os
import platform
import shlex
import shutil
import subprocess
import sys
import venv
from pathlib import Path

BUNDLE = Path(__file__).resolve().parent
BOOTSTRAP = "import runpy,sys;sys.path.insert(0,sys.argv.pop(1));runpy.run_module('pip',run_name='__main__')"


def verify_bundle(bundle):
    manifest = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    files = manifest["files"]
    for relative, expected in files.items():
        path = Path(relative)
        if path.is_absolute() or ".." in path.parts or not path.parts:
            raise ValueError("El manifiesto contiene una ruta no permitida.")
        actual = bundle / path
        if actual.is_symlink() or hashlib.sha256(actual.read_bytes()).hexdigest() != expected:
            raise ValueError(f"Archivo dañado o modificado: {relative}. Vuelve a copiar el paquete completo.")
    actual_files = {p.relative_to(bundle).as_posix() for folder in ("app", "wheels")
                    for p in (bundle / folder).rglob("*") if p.is_file()}
    expected_files = {p for p in files if p.startswith(("app/", "wheels/"))}
    if actual_files != expected_files:
        raise ValueError("El paquete contiene archivos ausentes o inesperados.")
    return manifest


def check_platform():
    if os.geteuid() == 0:
        raise RuntimeError("Abre el instalador como usuario normal, sin sudo.")
    if sys.version_info < (3, 11):
        raise RuntimeError("Se necesita Python 3.11 o posterior en el sistema de destino.")
    if platform.system() != "Linux" or platform.machine() != "x86_64":
        raise RuntimeError("Este paquete es para Linux x86_64 (Bazzite/SteamOS de 64 bits).")
    libc, version = platform.libc_ver()
    if libc != "glibc" or tuple(int(p) for p in version.split(".")[:2]) < (2, 34):
        raise RuntimeError("Se necesita glibc 2.34 o posterior para las bibliotecas Qt incluidas.")
    import tarfile
    if not hasattr(tarfile, "data_filter"):
        raise RuntimeError("Esta revisión de Python no incluye los filtros seguros de tarfile. Actualiza Python desde tu distribución.")


def desktop_quote(value):
    escaped = value.replace("\\", "\\\\\\\\").replace('"', '\\\\"').replace("`", "\\\\`").replace("$", "\\\\$").replace("%", "%%")
    return '"' + escaped + '"'


def write_shortcuts(installation, user_home):
    binary = user_home / ".local/bin/playcore"
    desktop = user_home / ".local/share/applications/playcore.desktop"
    for path, marker in ((binary, "# PlayCore launcher"), (desktop, "X-PlayCore-Managed=true")):
        if path.is_symlink() or (path.exists() and marker not in path.read_text(encoding="utf-8")):
            raise FileExistsError(f"Ya existe un acceso ajeno a este instalador: {path}")
    binary.parent.mkdir(parents=True, exist_ok=True)
    desktop.parent.mkdir(parents=True, exist_ok=True)
    launcher = installation / "abrir-playcore.sh"
    binary.write_text("#!/bin/sh\n# PlayCore launcher\nexec " + shlex.quote(str(launcher)) + ' "$@"\n', encoding="utf-8")
    binary.chmod(0o755)
    desktop.write_text(
        "[Desktop Entry]\nType=Application\nName=PlayCore\n"
        "Comment=Sistema, aplicaciones y complementos para tu equipo de juego\n"
        f"Exec={desktop_quote(str(binary))}\nIcon=applications-games\n"
        "Terminal=false\nCategories=Game;\nStartupNotify=true\n"
        "X-PlayCore-Managed=true\n", encoding="utf-8")
    return binary, desktop


def installation_path(bundle, destination):
    metadata = json.loads((bundle / "manifest.json").read_text(encoding="utf-8"))
    release_id = metadata["version"] + "-" + hashlib.sha256((bundle / "manifest.json").read_bytes()).hexdigest()[:12]
    return destination / "versions" / release_id


def install(bundle, destination, shortcuts=True):
    check_platform()
    print("Comprobando la integridad del paquete…", flush=True)
    metadata = verify_bundle(bundle)
    installation = installation_path(bundle, destination)
    python = installation / "venv/bin/python"
    if not installation.exists():
        installation.mkdir(parents=True)
        try:
            print("Copiando PlayCore y creando su entorno privado…", flush=True)
            shutil.copytree(bundle / "app", installation / "app")
            # Fedora/Bazzite puede carecer de ensurepip: se usa el wheel pip incluido.
            venv.EnvBuilder(with_pip=False).create(installation / "venv")
            wheels = bundle / "wheels"
            pip_wheels = list(wheels.glob("pip-*.whl"))
            if len(pip_wheels) != 1:
                raise ValueError("Se esperaba un único wheel de pip incluido.")
            print("Instalando las bibliotecas Qt incluidas, sin conexión…", flush=True)
            subprocess.run([
                str(python), "-I", "-c", BOOTSTRAP, str(pip_wheels[0]), "install",
                "--no-index", "--no-cache-dir", "--disable-pip-version-check",
                "--find-links", str(wheels), "PySide6-Essentials==" + metadata["qt_version"],
            ], check=True)
            launcher = installation / "abrir-playcore.sh"
            launcher.write_text("#!/bin/sh\n# PlayCore launcher\nexec " + shlex.quote(str(python)) +
                                " -I " + shlex.quote(str(installation / "app/launch.py")) + ' "$@"\n', encoding="utf-8")
            launcher.chmod(0o755)
            (installation / "package.json").write_text(json.dumps(metadata, indent=2), encoding="utf-8")
        except BaseException:
            # Solo se borra el directorio nuevo creado por esta ejecución fallida.
            shutil.rmtree(installation)
            raise
    print("Comprobando que Qt y PlayCore se pueden importar…", flush=True)
    subprocess.run([str(python), "-I", "-c",
                    "from PySide6.QtWidgets import QApplication; from PySide6.QtCore import qVersion; print('Qt:',qVersion())"], check=True)
    subprocess.run([str(python), "-I", str(installation / "app/launch.py"), "--help"], check=True)
    if shortcuts:
        binary, desktop = write_shortcuts(installation, Path.home())
        print(f"Acceso al menú: {desktop}\nLanzador: {binary}", flush=True)
    print(f"\nInstalación completada. Abre PlayCore desde el menú de aplicaciones.\n"
          f"También puedes ejecutar:\n{shlex.quote(str(installation / 'abrir-playcore.sh'))}\n"
          "Ya puedes retirar el USB o borrar la carpeta del instalador.", flush=True)
    return installation


def main():
    parser = argparse.ArgumentParser(description="Instalador offline de PlayCore para Bazzite/SteamOS x86_64")
    parser.add_argument("--dest", type=Path, default=Path.home() / ".local/share/playcore")
    parser.add_argument("--no-shortcuts", action="store_true", help="No crear accesos; útil para comprobar el paquete en una carpeta temporal")
    args = parser.parse_args()
    try:
        install(BUNDLE, args.dest.expanduser().resolve(), not args.no_shortcuts)
        return 0
    except Exception as exc:
        print(f"\nNo se completó la instalación: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
