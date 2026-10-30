"""Código incrustado en el .run; verifica y extrae antes de abrir el asistente."""
import hashlib
import io
import shutil
import subprocess
import sys
import tarfile
import tempfile
from pathlib import Path


def main():
    if sys.version_info < (3, 11) or not hasattr(tarfile, "data_filter"):
        raise RuntimeError("PlayCore necesita Python 3.11 o posterior con los filtros seguros de tarfile.")
    # El constructor sustituye estas dos constantes antes de crear el ejecutable.
    expected = "@PAYLOAD_SHA256@"
    root_name = "@BUNDLE_NAME@"
    raw = Path(sys.argv[1]).read_bytes()
    marker = bytes([10]) + b"__PLAYCORE_PAYLOAD__" + bytes([10])
    offset = raw.index(marker) + len(marker)
    payload = raw[offset:]
    if hashlib.sha256(payload).hexdigest() != expected:
        raise ValueError("El fichero de instalación está incompleto o dañado. Vuelve a copiarlo o descargarlo.")
    with tempfile.TemporaryDirectory(prefix="playcore-installer-") as temp:
        with tarfile.open(fileobj=io.BytesIO(payload), mode="r:gz") as archive:
            archive.extractall(temp, filter="data")
        bundle = Path(temp) / root_name
        if "--verify-only" in sys.argv[2:]:
            import importlib.util
            spec = importlib.util.spec_from_file_location("core", bundle / "instalar.py")
            core = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(core)
            core.verify_bundle(bundle)
            print("Integridad del instalador PlayCore: OK")
            return 0
        return subprocess.call([sys.executable, "-I", str(bundle / "installer_bootstrap.py"),
                                str(bundle), *sys.argv[2:]])


try:
    raise SystemExit(main())
except Exception as exc:
    message = "No se pudo abrir el instalador de PlayCore:\n" + str(exc)
    if shutil.which("kdialog"):
        subprocess.run(["kdialog", "--title", "Instalar PlayCore", "--error", message], check=False)
    elif shutil.which("zenity"):
        subprocess.run(["zenity", "--error", "--text=" + message], check=False)
    else:
        print(message, file=sys.stderr)
    raise SystemExit(1)
