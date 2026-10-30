#!/usr/bin/env python3
"""Construye una entrega offline sin incluir entornos, credenciales o datos locales."""
import argparse
import hashlib
import json
import shutil
import shlex
import tarfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys
sys.path.insert(0, str(ROOT))
from playcore import __version__ as VERSION
QT_VERSION = "6.12.0"
NAME = f"PlayCore-{VERSION}-Bazzite-x86_64"


def build(wheel_dir, output):
    bundle = output / NAME
    if bundle.exists():
        raise FileExistsError(f"La entrega ya existe: {bundle}. Elige otra carpeta de salida.")
    wanted = (
        f"pyside6_essentials-{QT_VERSION}-cp310-abi3-manylinux_2_34_x86_64.whl",
        f"pyside6_addons-{QT_VERSION}-cp310-abi3-manylinux_2_34_x86_64.whl",
        f"shiboken6-{QT_VERSION}-cp310-abi3-manylinux_2_34_x86_64.whl",
        "pip-26.1.2-py3-none-any.whl",
    )
    for filename in wanted:
        if not (wheel_dir / filename).is_file():
            raise FileNotFoundError(f"Falta la dependencia offline: {filename}")
    (bundle / "app/playcore").mkdir(parents=True)
    (bundle / "wheels").mkdir()
    for source in sorted((ROOT / "playcore").glob("*.py")):
        shutil.copyfile(source, bundle / "app/playcore" / source.name)
    for source, target in (("packaging/install.py", "instalar.py"),
                           ("packaging/instalar.sh", "instalar.sh"),
                           ("packaging/launch.py", "app/launch.py"),
                           ("packaging/installer_gui.py", "installer_gui.py"),
                           ("packaging/installer_bootstrap.py", "installer_bootstrap.py"),
                           ("packaging/LEEME.txt", "LEEME.txt"),
                           ("README.md", "README.md")):
        shutil.copyfile(ROOT / source, bundle / target)
    for filename in ("THIRD_PARTY.md", "RELEASE_NOTES.md"):
        if (ROOT / filename).is_file():
            shutil.copyfile(ROOT / filename, bundle / filename)
    (bundle / "docs").mkdir()
    for source in sorted((ROOT / "docs").glob("*.md")):
        shutil.copyfile(source, bundle / "docs" / source.name)
    for source in sorted((ROOT / "docs/images").rglob("*.png")):
        target = bundle / source.relative_to(ROOT)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
    (bundle / "instalar.sh").chmod(0o755)
    for filename in wanted:
        shutil.copyfile(wheel_dir / filename, bundle / "wheels" / filename)
    files = {p.relative_to(bundle).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in sorted(bundle.rglob("*")) if p.is_file()}
    metadata = {"version": VERSION, "qt_version": QT_VERSION, "architecture": "x86_64", "files": files}
    (bundle / "manifest.json").write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (bundle / "SHA256SUMS").write_text("".join(f"{digest}  {name}\n" for name, digest in files.items()), encoding="utf-8")
    archive = output / (NAME + ".tar.gz")
    with tarfile.open(archive, "w:gz") as stream:
        stream.add(bundle, arcname=NAME)
    (output / (archive.name + ".sha256")).write_text(
        hashlib.sha256(archive.read_bytes()).hexdigest() + "  " + archive.name + "\n", encoding="utf-8")
    build_executable(archive, output / (NAME + ".run"))
    print(f"Carpeta: {bundle}\nInstalador gráfico: {output / (NAME + '.run')}\n"
          f"Archivo comprimido: {archive}\nTamaño: {archive.stat().st_size / 1024**2:.1f} MiB")
    return bundle


def build_executable(archive, executable):
    payload = archive.read_bytes()
    digest = hashlib.sha256(payload).hexdigest()
    code = (ROOT / "packaging/self_extract.py").read_text(encoding="utf-8")
    code = code.replace("@PAYLOAD_SHA256@", digest).replace("@BUNDLE_NAME@", NAME)
    header = (
        f"#!/bin/sh\n# Instalador gráfico offline de PlayCore {VERSION}\n"
        "if ! command -v python3 >/dev/null 2>&1; then\n"
        "  if command -v kdialog >/dev/null 2>&1; then\n"
        "    kdialog --error 'PlayCore necesita Python 3.11 o posterior en el sistema.'\n"
        "  fi\n  exit 1\nfi\n"
        "exec python3 -I -c " + shlex.quote(code) + ' "$0" "$@"\n'
        "exit 1\n__PLAYCORE_PAYLOAD__\n"
    )
    executable.write_bytes(header.encode("utf-8") + payload)
    executable.chmod(0o755)
    executable.with_suffix(executable.suffix + ".sha256").write_text(
        hashlib.sha256(executable.read_bytes()).hexdigest() + "  " + executable.name + "\n", encoding="utf-8")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--wheel-dir", required=True, type=Path)
    parser.add_argument("--output", type=Path, default=ROOT / "entrega")
    args = parser.parse_args()
    build(args.wheel_dir.resolve(), args.output.resolve())
