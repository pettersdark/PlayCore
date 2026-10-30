"""Entrega del evento público a Steam mediante su depurador local ya habilitado."""
import json
import time
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, build_opener

from PySide6.QtCore import QEventLoop, QTimer, QUrl
from PySide6.QtNetwork import QNetworkProxy
from PySide6.QtWebSockets import QWebSocket

from .launch_options import import_script


# Decky puede seguir cargado en SharedJSContext al salir de Big Picture. El
# evento no confirma que su modal se haya montado en una ventana de Steam.
IMPORT_DIALOG_VISIBLE = """(() => {
  const documents = new Set([document]);
  if (typeof g_PopupManager !== 'undefined') {
    for (const popup of g_PopupManager.m_mapPopups?.values() ?? []) {
      try {
        if (popup.window?.document) documents.add(popup.window.document);
      } catch (_) {}
    }
  }
  return [...documents].some(doc => {
    const text = doc.body?.innerText ?? '';
    return text.includes('FSR / OptiScaler') &&
      (text.includes('I understand') || text.includes('Add to Decky Launch Options'));
  });
})()"""


def wait_for_import_dialog(url, execute, timeout=3):
    deadline = time.monotonic() + timeout
    while True:
        try:
            if execute(url, IMPORT_DIALOG_VISIBLE) is True:
                return
        except RuntimeError:
            break
        if time.monotonic() >= deadline:
            break
        time.sleep(0.15)
    raise RuntimeError(
        "Steam recibió la solicitud, pero no se ha podido confirmar que el diálogo "
        "de Decky esté visible. Abre Steam en modo Big Picture y el panel Decky → "
        "Launch Options. Si no hay un diálogo pendiente, vuelve a pulsar el botón "
        "en PlayCore. No se ha confirmado la importación; no necesitas reiniciar el equipo.")


def local_socket(url):
    try:
        parsed = urlsplit(url)
        return (parsed.scheme == "ws" and parsed.hostname in {"127.0.0.1", "localhost", "::1"}
                and parsed.port == 8081 and not parsed.username and not parsed.password
                and parsed.path.startswith("/devtools/page/"))
    except (ValueError, TypeError):
        return False


def steam_targets():
    # No proxies, credenciales, redirecciones ni direcciones remotas del usuario.
    from urllib.request import HTTPRedirectHandler
    class NoRedirect(HTTPRedirectHandler):
        def redirect_request(self, *args, **kwargs):
            return None
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with opener.open("http://127.0.0.1:8081/json/list", timeout=2) as response:
        data = json.loads(response.read(1024 * 1024))
    if not isinstance(data, list):
        raise RuntimeError("Respuesta inesperada de Steam.")
    return [item for item in data if isinstance(item, dict) and item.get("type") == "page"
            and local_socket(item.get("webSocketDebuggerUrl", ""))][:64]


def evaluate(url, expression, timeout_ms=1500):
    """Una petición CDP acotada; se crea dentro del hilo que la utiliza."""
    socket = QWebSocket()
    socket.setProxy(QNetworkProxy(QNetworkProxy.ProxyType.NoProxy))
    loop = QEventLoop()
    timer = QTimer()
    timer.setSingleShot(True)
    result = []

    def received(message):
        try:
            data = json.loads(message)
        except ValueError:
            return
        if data.get("id") == 1:
            result.append(data)
            loop.quit()

    socket.connected.connect(lambda: socket.sendTextMessage(json.dumps({
        "id": 1, "method": "Runtime.evaluate",
        "params": {"expression": expression, "returnByValue": True, "timeout": 1000},
    })))
    socket.textMessageReceived.connect(received)
    socket.errorOccurred.connect(lambda _: loop.quit())
    socket.disconnected.connect(loop.quit)
    timer.timeout.connect(loop.quit)
    timer.start(timeout_ms)
    socket.open(QUrl(url))
    loop.exec()
    timer.stop()
    socket.abort()
    if not result:
        raise RuntimeError("Steam no confirmó la recepción. Comprueba el diálogo antes de repetir.")
    reply = result[0]
    if "error" in reply or "exceptionDetails" in reply.get("result", {}):
        raise RuntimeError("Steam no pudo ejecutar la solicitud. Comprueba el diálogo antes de repetir.")
    return reply.get("result", {}).get("result", {}).get("value")


def request_import(scanner, discover=steam_targets, execute=evaluate):
    script = import_script(scanner)
    try:
        targets = discover()
    except (OSError, ValueError) as exc:
        raise RuntimeError("No se puede conectar con Steam. Abre Big Picture con Decky y "
                           "la depuración remota habilitada, y vuelve a pulsar el botón.") from exc
    # Primero solo consulta disponibilidad. Nunca reintenta el evento tras un envío incierto.
    deadline = time.monotonic() + 10
    for target in sorted(targets, key=lambda item: item.get("title") not in {"SP", "SharedJSContext"}):
        if time.monotonic() > deadline:
            break
        url = target.get("webSocketDebuggerUrl", "")
        if not local_socket(url):
            continue
        try:
            available = execute(url, "window.hasDeckyLaunchOptions === true")
        except RuntimeError:
            continue
        if available is True:
            # Revalida en la misma expresión que emite el evento público.
            expression = "(() => {\n" + script + "\nreturn true;\n})()"
            if execute(url, expression) is not True:
                raise RuntimeError("Steam no confirmó la solicitud. Comprueba el diálogo antes de repetir.")
            wait_for_import_dialog(url, execute)
            return "Diálogo de importación localizado en Steam. Revisa y confirma los tres perfiles en Decky; deja Enable globally apagado. Importación pendiente de tu confirmación."
    raise RuntimeError("Launch Options está instalado pero no está cargado en una ventana accesible. "
                       "Abre Big Picture y el panel de Decky → Launch Options, y vuelve a intentarlo.")
