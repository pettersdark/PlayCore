import os
import tempfile
import unittest
from pathlib import Path
from string import Formatter
from unittest.mock import patch

os.environ.setdefault('QT_QPA_PLATFORM', 'offscreen')
from PySide6.QtCore import QEventLoop, QSettings, QTimer
from PySide6.QtWidgets import QApplication, QMessageBox as NativeMessageBox

from playcore.detection import Scanner
from playcore.i18n import Localizer, translate
from playcore.ui import MainWindow, QMessageBox
from playcore.launch_options import import_script
from playcore.updater import parse_release
from playcore.translations import ENGLISH
from tests.test_updater import release_data
from tests.test_graphical_installer import gui


class LanguageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication.instance() or QApplication([])

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.settings = QSettings(str(self.home / 'preferences.ini'), QSettings.Format.IniFormat)
        self.scanner = Scanner(self.home, self.home, {}, which=lambda _: None)
        self.window = MainWindow(self.scanner, auto_scan=False, settings=self.settings)
        self.addCleanup(self.window.close)

    def english(self):
        self.window.language_combo.setCurrentIndex(self.window.language_combo.findData('en'))

    def test_switch_preserves_section_selections_inventory_and_log(self):
        profile = self.home / 'homebrew/themes/My profile.profile'
        profile.mkdir(parents=True)
        self.window.render_snapshot(self.scanner.scan())
        self.window.profile_combo.setCurrentIndex(1)
        self.window.proton_mode_combo.setCurrentIndex(1)
        self.window.navigation.setCurrentRow(4)
        table = self.window.tables['Proton']
        self.window.install_message('Instalación de Proton-GE completada.')
        self.window.message_panels[0].toggle.setChecked(True)
        self.english()
        self.assertEqual(self.window.navigation.item(0).text(), 'System')
        self.assertEqual(self.window.navigation.item(4).text(), 'Themes')
        self.assertEqual(self.window.navigation.currentRow(), 4)
        self.assertIs(self.window.tables['Proton'], table)
        self.assertEqual(self.window.profile_combo.currentData(), 'My profile.profile')
        self.assertIs(self.window.proton_mode_combo.currentData(), False)
        self.assertIn('My profile.profile', self.window.profile_note.text())
        self.assertEqual(table.horizontalHeaderItem(1).text(), 'Local status')
        self.assertEqual(table.item(0, 1).text(), 'Not detected')
        self.assertIn('Installation of Proton-GE completed.', self.window.install_logs[0].toPlainText())
        self.assertFalse(self.window.message_panels[0].log.isHidden())
        self.assertEqual(self.window.message_panels[0].toggle.text(), 'Hide messages')
        self.window.language_combo.setCurrentIndex(0)
        self.assertEqual(self.window.navigation.item(0).text(), 'Sistema')
        self.assertEqual(table.item(0, 1).text(), 'No detectado')
        self.assertIn('Instalación de Proton-GE completada.', self.window.install_logs[0].toPlainText())
        self.assertEqual(self.window.navigation.currentRow(), 4)

    def test_preference_is_restored_and_invalid_values_fall_back_to_spanish(self):
        self.english()
        settings = QSettings(self.settings.fileName(), QSettings.Format.IniFormat)
        reopened = MainWindow(self.scanner, auto_scan=False, settings=settings)
        self.addCleanup(reopened.close)
        self.assertEqual(reopened.localizer.language, 'en')
        self.assertEqual(reopened.refresh_button.text(), 'Refresh inventory')
        self.assertEqual(reopened.language_combo.currentData(), 'en')
        settings.setValue('ui/language', 'unsupported')
        self.assertEqual(Localizer(settings=settings).language, 'es')

    def test_new_worker_messages_are_translated_after_switch(self):
        self.english()
        self.window.install_message('Instalación solicitada: Proton-GE')
        self.window.install_message('Descargando Proton: 42 MiB…')
        self.assertIn('Downloading Proton: 42 MiB…', self.window.install_logs[0].toPlainText())
        loop = QEventLoop()
        self.window.start_scan()
        worker = self.window.worker
        worker.finished.connect(loop.quit)
        QTimer.singleShot(5000, loop.quit)
        loop.exec()
        self.app.processEvents()
        self.assertIs(self.window.worker, worker)
        self.assertTrue(self.window.statusBar().currentMessage().startswith('Scan completed'))
        self.assertEqual(self.window.tables['Decky'].item(0, 1).text(), 'Not detected')

    def test_release_notes_remain_verbatim_while_update_status_translates(self):
        data = release_data()
        data['body'] = '## Español\nInstalar PlayCore\n## English\nInstall PlayCore'
        release = parse_release(data)
        self.window.show_update_release(release)
        self.english()
        self.assertIn('New version available: 1.4.0', self.window.update_status.text())
        self.assertEqual(self.window.release_notes.toPlainText(), data['body'])
        self.window.show_update_release(None)
        self.assertIn('up to date', self.window.update_status.text())
        self.assertIn('No newer stable release', self.window.release_notes.toPlainText())

    def test_import_guide_translates_but_executable_script_is_unchanged(self):
        manifest = self.home / 'homebrew/plugins/dlo/plugin.json'
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{"name":"Launch Options"}')
        expected = import_script(self.scanner)
        self.english()
        def inspect(dialog):
            from PySide6.QtWidgets import QTextBrowser
            browsers = dialog.findChildren(QTextBrowser)
            preview = next(b for b in browsers if b.property('verbatim'))
            self.assertEqual(preview.toPlainText(), expected)
            self.assertTrue(any('PlayCore prepares the request' in b.toPlainText() for b in browsers))
        with patch('playcore.ui.QDialog.exec', new=inspect):
            self.window.show_manual_launch_profiles()

    def test_confirmation_dialog_uses_english_buttons_and_message(self):
        self.english()
        observed = []
        def inspect():
            dialog = self.app.activeModalWidget()
            observed.append((dialog.text(), dialog.button(NativeMessageBox.StandardButton.Yes).text()))
            dialog.button(NativeMessageBox.StandardButton.No).click()
        QTimer.singleShot(0, inspect)
        result = QMessageBox.question(self.window, 'Actualizar PlayCore',
                                      '¿Descargar e instalar PlayCore 1.4.0?\n\n'
                                      'La aplicación se volverá a abrir al terminar. Tus componentes instalados se conservan.')
        self.assertEqual(result, NativeMessageBox.StandardButton.No)
        self.assertEqual(observed[0][1], 'Yes')
        self.assertTrue(observed[0][0].startswith('Download and install'))

    def test_installer_follows_saved_language_and_translates_progress(self):
        self.english()
        window = gui.InstallerWindow(self.home, self.home / 'destination', settings=self.settings)
        self.addCleanup(window.close)
        self.assertEqual(window.install_button.text(), 'Install PlayCore')
        self.assertEqual(window.language_combo.currentData(), 'en')
        window.append_output('Comprobando la integridad del paquete…')
        self.assertIn('Verifying package integrity', window.log.toPlainText())
        window.language_combo.setCurrentIndex(0)
        self.assertEqual(window.install_button.text(), 'Instalar PlayCore')
        self.assertIn('Comprobando la integridad', window.log.toPlainText())

    def test_messages_keep_user_names_paths_and_command_output_intact(self):
        self.assertEqual(translate('Dependencias CSS detectado', 'en'), 'CSS dependencies detected')
        self.assertEqual(translate('Usuario: Sistema · Contraseña: Configurada', 'en'), 'User: Sistema · Password: Set')
        path = '/home/gamer/Temas/My profile.profile'
        self.assertEqual(translate(f'Destino: {path}', 'en'), f'Destination: {path}')
        self.assertEqual(translate('PROTON_USE_OPTISCALER=1 %command%', 'en'), 'PROTON_USE_OPTISCALER=1 %command%')
        self.assertEqual(translate('pip: Successfully installed PySide6', 'en'), 'pip: Successfully installed PySide6')
        self.assertEqual(translate('Error: El fichero SHA-256 no es válido.', 'en'), 'Error: The SHA-256 file is invalid.')

    def test_language_switch_keeps_active_update_state(self):
        process = self.window.update_process
        self.window.update_active = True
        try:
            self.window.update_progress.setValue(43)
            self.window.update_status.setText('Descargando el instalador y comprobando su integridad…')
            self.window.refresh_button.setEnabled(False)
            self.window.update_install_buttons()
            self.english()
            self.assertIs(self.window.update_process, process)
            self.assertTrue(self.window.update_active)
            self.assertEqual(self.window.update_progress.value(), 43)
            self.assertFalse(self.window.refresh_button.isEnabled())
            self.assertFalse(self.window.apply_update_button.isEnabled())
            self.assertTrue(self.window.update_status.text().startswith('Downloading the installer'))
        finally:
            self.window.update_active = False

    def test_catalog_preserves_every_runtime_field(self):
        formatter = Formatter()
        for source, target in ENGLISH.items():
            if '{0}' in source:
                original = sorted(field for _, field, _, _ in formatter.parse(source) if field is not None)
                translated = sorted(field for _, field, _, _ in formatter.parse(target) if field is not None)
                self.assertEqual(original, translated, source)

    def test_installer_log_keeps_its_block_limit_in_both_languages(self):
        window = gui.InstallerWindow(self.home, settings=self.settings)
        self.addCleanup(window.close)
        window.log.setMaximumBlockCount(3)
        for index in range(5):
            window.append_output(f'Instalación solicitada: Tool{index}')
        self.assertNotIn('Tool0', window.log.sourcePlainText())
        window.language_combo.setCurrentIndex(1)
        self.assertEqual(window.log.toPlainText().splitlines(), [
            'Installation requested: Tool2', 'Installation requested: Tool3', 'Installation requested: Tool4'])
