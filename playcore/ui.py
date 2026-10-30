"""Widgets Qt nativos: se respeta la paleta, tipografía y estilo del escritorio."""
from PySide6.QtCore import QProcess, QThread, QTimer, QUrl, Signal, Qt
from PySide6.QtGui import QDesktopServices, QIcon
from PySide6.QtWidgets import (
    QApplication, QComboBox, QDialog, QFormLayout, QGridLayout, QGroupBox, QHBoxLayout, QHeaderView, QLabel,
    QListWidget, QListWidgetItem, QMainWindow, QPushButton, QScrollArea,
    QSplitter, QStackedWidget, QTableWidget, QTableWidgetItem, QTextBrowser, QToolButton,
    QVBoxLayout, QWidget, QProgressBar, QMessageBox,
)

from .catalog import CSS_DEPENDENCIES, MACHINE_READY_URL, PLUGINS, PROFILE_STEPS
from .detection import Scanner
from .installers import Installer, steam_installations
from .accounts import password_command
from .launch_options import GUIDE as LAUNCH_OPTIONS_GUIDE, WARNING as LAUNCH_OPTIONS_WARNING, import_script
from .steam_bridge import request_import
from . import __version__
from .updater import Updater, RELEASES_URL, installation_destination


class UpdateWorker(QThread):
    ready = Signal(object)
    failed = Signal(str)
    progress = Signal(int)

    def __init__(self, updater, release=None, parent=None):
        super().__init__(parent)
        self.updater, self.release = updater, release

    def run(self):
        try:
            result = (self.updater.download(self.release, self.progress.emit)
                      if self.release is not None else self.updater.check())
            self.ready.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class MessagePanel(QWidget):
    """Resumen visible y registro pequeño que el usuario puede desplegar."""
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.summary = paragraph("No se ha iniciado ninguna instalación.")
        layout.addWidget(self.summary)
        self.toggle = QToolButton()
        self.toggle.setText("Mostrar mensajes")
        self.toggle.setCheckable(True)
        self.toggle.setArrowType(Qt.ArrowType.RightArrow)
        self.toggle.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        layout.addWidget(self.toggle)
        self.log = QTextBrowser()
        self.log.setAccessibleName("Mensajes de instalación")
        self.log.setFixedHeight(90)
        self.log.setPlainText("No se ha iniciado ninguna instalación.")
        self.log.hide()
        layout.addWidget(self.log)
        self.toggle.toggled.connect(self.set_expanded)

    def set_expanded(self, expanded):
        self.log.setVisible(expanded)
        self.toggle.setText("Ocultar mensajes" if expanded else "Mostrar mensajes")
        self.toggle.setArrowType(Qt.ArrowType.DownArrow if expanded else Qt.ArrowType.RightArrow)


class InstallWorker(QThread):
    progress = Signal(str)
    succeeded = Signal(str)
    failed = Signal(str)

    def __init__(self, installer, name, parent=None, steam_target=None, proton_latest=False):
        super().__init__(parent)
        self.installer, self.name = installer, name
        self.steam_target = steam_target
        self.proton_latest = proton_latest

    def run(self):
        try:
            if self.steam_target is None:
                result = self.installer.install(self.name, self.progress.emit)
            else:
                result = self.installer.install(self.name, self.progress.emit, self.steam_target,
                                                proton_latest=self.proton_latest)
            self.succeeded.emit(result)
        except Exception as exc:
            self.failed.emit(str(exc))


class ScanWorker(QThread):
    ready = Signal(object)
    failed = Signal(str)

    def __init__(self, scanner, parent=None):
        super().__init__(parent)
        self.scanner = scanner

    def run(self):
        try:
            self.ready.emit(self.scanner.scan())
        except Exception as exc:
            self.failed.emit(f"No se pudo completar la detección: {exc}")


class LaunchProfilesWorker(QThread):
    result = Signal(str)

    def __init__(self, scanner, parent=None):
        super().__init__(parent)
        self.scanner = scanner

    def run(self):
        try:
            self.result.emit(request_import(self.scanner))
        except Exception as exc:
            self.result.emit(str(exc))


class InventoryTable(QTableWidget):
    def __init__(self):
        super().__init__(0, 3)
        self.setHorizontalHeaderLabels(["Componente", "Estado local", "Evidencia"])
        self.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.setWordWrap(False)
        self.verticalHeader().hide()
        self.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        self.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.setMinimumHeight(150)

    def populate(self, findings):
        self.setRowCount(len(findings))
        for row, finding in enumerate(findings):
            for column, value in enumerate((finding.name, finding.status, finding.evidence or "—")):
                item = QTableWidgetItem(value)
                item.setToolTip(value)
                self.setItem(row, column, item)


