"""Arranca Qt desde los wheels incluidos, sin instalar nada antes del clic."""
import importlib.util
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path, PurePosixPath


def show_error(message):
    if shutil.which("kdialog"):
        subprocess.run(["kdialog", "--title", "Instalar PlayCore", "--error", message], check=False)
    elif shutil.which("zenity"):
        subprocess.run(["zenity", "--error", "--title=Instalar PlayCore", "--text=" + message], check=False)
    else:
        print(message, file=sys.stderr)


def main():
    # El instalador importa las traducciones del paquete verificado. No debe
    # añadir __pycache__ al contenido que vuelve a comprobar instalar.py.
    sys.dont_write_bytecode = True
    bundle = Path(sys.argv[1]).resolve()
    spec = importlib.util.spec_from_file_location("playcore_installer_core", bundle / "instalar.py")
    core = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(core)
    core.check_platform()
    core.verify_bundle(bundle)
    with tempfile.TemporaryDirectory(prefix="playcore-installer-qt-") as temp:
        for pattern in ("pyside6_essentials-*.whl", "shiboken6-*.whl"):
            candidates = list((bundle / "wheels").glob(pattern))
            if len(candidates) != 1:
                raise ValueError("Falta una biblioteca Qt incluida en el instalador.")
            with zipfile.ZipFile(candidates[0]) as archive:
                for name in archive.namelist():
                    path = PurePosixPath(name)
                    if path.is_absolute() or ".." in path.parts or "\\" in name:
                        raise ValueError("Ruta no permitida en una biblioteca incluida.")
                archive.extractall(temp)
        sys.path.insert(0, temp)
        sys.path.insert(0, str(bundle))
        sys.path.insert(0, str(bundle / "app"))
        from installer_gui import main as graphical_main
        return graphical_main(bundle, sys.argv[2:])


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        show_error("No se pudo abrir el instalador de PlayCore:\n" + str(exc))
        raise SystemExit(1)
