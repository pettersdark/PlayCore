"""Solicitud pública de importación; nunca accede a los ajustes de Decky."""
import json

from .catalog import PLUGINS
from .detection import normalized


WARNING = (
    "Requieren una versión compatible de Proton-CachyOS, seleccionada para el juego. "
    "La presencia de Proton no garantiza compatibilidad del juego ni del hardware. "
    "No actives Enable globally. Elige un único perfil por juego; el combinado "
    "sustituye a los individuales."
)

GUIDE = """PlayCore prepara la solicitud; todavía no se ha importado nada.
1. Abre Steam/Big Picture con Decky y Launch Options cargados.
2. Desde Chrome/Chromium abre chrome://inspect/#devices, configura localhost:8081
   (o IP_DEL_EQUIPO:8081 desde otro equipo) y pulsa Inspect en la ventana de Steam
   que contiene Decky. Requiere la depuración remota de Steam habilitada.
3. En Console, comprueba window.hasDeckyLaunchOptions === true. Si no es true,
   selecciona la ventana/contexto correcto o carga el plugin. No uses la consola
   de una página web ni una ventana Qt: no comparten el window de Steam.
4. Copia el script con el botón y ejecútalo en esa consola. Revisa el código antes
   de pegarlo; si el navegador bloquea el pegado, sigue su procedimiento de revisión.
5. Decky pedirá I understand y después Add to Decky Launch Options. Comprueba los
   tres comandos y deja Enable globally apagado en todos; puedes cancelar.
6. En Decky → Launch Options → Manage Launch Options, busca el grupo PlayCore y
   los nombres OptiScaler, FSR 4 Upgrade y OptiScaler + FSR 4. Comprueba sus IDs, On command,
   Off command vacío, Value ID común y Enable globally apagado. Sin valor por defecto.
7. En las opciones del juego elige None para desactivar o un solo valor del selector.
   Elimina/desactiva antes otros perfiles equivalentes o variables en Original launch
   options; el selector solo excluye los tres valores que importa PlayCore.
Para repetir, usa el mismo script y conserva los IDs: el plugin actualiza esas
entradas. No uses Duplicate ni crees copias manuales. El plugin puede conservar una
activación global anterior: apágala en Manage Launch Options ANTES de reimportar.
Si no tienes depuración remota o una versión con este evento y selectores, actualiza
el plugin o deja la importación pendiente. No se modifican archivos internos.
Fuente: https://github.com/Wurielle/decky-launch-options#integration-with-third-party-plugins
"""


def launch_options():
    """Un solo valueId ofrece exclusión mutua, sin valor activo predeterminado."""
    return [
        dict(id=identifier, name=label, group="PlayCore",
             valueId="playcore-fsr-optiscaler", valueName=label,
             on=command, off="", enableGlobally=False, fallbackValue=False)
        for identifier, label, command in (
            ("playcore-optiscaler", "OptiScaler", "PROTON_USE_OPTISCALER=1 %command%"),
            ("playcore-fsr4", "FSR 4 Upgrade", "PROTON_FSR4_UPGRADE=1 %command%"),
            ("playcore-optiscaler-fsr4", "OptiScaler + FSR 4",
             "PROTON_USE_OPTISCALER=1 PROTON_FSR4_UPGRADE=1 %command%"),
        )
    ]


def import_script(scanner):
    """Relee el manifiesto al pulsar, incluso si el inventario está desactualizado."""
    manifests = scanner.manifests(scanner.home / "homebrew/plugins", "plugin.json")
    if not any(normalized(alias) in manifests for alias in PLUGINS["Decky Launch Options"]):
        raise RuntimeError("Decky Launch Options no detectado. Instálalo desde Decky y actualiza la detección.")
    payload = json.dumps(launch_options(), ensure_ascii=False, indent=2)
    return (
        "// Ejecutar solo en la ventana de Steam con Decky Launch Options cargado.\n"
        "(() => {\n"
        "  if (window.hasDeckyLaunchOptions !== true) {\n"
        "    throw new Error('Decky Launch Options no está cargado en esta ventana');\n"
        "  }\n"
        "  window.dispatchEvent(new CustomEvent('dlo-add-launch-options', {\n"
        f"    detail: {payload}\n"
        "  }));\n"
        "  console.info('Solicitud enviada. Revisa y confirma en Decky; aún no confirma la importación.');\n"
        "})();\n"
    )
