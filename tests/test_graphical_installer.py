import importlib.util
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

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

    def test_update_reopens_only_after_success_and_preserves_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp)
            launcher = bundle / "abrir-playcore.sh"
            launcher.touch()
            for opened in (True, False):
                window = gui.InstallerWindow(bundle, bundle, update=True)
                # Consume el arranque programado, sustituyendo solo el proceso real.
                with patch.object(window.process, "start"):
                    self.app.processEvents()
                with patch.object(gui, "load_core") as core, patch.object(
                        gui.QProcess, "startDetached", return_value=(opened, 123)), patch.object(gui.QMessageBox, "warning"):
                    core.return_value.installation_path.return_value = bundle
                    window.install_finished(0, QProcess.ExitStatus.NormalExit)
                self.assertEqual(window.update_completed, opened)
                self.assertTrue(window.open_button.isEnabled())
                window.close()
