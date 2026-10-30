import importlib.util
import os
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QProcess
from PySide6.QtWidgets import QApplication

spec = importlib.util.spec_from_file_location("playcore_graphical_installer", Path(__file__).resolve().parents[1] / "packaging/installer_gui.py")
gui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gui)


class GraphicalInstallerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def test_opening_installer_does_not_start_installation(self):
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / "destination"
            window = gui.InstallerWindow(Path(temp), target, shortcuts=False)
            self.assertEqual(window.process.state(), QProcess.ProcessState.NotRunning)
            self.assertFalse(target.exists())
            self.assertTrue(window.install_button.isEnabled())
            self.assertFalse(window.open_button.isEnabled())
            self.assertTrue(window.log.isHidden())
            window.details_button.click()
            self.assertFalse(window.log.isHidden())
            window.details_button.click()
            self.assertTrue(window.log.isHidden())
            window.close()

    def test_failed_installation_keeps_error_and_allows_retry(self):
        with tempfile.TemporaryDirectory() as temp:
            window = gui.InstallerWindow(Path(temp), Path(temp) / "destination", shortcuts=False)
            window.append_output("Fallo de prueba")
            window.install_finished(1, QProcess.ExitStatus.NormalExit)
            self.assertIn("No se completó", window.status.text())
            self.assertTrue(window.install_button.isEnabled())
            self.assertFalse(window.open_button.isEnabled())
            self.assertIn("Fallo de prueba", window.log.toPlainText())
            window.close()
