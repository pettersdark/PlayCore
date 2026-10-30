#!/usr/bin/env python3
"""Prueba el asistente offline en temporales, sin crear accesos ni instalar componentes."""
import argparse
import os
import subprocess
import tempfile
from pathlib import Path

GUI_SMOKE = r'''
import importlib.util, os, sys, types
from pathlib import Path
bundle, destination, result_file = map(Path, sys.argv[1:4])
spec = importlib.util.spec_from_file_location('bootstrap', bundle/'installer_bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
shim = types.ModuleType('installer_gui')
def smoke(bundle, arguments):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QSettings, QTimer
    spec = importlib.util.spec_from_file_location('real_gui', bundle/'installer_gui.py')
    gui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gui)
    app = QApplication([])
    preferences = QSettings(os.environ['PLAYCORE_SMOKE_SETTINGS'], QSettings.Format.IniFormat)
    window = gui.InstallerWindow(bundle, destination, shortcuts=False, settings=preferences)
    assert not destination.exists(), 'Abrir el instalador no debe instalar nada'
    window.show()
    completed = []
    def finished(code, status):
        completed.append(code)
        window.grab().save('/tmp/playcore-1.3-installer-success.png')
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
import os, sys
sys.path.insert(0, sys.argv[1])
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings, QTimer
from playcore.ui import MainWindow
from playcore import __version__
app = QApplication([])
preferences = QSettings(os.environ['PLAYCORE_SMOKE_SETTINGS'], QSettings.Format.IniFormat)
window = MainWindow(auto_scan=False, settings=preferences)
window.start_scan()
window.show()
completed = []
def finish():
    if window.worker.isRunning():
        QTimer.singleShot(100, finish)
        return
    assert window.snapshot is not None
    assert window.navigation.count() == 7
    assert {f.name for f in window.snapshot.proton} == {'Proton-CachyOS', 'Proton-GE'}
    assert all(panel.log.isHidden() for panel in window.message_panels)
    assert window.navigation.item(0).text() == 'Sistema'
    table = window.tables['Proton']
    window.language_combo.setCurrentIndex(window.language_combo.findData('en'))
    assert window.navigation.item(0).text() == 'System'
    assert window.tables['Proton'] is table
    assert table.horizontalHeaderItem(1).text() == 'Local status'
    window.install_message('Instalación de Proton-GE completada.')
    assert 'Installation of Proton-GE completed.' in window.install_logs[0].toPlainText()
    window.navigation.setCurrentRow(2)
    app.processEvents()
    window.grab().save('/tmp/playcore-1.3-installed-app-english.png')
    completed.append(True)
    window.close()
    app.quit()
QTimer.singleShot(100, finish)
QTimer.singleShot(30000, app.quit)
app.exec()
assert completed
print('Interfaz instalada PlayCore', __version__, ': OK')
'''

UPDATE_SMOKE = r'''
import importlib.util, os, subprocess, sys, types
from pathlib import Path
from unittest.mock import patch
bundle, destination = map(Path, sys.argv[1:3])
previous = destination/'versions/1.0.0-previous/keep.txt'
previous.parent.mkdir(parents=True)
previous.write_text('previous installation')
settings = destination/'user-settings.json'
settings.write_text('{"preserved": true}')
spec = importlib.util.spec_from_file_location('bootstrap', bundle/'installer_bootstrap.py')
bootstrap = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bootstrap)
shim = types.ModuleType('installer_gui')
def smoke(bundle, arguments):
    from PySide6.QtWidgets import QApplication
    from PySide6.QtCore import QSettings, QTimer
    spec = importlib.util.spec_from_file_location('update_gui', bundle/'installer_gui.py')
    gui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gui)
    app = QApplication([])
    reopened = []
    def open_installed(program, args):
        # Comprueba el lanzador real sin dejar otra ventana abierta en el equipo.
        subprocess.run([program, '--help'], check=True, timeout=20)
        reopened.append(program)
        return True, 123
    with patch.object(gui.QProcess, 'startDetached', side_effect=open_installed):
        preferences = QSettings(os.environ['PLAYCORE_SMOKE_SETTINGS'], QSettings.Format.IniFormat)
        window = gui.InstallerWindow(bundle, destination, shortcuts=False, update=True, settings=preferences)
        assert window.localizer.language == 'en'
        assert window.install_button.text() == 'Update PlayCore'
        window.show()
        QTimer.singleShot(60000, app.quit)
        app.exec()
    assert window.update_completed, window.log.toPlainText()
    assert 'installation completed' in window.status.text()
    assert len(reopened) == 1
    assert previous.read_text() == 'previous installation'
    assert settings.read_text() == '{"preserved": true}'
    assert (window.installed_path/'app/playcore/updater.py').is_file()
    print('Actualización automática, reapertura y conservación de datos: OK', flush=True)
    return 0
shim.main = smoke
sys.modules['installer_gui'] = shim
sys.argv = ['installer_bootstrap.py', str(bundle)]
raise SystemExit(bootstrap.main())
'''


def main(bundle):
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen")
    with tempfile.TemporaryDirectory(prefix="playcore-smoke-") as temp:
        env['PLAYCORE_SMOKE_SETTINGS'] = str(Path(temp) / 'preferences.ini')
        destination = Path(temp) / "instalación gráfica con espacios"
        result = Path(temp) / "installed-path.txt"
        # Python del sistema, sin usar las dependencias del entorno de desarrollo.
        subprocess.run(["python3", "-I", "-c", GUI_SMOKE, str(bundle), str(destination), str(result)],
                       env=env, check=True, timeout=70)
        installed = Path(result.read_text())
        subprocess.run([str(installed / "abrir-playcore.sh"), "--help"], cwd="/tmp", env=env, check=True)
        subprocess.run([str(installed / "venv/bin/python"), "-I", "-c", APP_SMOKE, str(installed / "app")],
                       cwd="/tmp", env=env, check=True, timeout=40)
        subprocess.run(["python3", "-I", "-c", UPDATE_SMOKE, str(bundle), str(Path(temp) / "update destination")],
                       env=env, check=True, timeout=70)
    print("Prueba offline terminada. Solo se utilizaron carpetas temporales.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bundle", type=Path, required=True)
    main(parser.parse_args().bundle.resolve())
