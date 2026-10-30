import os
import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
from PySide6.QtCore import QEventLoop, QSettings, QTimer
from PySide6.QtWidgets import QApplication

from playcore.detection import Scanner
from playcore.ui import MainWindow
from playcore.updater import parse_release
from tests.test_updater import release_data


class GuiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.scanner = Scanner(self.home, self.home, {}, which=lambda _: None)
        self.window = MainWindow(self.scanner, auto_scan=False,
                                 settings=QSettings(str(self.home / "ui.ini"), QSettings.Format.IniFormat))
        self.addCleanup(self.window.close)

    def test_seven_sections_and_inventory(self):
        self.window.render_snapshot(self.scanner.scan())
        self.assertEqual(self.window.navigation.count(), 7)
        self.assertEqual(self.window.tables["Temas"].rowCount(), 15)
        self.assertEqual(self.window.tables["Decky"].rowCount(), 5)
        for index in range(7):
            self.window.navigation.setCurrentRow(index)
            self.assertEqual(self.window.pages.currentIndex(), index)

    def test_profile_is_manual_and_does_not_write_files(self):
        profile = self.home / "homebrew/themes/Soft Play.profile"
        profile.mkdir(parents=True)
        self.window.render_snapshot(self.scanner.scan())
        self.assertIsNone(self.window.profile_combo.currentData())
        self.window.profile_combo.setCurrentIndex(1)
        self.assertIn("manualmente", self.window.profile_note.text())
        self.assertEqual(list(profile.iterdir()), [])
        self.assertFalse((self.home / "homebrew/settings").exists())
        self.window.render_snapshot(self.scanner.scan())
        self.assertEqual(self.window.profile_combo.currentData(), "Soft Play.profile")

    def test_update_check_uses_worker_and_exposes_new_release(self):
        release = parse_release(release_data())
        with patch.object(self.window.updater, "check", return_value=release), patch(
                "playcore.ui.installation_destination", return_value=self.home):
            loop = QEventLoop()
            self.window.check_updates_button.click()
            self.window.update_worker.finished.connect(loop.quit)
            QTimer.singleShot(5000, loop.quit)
            loop.exec()
            self.app.processEvents()
            self.assertIn("1.4.0", self.window.update_status.text())
            self.assertTrue(self.window.apply_update_button.isEnabled())
            self.assertEqual(self.window.release_notes.toPlainText(), "Novedades de prueba")
            self.assertIn("1.4.0", self.window.updates_shortcut.text())

    def test_update_download_error_preserves_current_app_and_allows_retry(self):
        from PySide6.QtWidgets import QMessageBox
        self.window.available_release = parse_release(release_data())
        with patch("playcore.ui.installation_destination", return_value=self.home), patch(
                "playcore.ui.QMessageBox.question", return_value=QMessageBox.StandardButton.Yes), patch.object(
                self.window.updater, "download", side_effect=ValueError("SHA-256 incorrecto")):
            loop = QEventLoop()
            self.window.apply_update()
            self.window.update_worker.finished.connect(loop.quit)
            QTimer.singleShot(5000, loop.quit)
            loop.exec()
            self.app.processEvents()
            self.assertIn("SHA-256", self.window.update_status.text())
            self.assertTrue(self.window.apply_update_button.isEnabled())
            self.assertFalse(self.window.update_active)
            self.assertEqual(self.window.update_process.state(), self.window.update_process.ProcessState.NotRunning)

    def test_source_copy_checks_but_does_not_install_updates(self):
        self.window.show_update_release(parse_release(release_data()))
        self.assertFalse(self.window.apply_update_button.isEnabled())
        self.assertIn("código fuente", self.window.update_install_hint.text())

    def test_proton_latest_remains_available_with_an_older_version(self):
        (self.home / "etc").mkdir()
        (self.home / "etc/os-release").write_text("ID=steamos")
        steam = self.home / ".local/share/Steam"
        for version in ("proton-cachyos-old", "GE-Proton10-1"):
            folder = steam / "compatibilitytools.d" / version
            folder.mkdir(parents=True)
            (folder / "proton").touch()
            (folder / "compatibilitytool.vdf").touch()
        with patch("playcore.ui.steam_installations", return_value=(steam,)):
            self.window.render_snapshot(self.scanner.scan())
        for name in ("Proton-CachyOS", "Proton-GE"):
            button = self.window.install_buttons[name]
            self.assertTrue(button.isEnabled())
            self.assertIn("Latest", button.text())
        self.assertIs(self.window.proton_mode_combo.currentData(), True)
        self.window.proton_mode_combo.setCurrentIndex(1)
        self.assertNotIn("Latest", self.window.install_buttons["Proton-GE"].text())

    def test_background_scan_and_refresh(self):
        loop = QEventLoop()
        self.window.start_scan()
        self.assertFalse(self.window.refresh_button.isEnabled())
        self.window.worker.finished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        self.assertFalse(self.window.worker.isRunning())
        self.app.processEvents()
        self.assertIsNotNone(self.window.snapshot)
        self.assertTrue(self.window.refresh_button.isEnabled())

    def test_worker_error_is_visible(self):
        class BrokenScanner:
            def scan(self):
                raise OSError("lectura fallida")
        self.window.scanner = BrokenScanner()
        loop = QEventLoop()
        self.window.start_scan()
        self.window.worker.finished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        self.app.processEvents()
        self.assertIn("lectura fallida", self.window.diagnostics.toPlainText())
        self.assertTrue(self.window.refresh_button.isEnabled())

    def test_install_buttons_only_for_missing_items_on_supported_system(self):
        (self.home / "etc").mkdir()
        (self.home / "etc/os-release").write_text("ID=steamos")
        loader = self.home / "homebrew/services/PluginLoader"
        loader.parent.mkdir(parents=True)
        loader.touch()
        self.window.render_snapshot(self.scanner.scan())
        self.assertTrue(self.window.install_buttons["Decky Launch Options"].isEnabled())
        plugin = self.home / "homebrew/plugins/Launch Options/plugin.json"
        plugin.parent.mkdir(parents=True)
        plugin.write_text('{"name": "Launch Options"}')
        self.window.render_snapshot(self.scanner.scan())
        self.assertFalse(self.window.install_buttons["Decky Launch Options"].isEnabled())

    def test_installation_runs_on_click_and_refreshes_without_real_install(self):
        class FakeInstaller:
            calls = []
            def install(self, name, progress):
                self.calls.append(name)
                progress("validation simulée")
                return "Installation simulée terminée"
        fake = FakeInstaller()
        self.window.installer = fake
        (self.home / "etc").mkdir()
        (self.home / "etc/os-release").write_text("ID=bazzite")
        self.window.render_snapshot(self.scanner.scan())
        self.assertEqual(fake.calls, [])
        loop = QEventLoop()
        self.window.install_buttons["Heroic"].click()
        self.window.install_worker.finished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        self.app.processEvents()
        if self.window.worker is not None:
            self.window.worker.wait(5000)
        self.app.processEvents()
        self.assertEqual(fake.calls, ["Heroic"])
        self.assertIn("terminée", self.window.install_logs[0].toPlainText())
        self.assertTrue(self.window.refresh_button.isEnabled())
        self.assertEqual(self.window.statusBar().currentMessage(), "Instalación de Heroic completada.")
        self.assertTrue(self.window.install_logs[0].toPlainText().endswith("Instalación de Heroic completada."))
        self.window.render_snapshot(self.scanner.scan())
        self.assertEqual(self.window.statusBar().currentMessage(), "Instalación de Heroic completada.")

    def test_launch_profiles_require_plugin_and_prepare_only_on_click(self):
        self.window.render_snapshot(self.scanner.scan())
        self.assertFalse(self.window.launch_profiles_button.isEnabled())
        manifest = self.home / "homebrew/plugins/dlo/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{"name":"Launch Options"}')
        self.window.render_snapshot(self.scanner.scan())
        self.assertTrue(self.window.launch_profiles_button.isEnabled())
        with patch("playcore.ui.QDialog.exec"), patch("playcore.ui.QApplication.clipboard") as clipboard:
            self.window.show_manual_launch_profiles()
            clipboard.assert_not_called()
        manifest.unlink()
        with patch("playcore.ui.QDialog.exec") as show:
            self.window.show_manual_launch_profiles()
            show.assert_not_called()
        self.assertIn("no detectado", self.window.install_logs[0].toPlainText())

    def test_direct_import_runs_in_worker_and_reports_confirmation_pending(self):
        manifest = self.home / "homebrew/plugins/dlo/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{"name":"Launch Options"}')
        self.window.render_snapshot(self.scanner.scan())
        loop = QEventLoop()
        with patch("playcore.ui.request_import", return_value="Importación pendiente de confirmación") as request:
            self.window.launch_profiles_button.click()
            self.window.launch_profiles_worker.finished.connect(loop.quit)
            QTimer.singleShot(5000, loop.quit)
            loop.exec()
            self.app.processEvents()
            request.assert_called_once_with(self.scanner)
        self.assertIn("pendiente", self.window.install_logs[0].toPlainText())
        self.assertTrue(self.window.launch_profiles_button.isEnabled())

    def test_message_panels_are_small_and_can_be_opened_and_closed(self):
        panel = self.window.message_panels[0]
        self.assertTrue(panel.log.isHidden())
        self.window.install_message("Progreso de prueba")
        panel.toggle.click()
        self.assertFalse(panel.log.isHidden())
        self.assertEqual(panel.log.height(), 90)
        self.assertEqual(panel.toggle.text(), "Ocultar mensajes")
        panel.toggle.click()
        self.assertTrue(panel.log.isHidden())
        self.assertIn("Progreso de prueba", panel.log.toPlainText())

    def test_install_error_is_not_reported_as_completed_after_scan(self):
        class FailedInstaller:
            def install(self, name, progress):
                raise RuntimeError("Error de descarga simulado")
        self.window.installer = FailedInstaller()
        (self.home / "etc").mkdir()
        (self.home / "etc/os-release").write_text("ID=steamos")
        self.window.render_snapshot(self.scanner.scan())
        loop = QEventLoop()
        self.window.install_buttons["Heroic"].click()
        self.window.install_worker.finished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        self.app.processEvents()
        if self.window.worker:
            self.window.worker.wait(5000)
        self.app.processEvents()
        self.assertEqual(self.window.statusBar().currentMessage(), "No se completó la instalación de Heroic.")
        self.assertIn("Error de descarga simulado", self.window.install_logs[0].toPlainText())

    def test_password_action_uses_external_process_without_changing_password(self):
        loop = QEventLoop()
        # Sustituye Konsole/passwd por un proceso inocuo. No se prueba con secretos.
        with patch("playcore.ui.password_command", return_value=("/usr/bin/true", [])):
            self.window.password_button.click()
        self.window.password_process.finished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        self.app.processEvents()
        if self.window.worker is not None:
            self.window.worker.wait(5000)
        self.app.processEvents()
        self.assertIn("terminal ha terminado", self.window.password_note.text())
        self.assertTrue(self.window.password_button.isEnabled())
        self.assertTrue(self.window.refresh_button.isEnabled())

    def test_theme_dependency_choice_and_decky_prerequisites(self):
        (self.home / "etc").mkdir()
        (self.home / "etc/os-release").write_text("ID=steamos")
        self.window.render_snapshot(self.scanner.scan())
        self.assertTrue(self.window.install_buttons["Decky Loader"].isEnabled())
        self.assertFalse(self.window.install_buttons["HLTB"].isEnabled())
        self.assertFalse(self.window.install_buttons["Machine Ready TV"].isEnabled())
        loader = self.home / "homebrew/services/PluginLoader"
        loader.parent.mkdir(parents=True)
        loader.touch()
        plugin = self.home / "homebrew/plugins/css/plugin.json"
        plugin.parent.mkdir(parents=True)
        plugin.write_text('{"name":"CSS Loader"}')
        theme = self.home / "homebrew/themes/theme/theme.json"
        theme.parent.mkdir(parents=True)
        theme.write_text('{"name":"Animated PSP Waves Background"}')
        self.window.render_snapshot(self.scanner.scan())
        self.assertTrue(self.window.install_buttons["HLTB"].isEnabled())
        self.assertTrue(self.window.install_buttons["Machine Ready TV"].isEnabled())
        self.assertFalse(self.window.install_buttons["Tema CSS seleccionado"].isEnabled())
        self.window.css_combo.setCurrentIndex(1)
        self.assertTrue(self.window.install_buttons["Tema CSS seleccionado"].isEnabled())


if __name__ == "__main__":
    unittest.main()
