"""Entrada aislada de PolicyKit para los plugins del catálogo y Decky Loader."""
import hashlib
import os
import pwd
import subprocess
import sys
from pathlib import Path

# Python -I no añade el directorio del script a sys.path. Importación explícita
# del validador hermano; no se importa PySide6 ni configuración de usuario.
import importlib.util
import tempfile


def main():
    if os.geteuid() != 0 or not os.environ.get("PKEXEC_UID"):
        raise RuntimeError("Este ayudante debe iniciarse desde PlayCore mediante PolicyKit.")
    if len(sys.argv) == 3:
        component, archive_path, digest = "Decky Launch Options", *sys.argv[1:]
    elif len(sys.argv) == 4:
        component, archive_path, digest = sys.argv[1:]
    else:
        raise ValueError("Se esperaba el componente, el paquete y su SHA-256.")
    account = pwd.getpwuid(int(os.environ["PKEXEC_UID"]))
    if account.pw_uid == 0:
        raise RuntimeError("Abre PlayCore como usuario normal.")
    base = Path(account.pw_dir) / "homebrew"
    spec = importlib.util.spec_from_file_location("plugin_package", Path(__file__).with_name("plugin_package.py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    # Leer una única vez evita cambiar el paquete entre validación y extracción.
    if component not in module.PLUGIN_SPECS and component != "Decky Loader":
        raise ValueError("Componente no permitido.")
    with open(archive_path, "rb") as stream:
        payload = stream.read(module.MAX_DOWNLOAD + 1)
    if component == "Decky Loader":
        if (base / "services/PluginLoader").exists():
            raise FileExistsError("Decky ya está instalado. No se reemplaza desde este instalador.")
        if len(payload) > 1024 * 1024 or hashlib.sha256(payload).hexdigest() != digest:
            raise ValueError("No coincide el SHA-256 del instalador oficial de Decky.")
        env = dict(os.environ, SUDO_USER=account.pw_name, SUDO_UID=str(account.pw_uid),
                   SUDO_GID=str(account.pw_gid))
        # Copia privada de root: el script no puede cambiar mientras se ejecuta.
        with tempfile.TemporaryDirectory(prefix="playcore-decky-") as temp:
            script = Path(temp) / "install_release.sh"
            script.write_bytes(payload)
            result = subprocess.run(["/bin/bash", str(script)], env=env, timeout=600)
        if result.returncode:
            raise RuntimeError("El instalador oficial de Decky terminó con errores. Revisa el registro.")
        print("Instalador oficial de Decky completado.", flush=True)
        return
    if not (base / "services/PluginLoader").is_file() or not (base / "plugins").is_dir():
        raise RuntimeError("No se encuentra Decky en ~/homebrew. Instálalo primero.")
    version = module.deploy_package(payload, digest, base / "plugins",
                                    (account.pw_uid, account.pw_gid), component)
    print(f"{component} {version}: archivos instalados.", flush=True)
    completed = subprocess.run(["/usr/bin/systemctl", "restart", "plugin_loader.service"],
                               capture_output=True, text=True, timeout=45)
    if completed.returncode:
        raise RuntimeError("El plugin está copiado, pero no se pudo reiniciar Decky: " + completed.stderr)
    active = subprocess.run(["/usr/bin/systemctl", "is-active", "plugin_loader.service"],
                           capture_output=True, text=True, timeout=10)
    if active.returncode:
        raise RuntimeError("El plugin está copiado, pero Decky no está activo. Consulta su servicio.")
    print(f"Decky reiniciado. Comprueba {component} en el menú Decky de Gaming Mode.", flush=True)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(str(exc), file=sys.stderr)
        raise SystemExit(1)
