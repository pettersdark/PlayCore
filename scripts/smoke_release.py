#!/usr/bin/env python3
"""Prueba el asistente offline en temporales, sin crear accesos ni instalar componentes."""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path

GUI_SMOKE = r'''
import importlib.util, sys, types
from pathlib import Path
bundle, destination, result_file = map(Path, sys.argv[1:4])
spec = importlib.util.spec_from_file_location('bootstrap', bundle/'installer_bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
shim = types.ModuleType('installer_gui')
def smoke(bundle, arguments):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QTimer
    spec = importlib.util.spec_from_file_location('real_gui', bundle/'installer_gui.py')
    gui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gui)
    app = QApplication([])
    window = gui.InstallerWindow(bundle, destination, shortcuts=False)
    assert not destination.exists(), 'Abrir el instalador no debe instalar nada'
    window.show()
    completed = []
    def finished(code, status):
        completed.append(code)
        window.grab().save('/tmp/playcore-1.0-installer-success.png')
        window.close()
        app.quit()
    window.process.finished.connect(finished)
    QTimer.singleShot(100, window.install_button.click)
    QTimer.singleShot(60000, app.quit)
    app.exec()
    assert completed == [0], window.log.toPlainText()
    assert window.open_button.isEnabled()
    assert 'completada' in window.status.text()
    assert (window.installed_path/'abrir-playcore.sh').is_file()
    result_file.write_text(str(window.installed_path))
    print('Asistente gráfico con Qt incluido: OK', flush=True)
    return 0
shim.main = smoke
sys.modules['installer_gui'] = shim
sys.argv = ['installer_bootstrap.py', str(bundle)]
raise SystemExit(bootstrap.main())
'''

APP_SMOKE = r'''
import sys
sys.path.insert(0, sys.argv[1])
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QTimer
from playcore.ui import MainWindow
from playcore import __version__
app = QApplication([])
window = MainWindow()
window.show()
completed = []
def finish():
    if window.worker.isRunning():
        QTimer.singleShot(100, finish)
        return
    assert window.snapshot is not None
    assert window.navigation.count() == 6
    assert {f.name for f in window.snapshot.proton} == {'Proton-CachyOS', 'Proton-GE'}
    assert all(panel.log.isHidden() for panel in window.message_panels)
    window.navigation.setCurrentRow(2)
    app.processEvents()
    window.grab().save('/tmp/playcore-1.0-installed-app.png')
    completed.append(True)
    window.close()
    app.quit()
QTimer.singleShot(100, finish)
QTimer.singleShot(30000, app.quit)
app.exec()
assert completed
print('Interfaz instalada PlayCore', __version__, ': OK')
'''


def main(bundle):
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    with tempfile.TemporaryDirectory(prefix="playcore-1.0-smoke-") as temp:
        destination = Path(temp) / "instalación gráfica con espacios"
        result = Path(temp) / "installed-path.txt"
        # Python del sistema, sin usar las dependencias del entorno de desarrollo.
        subprocess.run(["python3", "-I", "-c", GUI_SMOKE, str(bundle), str(destination), str(result)],
                       env=env, check=True, timeout=70)
        installed = Path(result.read_text())
        subprocess.run([str(installed / "abrir-playcore.sh"), "--help"], cwd="/tmp", env=env, check=True)
        subprocess.run([str(installed / "venv/bin/python"), "-I", "-c", APP_SMOKE, str(installed / "app")],
                       cwd="/tmp", env=env, check=True, timeout=40)
    print("Prueba offline terminada. Solo se utilizaron carpetas temporales.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    main(parser.parse_args().bundle.resolve())