def paragraph(text):
    label = QLabel(text)
    label.setTextFormat(Qt.TextFormat.PlainText)
    label.setWordWrap(True)
    label.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
    return label


class MainWindow(QMainWindow):
    SECTIONS = (
        ("Sistema", "computer"), ("Aplicaciones", "applications-other"),
        ("Proton", "applications-games"), ("Decky", "preferences-plugin"),
        ("Temas", "preferences-desktop-theme"), ("Mantenimiento", "tools-check-spelling"),
        ("Actualizaciones", "system-software-update"),
    )

    def __init__(self, scanner=None, auto_scan=True, installer=None):
        super().__init__()
        self.scanner = scanner or Scanner()
        self.worker = None
        self.installer = installer or Installer()
        self.install_worker = None
        self.launch_profiles_worker = None
        self.updater = Updater()
        self.update_worker = None
        self.available_release = None
        self.update_active = False
        self.update_process = QProcess(self)
        self.update_process.setProcessChannelMode(QProcess.ProcessChannelMode.MergedChannels)
        self.update_process.readyReadStandardOutput.connect(self.read_update_output)
        self.update_process.finished.connect(self.update_process_finished)
        self.update_process.errorOccurred.connect(self.update_process_error)
        self.install_buttons = {}
        self.install_logs = []
        self.message_panels = []
        self.operation_summary = ""
        self.password_process = QProcess(self)
        self.password_process.finished.connect(self.password_finished)
        self.password_process.errorOccurred.connect(self.password_error)
        self.snapshot = None
        self.setWindowTitle("PlayCore")
        self.setWindowIcon(QIcon.fromTheme("applications-games"))
        self.resize(1100, 760)
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(20, 16, 20, 16)
        header = QHBoxLayout()
        title = QLabel("PlayCore")
        font = title.font()
        font.setPointSize(font.pointSize() + 8)
        font.setBold(True)
        title.setFont(font)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(QLabel(f"Versión {__version__} · Instalación bajo demanda"))
        self.updates_shortcut = QPushButton("Buscar actualizaciones")
        self.updates_shortcut.clicked.connect(self.open_updates)
        header.addWidget(self.updates_shortcut)
        self.refresh_button = QPushButton(QIcon.fromTheme("view-refresh"), "Actualizar detección")
        self.refresh_button.clicked.connect(self.start_scan)
        header.addWidget(self.refresh_button)
        layout.addLayout(header)
        layout.addWidget(paragraph("Tu equipo de juego, de un vistazo. Consulta el sistema, las aplicaciones y los complementos locales."))
        splitter = QSplitter()
        self.navigation = QListWidget()
        self.navigation.setAccessibleName("Secciones de PlayCore")
        self.navigation.setMinimumWidth(155)
        self.pages = QStackedWidget()
        self.tables = {}
        self.system_labels = {}
        for name, icon in self.SECTIONS:
            self.navigation.addItem(QListWidgetItem(QIcon.fromTheme(icon), name))
            page = QWidget()
            page_layout = QVBoxLayout(page)
            heading = QLabel(name)
            heading_font = heading.font()
            heading_font.setPointSize(heading_font.pointSize() + 4)
            heading_font.setBold(True)
            heading.setFont(heading_font)
            page_layout.addWidget(heading)
            self.build_section(name, page_layout)
            scroll = QScrollArea()
            scroll.setWidgetResizable(True)
            scroll.setWidget(page)
            self.pages.addWidget(scroll)
        splitter.addWidget(self.navigation)
        splitter.addWidget(self.pages)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([175, 900])
        layout.addWidget(splitter, 1)
        layout.addWidget(paragraph("Las instalaciones comienzan al pulsar Instalar. Los perfiles se aplican manualmente en CSS Loader; no se modifican las opciones de lanzamiento de los juegos."))
        self.setCentralWidget(central)
        self.navigation.currentRowChanged.connect(self.pages.setCurrentIndex)
        self.navigation.setCurrentRow(0)
        self.statusBar().showMessage("Listo para detectar")
        if auto_scan:
            self.start_scan()
            QTimer.singleShot(1500, self.check_updates)

    def build_section(self, name, layout):
        if name == "Actualizaciones":
            group = QGroupBox("Mantén PlayCore al día")
            content = QVBoxLayout(group)
            content.addWidget(paragraph(f"Versión instalada: {__version__}"))
            content.addWidget(paragraph("Busca nuevas versiones estables en el repositorio oficial de GitHub. Tú decides cuándo instalarlas."))
            self.update_status = paragraph("Todavía no se han buscado actualizaciones.")
            content.addWidget(self.update_status)
            self.update_progress = QProgressBar()
            self.update_progress.setRange(0, 100)
            self.update_progress.hide()
            content.addWidget(self.update_progress)
            buttons = QHBoxLayout()
            self.check_updates_button = QPushButton("Buscar actualizaciones")
            self.check_updates_button.clicked.connect(self.check_updates)
            buttons.addWidget(self.check_updates_button)
            self.apply_update_button = QPushButton("Descargar e instalar")
            self.apply_update_button.setEnabled(False)
            self.apply_update_button.clicked.connect(self.apply_update)
            buttons.addWidget(self.apply_update_button)
            releases_button = QPushButton("Ver en GitHub")
            releases_button.clicked.connect(lambda: QDesktopServices.openUrl(QUrl(
                self.available_release.url if self.available_release else RELEASES_URL)))
            buttons.addWidget(releases_button)
            content.addLayout(buttons)
            layout.addWidget(group)
            layout.addWidget(paragraph("La descarga se comprueba con SHA-256. La aplicación se volverá a abrir al terminar. Se conservan tus componentes y la versión anterior."))
            self.update_install_hint = paragraph("Esta copia se ejecuta desde el código fuente. Instala la nueva versión con el instalador para activar las actualizaciones desde la app.")
            self.update_install_hint.setVisible(installation_destination() is None)
            layout.addWidget(self.update_install_hint)
            notes_group = QGroupBox("Novedades de la versión")
            notes_layout = QVBoxLayout(notes_group)
            self.release_notes = QTextBrowser()
            self.release_notes.setOpenLinks(False)
            self.release_notes.setPlainText("Aquí aparecerán las novedades cuando haya una actualización disponible.")
            notes_layout.addWidget(self.release_notes)
            layout.addWidget(notes_group, 1)
            self.update_log = QTextBrowser()
            self.update_log.setMaximumHeight(90)
            self.update_log.hide()
            layout.addWidget(self.update_log)
        elif name == "Sistema":
            group = QGroupBox("Información del equipo")
            form = QFormLayout(group)
            for key in ("Distribución", "Versión", "Hostname", "Kernel", "Escritorio", "Sesión"):
                value = paragraph("Pendiente de detección")
                self.system_labels[key] = value
                form.addRow(key, value)
            layout.addWidget(group)
            self.compatibility = paragraph("Detectando SteamOS o Bazzite…")
            layout.addWidget(self.compatibility)
            account = QGroupBox("Contraseña del usuario")
            account_layout = QVBoxLayout(account)
            self.account_label = paragraph("Consultando el estado de la cuenta…")
            account_layout.addWidget(self.account_label)
            account_layout.addWidget(paragraph("Para autorizar instalaciones de Decky necesitas la contraseña de tu usuario. Puedes establecerla o cambiarla con passwd en Konsole. PlayCore no recibe ni guarda tu contraseña. Los Flatpaks y Proton en tu carpeta de usuario no requieren permisos de administrador."))
            self.password_button = QPushButton(QIcon.fromTheme("dialog-password"), "Establecer o cambiar contraseña…")
            self.password_button.clicked.connect(self.change_password)
            account_layout.addWidget(self.password_button)
            self.password_note = paragraph("En la terminal, sigue los mensajes de passwd. Al escribir la contraseña no aparecen caracteres. Si te pide la contraseña actual y nunca has definido una, prueba a dejarla vacía pulsando Intro.")
            account_layout.addWidget(self.password_note)
            layout.addWidget(account)
            layout.addStretch()
        elif name in {"Aplicaciones", "Proton", "Decky"}:
            descriptions = {
                "Aplicaciones": "Heroic y ProtonPlus: consulta Flatpak de usuario y sistema, además de ejecutables disponibles en PATH.",
                "Proton": "Proton-CachyOS y Proton-GE: detecta herramientas instaladas en Steam nativo y Flatpak. La selección para cada juego se realiza en Steam.",
                "Decky": "Decky Loader y los cuatro plugins solicitados. Se leen los manifiestos locales de ~/homebrew/plugins; no se comprueba si el servicio está ejecutándose.",
            }
            layout.addWidget(paragraph(descriptions[name]))
            table = InventoryTable()
            self.tables[name] = table
            layout.addWidget(table, 1)
            if name == "Aplicaciones":
                layout.addWidget(paragraph("Instalación Flatpak para tu usuario desde Flathub. Se descargarán la aplicación y sus dependencias."))
                for app_name in ("Heroic", "ProtonPlus"):
                    self.add_install_button(layout, app_name)
                self.add_install_log(layout)
            elif name == "Decky":
                layout.addWidget(paragraph("Instala primero Decky Loader y después los plugins. Se descargan las versiones estables oficiales con SHA-256. Cada plugin nuevo pide permisos de administrador y reinicia Decky. No se sobrescriben componentes existentes."))
                grid = QGridLayout()
                for index, component in enumerate(("Decky Loader", *PLUGINS)):
                    button = self.add_install_button(None, component)
                    grid.addWidget(button, index // 2, index % 2)
                layout.addLayout(grid)
                layout.addWidget(paragraph("Instalar Decky Loader ejecuta su instalador oficial: crea el servicio y habilita la depuración remota de Steam; en Bazzite también puede ajustar el contexto SELinux. Configura tu contraseña desde Sistema antes de autorizarlo."))
                self.launch_profiles_button = QPushButton("Instalar perfiles FSR/OptiScaler")
                self.launch_profiles_button.setEnabled(False)
                self.launch_profiles_button.clicked.connect(self.prepare_launch_profiles)
                layout.addWidget(self.launch_profiles_button)
                manual_profiles = QPushButton("Ver procedimiento manual de importación…")
                manual_profiles.clicked.connect(self.show_manual_launch_profiles)
                layout.addWidget(manual_profiles)
                layout.addWidget(paragraph(LAUNCH_OPTIONS_WARNING))
                self.add_install_log(layout)
            elif name == "Proton":
                layout.addWidget(paragraph("Instala Proton-CachyOS SLR o Proton-GE. Latest mantiene un nombre fijo en Steam y los datos de instalación para que ProtonPlus lo reconozca y lo actualice. Reinicia Steam después de instalarlo y selecciónalo en Compatibilidad."))
                self.proton_mode_combo = QComboBox()
                self.proton_mode_combo.setAccessibleName("Modalidad de instalación de Proton")
                self.proton_mode_combo.addItem("Latest · para actualizar con ProtonPlus", True)
                self.proton_mode_combo.addItem("Versión independiente · última estable", False)
                self.proton_mode_combo.currentIndexChanged.connect(self.update_install_buttons)
                layout.addWidget(self.proton_mode_combo)
                self.steam_combo = QComboBox()
                self.steam_combo.setAccessibleName("Instalación de Steam para Proton")
                self.steam_combo.currentIndexChanged.connect(self.update_install_buttons)
                layout.addWidget(self.steam_combo)
                self.add_install_button(layout, "Proton-CachyOS")
                self.add_install_button(layout, "Proton-GE")
                self.add_install_log(layout)
        elif name == "Temas":
            layout.addWidget(paragraph("Machine Ready TV · Tema base y 14 dependencias CSS. Los manifiestos indican presencia local, no activación ni compatibilidad de versión."))
            table = InventoryTable()
            self.tables[name] = table
            table.setMinimumHeight(240)
            layout.addWidget(table, 1)
            self.add_install_button(layout, "Machine Ready TV")
            self.add_install_button(layout, "Dependencias CSS")
            layout.addWidget(paragraph("Machine Ready TV instala los temas y perfiles del repositorio y las 14 dependencias. Conserva todas las carpetas existentes. También puedes instalar una dependencia concreta:"))
            self.css_combo = QComboBox()
            self.css_combo.addItems(CSS_DEPENDENCIES)
            self.css_combo.currentIndexChanged.connect(self.update_install_buttons)
            layout.addWidget(self.css_combo)
            self.add_install_button(layout, "Tema CSS seleccionado")
            self.add_install_log(layout)
            self.profile_combo = QComboBox()
            self.profile_combo.setAccessibleName("Perfil local para consultar; no se aplica")
            self.profile_combo.addItem("Sin selección · elige el perfil manualmente en CSS Loader", None)
            layout.addWidget(self.profile_combo)
            self.profile_note = paragraph("No se ha elegido ningún perfil. PlayCore no cambia la selección de CSS Loader.")
            layout.addWidget(self.profile_note)
            self.profile_combo.currentIndexChanged.connect(self.profile_changed)
            guide = QGroupBox("Configuración manual en CSS Loader")
            guide_layout = QVBoxLayout(guide)
            for index, step in enumerate(PROFILE_STEPS, 1):
                guide_layout.addWidget(paragraph(f"{index}. {step}"))
            # La dirección es seleccionable, sin abrir navegadores desde la aplicación.
            guide_layout.addWidget(paragraph(f"Fuente y descarga manual: {MACHINE_READY_URL}"))
            layout.addWidget(guide)
        else:
            layout.addWidget(paragraph("Diagnóstico de solo lectura. Actualizar detección vuelve a consultar el inventario; no borra cachés, actualiza paquetes ni reinicia servicios."))
            self.free_space = paragraph("Espacio libre: pendiente")
            layout.addWidget(self.free_space)
            self.diagnostics = QTextBrowser()
            self.diagnostics.setAccessibleName("Avisos de diagnóstico")
            layout.addWidget(self.diagnostics, 1)

    def open_updates(self):
        self.navigation.setCurrentRow(len(self.SECTIONS) - 1)
        if self.available_release is None:
            self.check_updates()

    def update_update_buttons(self):
        if not hasattr(self, "apply_update_button"):
            return
        querying = self.update_worker is not None and self.update_worker.isRunning()
        busy = (self.installation_busy()
                or (self.worker is not None and self.worker.isRunning())
                or self.password_process.state() != QProcess.ProcessState.NotRunning)
        self.check_updates_button.setEnabled(not querying and not self.update_active)
        self.updates_shortcut.setEnabled(not querying and not self.update_active)
        self.apply_update_button.setEnabled(
            self.available_release is not None and installation_destination() is not None
            and not querying and not busy)

    def check_updates(self):
        if self.update_active or (self.update_worker is not None and self.update_worker.isRunning()):
            return
        self.available_release = None
        self.apply_update_button.setText("Descargar e instalar")
        self.updates_shortcut.setText("Buscar actualizaciones")
        self.release_notes.setPlainText("Consultando las novedades…")
        self.update_status.setText("Buscando versiones estables en GitHub…")
        self.update_worker = UpdateWorker(self.updater, parent=self)
        self.update_worker.ready.connect(self.show_update_release)
        self.update_worker.failed.connect(self.update_failed)
        self.update_worker.finished.connect(self.update_update_buttons)
        self.update_worker.start()
        self.update_update_buttons()

    def show_update_release(self, release):
        self.available_release = release
        if release is None:
            self.update_status.setText(f"PlayCore está al día. Tienes la versión {__version__}.")
            self.release_notes.setPlainText("No hay una versión estable más reciente disponible.")
        else:
            self.update_status.setText(f"Nueva versión disponible: {release.version} · {release.size / 1024**2:.1f} MiB")
            self.release_notes.setPlainText(release.notes)
            self.apply_update_button.setText(f"Actualizar a {release.version}")
            self.updates_shortcut.setText(f"Nueva versión: {release.version}")
        self.update_update_buttons()

    def apply_update(self):
        self.update_update_buttons()
        if not self.apply_update_button.isEnabled():
            return
        release = self.available_release
        answer = QMessageBox.question(self, "Actualizar PlayCore",
            f"¿Descargar e instalar PlayCore {release.version}?\n\n"
            "La aplicación se volverá a abrir al terminar. Tus componentes instalados se conservan.",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
            QMessageBox.StandardButton.No)
        if answer != QMessageBox.StandardButton.Yes:
            return
        self.update_active = True
        self.update_log.clear()
        self.update_log.hide()
        self.update_progress.setValue(0)
        self.update_progress.show()
        self.update_status.setText("Descargando el instalador y comprobando su integridad…")
        self.update_worker = UpdateWorker(self.updater, release, self)
        self.update_worker.progress.connect(self.update_progress.setValue)
        self.update_worker.ready.connect(self.start_update_installer)
        self.update_worker.failed.connect(self.update_failed)
        self.update_worker.finished.connect(self.update_install_buttons)
        self.update_worker.start()
        self.refresh_button.setEnabled(False)
        self.update_install_buttons()

    def start_update_installer(self, path):
        destination = installation_destination()
        if destination is None:
            self.update_failed("No se pudo identificar la instalación actual.")
            return
        self.update_status.setText("Descarga verificada. Instalando PlayCore; se abrirá al terminar…")
        self.update_progress.setRange(0, 0)
        self.update_process.start("/bin/sh", [str(path), "--update", "--dest", str(destination)])

    def read_update_output(self):
        text = bytes(self.update_process.readAllStandardOutput()).decode("utf-8", errors="replace")
        if text.strip():
            self.update_log.setPlainText(self.update_log.toPlainText() + "\n" + text.rstrip())

    def update_process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.update_failed("No se pudo iniciar el instalador: " + self.update_process.errorString())

    def update_process_finished(self, code, exit_status):
        self.read_update_output()
        self.update_active = False
        if code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            self.close()
        else:
            self.update_failed("La actualización no se completó. Puedes seguir usando esta versión y volver a intentarlo.")

    def update_failed(self, message):
        self.update_active = False
        self.update_progress.setRange(0, 100)
        self.update_progress.hide()
        self.update_status.setText(message)
        if not self.update_log.document().isEmpty():
            self.update_log.show()
        if self.available_release is None:
            self.release_notes.setPlainText("No se han podido consultar las novedades. Puedes volver a buscar actualizaciones.")
        self.scan_finished()

    def add_install_button(self, layout, name):
        button = QPushButton(QIcon.fromTheme("list-add"), f"Instalar {name}")
        button.setEnabled(False)
        button.clicked.connect(lambda checked=False, target=name: self.start_install(target))
        self.install_buttons[name] = button
        if layout is not None:
            layout.addWidget(button)
        return button

    def add_install_log(self, layout):
        panel = MessagePanel()
        self.message_panels.append(panel)
        self.install_logs.append(panel.log)
        layout.addWidget(panel)

    def installation_busy(self):
        return (self.update_active or (self.install_worker is not None and self.install_worker.isRunning())
                or (self.launch_profiles_worker is not None and self.launch_profiles_worker.isRunning()))

    def prepare_launch_profiles(self):
        if self.installation_busy():
            return
        self.install_message("Conectando con Steam para solicitar la importación de perfiles…")
        self.launch_profiles_worker = LaunchProfilesWorker(self.scanner, self)
        self.launch_profiles_worker.result.connect(self.install_message)
        self.launch_profiles_worker.finished.connect(self.scan_finished)
        self.refresh_button.setEnabled(False)
        self.launch_profiles_worker.start()
        self.update_install_buttons()

    def show_manual_launch_profiles(self):
        try:
            script = import_script(self.scanner)
        except (OSError, RuntimeError) as exc:
            self.install_message(str(exc))
            return
        dialog = QDialog(self)
        dialog.setWindowTitle("Perfiles preparados · importación pendiente en Decky")
        dialog.resize(800, 650)
        layout = QVBoxLayout(dialog)
        layout.addWidget(paragraph(LAUNCH_OPTIONS_WARNING))
        guide = QTextBrowser()
        guide.setPlainText(LAUNCH_OPTIONS_GUIDE)
        layout.addWidget(guide, 2)
        preview = QTextBrowser()
        preview.setAccessibleName("Script de importación para la consola de Steam")
        preview.setPlainText(script)
        layout.addWidget(preview, 1)
        copy = QPushButton("Copiar script de importación")
        def copy_script():
            QApplication.clipboard().setText(script)
            copy.setText("Script copiado · ejecuta y confirma en Steam")
        copy.clicked.connect(copy_script)
        layout.addWidget(copy)
        close = QPushButton("Cerrar")
        close.clicked.connect(dialog.accept)
        layout.addWidget(close)
        dialog.exec()

    def update_install_buttons(self):
        self.update_update_buttons()
        statuses = {}
        if self.snapshot:
            statuses = {f.name: f.status for f in (*self.snapshot.applications, *self.snapshot.decky,
                                                  *self.snapshot.themes, *self.snapshot.proton)}
        scanning = self.worker is not None and self.worker.isRunning()
        password_busy = self.password_process.state() != QProcess.ProcessState.NotRunning
        if hasattr(self, "launch_profiles_button"):
            self.launch_profiles_button.setEnabled(
                statuses.get("Decky Launch Options") == "Detectado"
                and not scanning and not self.installation_busy() and not password_busy)
            self.launch_profiles_button.setToolTip(
                "Solicita la importación directamente en Steam; revisa y confirma en Decky.")
        for name, button in self.install_buttons.items():
            component = self.css_combo.currentText() if name == "Tema CSS seleccionado" else name
            installed = statuses.get(component) == "Detectado"
            if name == "Dependencias CSS":
                installed = all(statuses.get(dep) == "Detectado" for dep in CSS_DEPENDENCIES)
            supported = self.snapshot is not None and self.snapshot.system.supported
            available = name not in PLUGINS or statuses.get("Decky Loader") == "Detectado"
            if name in ("Machine Ready TV", "Dependencias CSS", "Tema CSS seleccionado"):
                available = statuses.get("CSS Loader") == "Detectado" and statuses.get("Decky Loader") == "Detectado"
            if name in ("Proton-CachyOS", "Proton-GE"):
                available = self.steam_combo.currentData() is not None
            button.setText(f"{component} detectado" if installed else f"Instalar {component}")
            if name in ("Proton-CachyOS", "Proton-GE"):
                # Detectar una versión local no indica si coincide con Latest.
                installed = False
                mode = "Latest" if self.proton_mode_combo.currentData() else "última estable"
                button.setText(f"Instalar {component} · {mode}")
            if name == "Machine Ready TV":
                button.setText("Instalar lo que falta de Machine Ready TV y sus dependencias")
            button.setEnabled(supported and available and not installed
                              and not self.installation_busy() and not scanning and not password_busy)
            button.setToolTip("Completa primero los requisitos: Decky / CSS Loader o Steam de destino" if not available else
                              "Disponible en SteamOS y Bazzite; requiere conexión a Internet")
        self.password_button.setEnabled(not self.installation_busy() and not password_busy)

    def install_message(self, message):
        for log in self.install_logs:
            # setPlainText evita interpretar como HTML la salida externa.
            log.setPlainText(log.toPlainText() + "\n" + message)
            bar = log.verticalScrollBar()
            bar.setValue(bar.maximum())
        self.statusBar().showMessage(message.splitlines()[-1] if message else "")
        for panel in self.message_panels:
            panel.summary.setText(message.splitlines()[-1] if message else "")

    def installation_succeeded(self, details):
        self.install_message(details)
        self.operation_summary = f"Instalación de {self.install_worker.name} completada."
        self.install_message(self.operation_summary)

    def installation_failed(self, error):
        self.operation_summary = f"No se completó la instalación de {self.install_worker.name}."
        self.install_message(f"Error: {error}")
        self.install_message(self.operation_summary)

    def start_install(self, name):
        button = self.install_buttons.get(name)
        if button is None or not button.isEnabled():
            return
        self.operation_summary = ""
        for log in self.install_logs:
            log.setPlainText(f"Instalación solicitada: {name}")
        target = self.steam_combo.currentData() if name in ("Proton-CachyOS", "Proton-GE") else None
        if name == "Tema CSS seleccionado":
            name = self.css_combo.currentText()
        latest = bool(self.proton_mode_combo.currentData()) if target is not None else False
        self.install_worker = InstallWorker(self.installer, name, self, target, latest)
        self.install_worker.progress.connect(self.install_message)
        self.install_worker.succeeded.connect(self.installation_succeeded)
        self.install_worker.failed.connect(self.installation_failed)
        self.install_worker.finished.connect(self.install_finished)
        self.install_worker.start()
        self.refresh_button.setEnabled(False)
        for item in self.install_buttons.values():
            item.setEnabled(False)
        self.password_button.setEnabled(False)

    def change_password(self):
        if self.installation_busy() or self.password_process.state() != QProcess.ProcessState.NotRunning:
            return
        try:
            program, arguments = password_command()
        except RuntimeError as exc:
            self.password_note.setText(str(exc))
            return
        self.password_process.setProgram(program)
        self.password_process.setArguments(arguments)
        self.password_process.start()
        self.password_note.setText("Konsole abrirá passwd para tu usuario. Introduce allí la contraseña siguiendo sus mensajes; PlayCore no registra la conversación. Cierra Konsole al terminar y se actualizará el estado.")
        self.update_install_buttons()

    def password_finished(self, *_):
        self.password_note.setText("La terminal ha terminado. Revisa el estado de la contraseña; puedes volver a abrirla si no completaste el cambio.")
        self.start_scan()

    def password_error(self, *_):
        self.password_note.setText("No se pudo abrir o mantener Konsole: " + self.password_process.errorString())
        self.update_install_buttons()

    def install_finished(self):
        self.start_scan()

    def profile_changed(self):
        selected = self.profile_combo.currentData()
        self.profile_note.setText(
            f"Perfil consultado: {selected}. Para activarlo, selecciónalo manualmente en CSS Loader después de Nav Patch y Refresh."
            if selected else "No se ha elegido ningún perfil. PlayCore no cambia la selección de CSS Loader."
        )

    def start_scan(self):
        if self.installation_busy():
            return
        if self.worker is not None and self.worker.isRunning():
            return
        self.refresh_button.setEnabled(False)
        self.statusBar().showMessage(self.operation_summary or "Leyendo inventario local…")
        self.worker = ScanWorker(self.scanner, self)
        self.worker.ready.connect(self.render_snapshot)
        self.worker.failed.connect(self.scan_failed)
        self.worker.finished.connect(self.scan_finished)
        self.worker.start()
        self.update_install_buttons()

    def scan_finished(self):
        self.refresh_button.setEnabled(not self.installation_busy())
        self.update_install_buttons()

    def scan_failed(self, message):
        self.snapshot = None
        self.statusBar().showMessage(self.operation_summary or message)
        self.diagnostics.setPlainText(message)

    def render_snapshot(self, snapshot):
        self.snapshot = snapshot
        system = snapshot.system
        values = (system.pretty_name, system.version, system.hostname, system.kernel,
                  system.desktop, system.session)
        for label, value in zip(self.system_labels.values(), values):
            label.setText(value)
        self.compatibility.setText("Sistema objetivo detectado: SteamOS / Bazzite."
                                   if system.supported else "Distribución fuera de los sistemas objetivo. El inventario sigue disponible; no se ejecutan cambios.")
        self.account_label.setText(f"Usuario: {snapshot.username} · Contraseña: {snapshot.password_status}")
        previous_steam = self.steam_combo.currentData()
        self.steam_combo.blockSignals(True)
        self.steam_combo.clear()
        targets = steam_installations(self.scanner.home, self.scanner.env)
        self.steam_combo.addItem("Selecciona Steam de destino…", None)
        for target in targets:
            self.steam_combo.addItem(str(target), str(target))
        index = self.steam_combo.findData(previous_steam) if previous_steam else (1 if len(targets) == 1 else 0)
        self.steam_combo.setCurrentIndex(max(0, index))
        self.steam_combo.blockSignals(False)
        for name, findings in (("Aplicaciones", snapshot.applications), ("Proton", snapshot.proton),
                               ("Decky", snapshot.decky), ("Temas", snapshot.themes)):
            self.tables[name].populate(findings)
        selected = self.profile_combo.currentData()
        self.profile_combo.blockSignals(True)
        self.profile_combo.clear()
        self.profile_combo.addItem("Sin selección · elige el perfil manualmente en CSS Loader", None)
        for profile in snapshot.profiles:
            self.profile_combo.addItem(profile, profile)
        index = self.profile_combo.findData(selected) if selected else 0
        self.profile_combo.setCurrentIndex(max(0, index))
        self.profile_combo.blockSignals(False)
        self.profile_changed()
        self.free_space.setText(f"Espacio libre en el volumen del usuario: {snapshot.free_bytes / 1024**3:.1f} GiB"
                                if snapshot.free_bytes >= 0 else "Espacio libre: desconocido")
        self.diagnostics.setPlainText("\n".join(snapshot.warnings) or "Detección completada sin errores de lectura.\nNo detectado significa que no se encontró en las rutas comprobadas.")
        self.statusBar().showMessage(self.operation_summary or f"Detección completada · {len(snapshot.warnings)} avisos")
        self.update_install_buttons()

    def closeEvent(self, event):
        if self.update_worker is not None and self.update_worker.isRunning():
            self.statusBar().showMessage("Espera a que termine la consulta o descarga de la actualización…")
            event.ignore()
            return
        if self.password_process.state() != QProcess.ProcessState.NotRunning:
            self.statusBar().showMessage("Termina y cierra la terminal de contraseña antes de cerrar PlayCore.")
            event.ignore()
            return
        if self.installation_busy():
            self.statusBar().showMessage("Espera a que termine la instalación antes de cerrar…")
            event.ignore()
            return
        if self.worker is not None and self.worker.isRunning():
            self.statusBar().showMessage("Espera a que termine la lectura antes de cerrar…")
            event.ignore()
            return
        self.updater.cleanup()
        event.accept()
