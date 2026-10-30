"""Estado público de la cuenta y cambio de contraseña en una terminal externa."""
import os
import pwd
import shutil
import subprocess


def current_account():
    return pwd.getpwuid(os.getuid()).pw_name


def password_status(runner=subprocess.run, which=shutil.which):
    if not which("passwd"):
        return "Desconocido (passwd no disponible)"
    try:
        result = runner(["passwd", "-S"], capture_output=True, text=True, timeout=5)
        if result.returncode:
            return "Desconocido"
        fields = result.stdout.split()
        return {"P": "Configurada", "NP": "Sin contraseña", "L": "Cuenta bloqueada"}.get(
            fields[1] if len(fields) > 1 else "", "Desconocido")
    except (OSError, subprocess.TimeoutExpired):
        return "Desconocido"


def password_command(which=shutil.which):
    terminal, passwd = which("konsole"), which("passwd")
    if not terminal or not passwd:
        raise RuntimeError("Se necesita Konsole y passwd para cambiar la contraseña desde PlayCore.")
    # Sin shell, contraseña en argumentos, pipes ni registros. passwd opera sobre
    # la cuenta del proceso y pregunta en la terminal con la entrada oculta.
    return terminal, ["--separate", "--nofork", "--hold", "-e", passwd]
