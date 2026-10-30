"""Instalador gráfico: no inicia instalaciones antes de pulsar Instalar."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

from PySide6.QtCore import QProcess, Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import (
    QApplication, QDialog, QHBoxLayout, QLabel, QMessageBox, QPlainTextEdit,
    QProgressBar, QPushButton, QToolButton, QVBoxLayout,
)


def load_core(bundle):
    spec = importlib.util.spec_from_file_location("playcore_installer_core", bundle / "instalar.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class InstallerWindow(QDialog):
    def __init__(self, bundle, destination=None, shortcuts=True):
        super().__init__()
        self.bundle = Path(bundle)
        manifest = self.bundle / "manifest.json"
        self.version = json.loads(manifest.read_text())["version"] if manifest.is_file() else "1.1.0"
        self.destination = destination or Path.home() / ".local/share/playcore"
        self.shortcuts = shortcuts
        self.installed_path = None
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self.read_stdout)
        self.process.readyReadStandardError.connect(self.read_stderr)
        self.process.finished.connect(self.install_finished)
        self.process.errorOccurred.connect(self.process_error)
        self.setWindowTitle(f"Instalar PlayCore {self.version}")
        self.setWindowIcon(QIcon.fromTheme("applications-games"))
        self.resize(650, 340)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        title = QLabel(f"PlayCore {self.version}")
        font = title.font()
        font.setPointSize(font.pointSize() + 8)
        font.setBold(True)
        title.setFont(font)
        layout.addWidget(title)
        for text in (
            "Instala PlayCore para SteamOS o Bazzite en tu cuenta de usuario.",
            "Incluye sus bibliotecas Qt. No necesita conexión ni permisos de administrador para instalar PlayCore.",
            "Al terminar tendrás un acceso en el menú de aplicaciones. Los componentes de juego se instalan después, desde PlayCore.",
            f"Destino: {self.destination}",
        ):
            label = QLabel(text)
            label.setTextFormat(Qt.TextFormat.PlainText)
            label.setWordWrap(True)
            layout.addWidget(label)
        self.status = QLabel("Todo listo. Pulsa Instalar PlayCore para comenzar.")
        self.status.setTextFormat(Qt.TextFormat.PlainText)
        self.status.setWordWrap(True)
        layout.addWidget(self.status)
        self.progress = QProgressBar()
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        layout.addWidget(self.progress)
        self.details_button = QToolButton()
        self.details_button.setText("Mostrar mensajes")
        self.details_button.setCheckable(True)
        self.details_button.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)
        self.details_button.setArrowType(Qt.ArrowType.RightArrow)
        self.details_button.toggled.connect(self.toggle_details)
        layout.addWidget(self.details_button)
        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumBlockCount(300)
        self.log.setFixedHeight(90)
        self.log.hide()
        layout.addWidget(self.log)
        buttons = QHBoxLayout()
        self.close_button = QPushButton("Cerrar")
        self.close_button.clicked.connect(self.close)
        buttons.addWidget(self.close_button)
        buttons.addStretch()
        self.open_button = QPushButton("Abrir PlayCore")
        self.open_button.setEnabled(False)
        self.open_button.clicked.connect(self.open_application)
        buttons.addWidget(self.open_button)
        self.install_button = QPushButton("Instalar PlayCore")
        self.install_button.setDefault(True)
        self.install_button.clicked.connect(self.start_install)
        buttons.addWidget(self.install_button)
        layout.addLayout(buttons)

    def toggle_details(self, visible):
        self.log.setVisible(visible)
        self.details_button.setText("Ocultar mensajes" if visible else "Mostrar mensajes")
        self.details_button.setArrowType(Qt.ArrowType.DownArrow if visible else Qt.ArrowType.RightArrow)

    def start_install(self):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            return
        self.install_button.setEnabled(False)
        self.close_button.setEnabled(False)
        self.open_button.setEnabled(False)
        self.status.setText("Instalando PlayCore. Espera a que termine…")
        self.progress.setRange(0, 0)
        arguments = ["-I", str(self.bundle / "instalar.py"), "--dest", str(self.destination)]
        if not self.shortcuts:
            arguments.append("--no-shortcuts")
        self.process.start(sys.executable, arguments)

    def read_stdout(self):
        self.append_output(bytes(self.process.readAllStandardOutput()).decode("utf-8", errors="replace"))

    def read_stderr(self):
        self.append_output(bytes(self.process.readAllStandardError()).decode("utf-8", errors="replace"))

    def append_output(self, text):
        if text.strip():
            self.log.appendPlainText(text.rstrip())

    def install_finished(self, code, exit_status):
        self.read_stdout()
        self.read_stderr()
        self.close_button.setEnabled(True)
        self.progress.setRange(0, 100)
        if code == 0 and exit_status == QProcess.ExitStatus.NormalExit:
            self.installed_path = load_core(self.bundle).installation_path(self.bundle, self.destination)
            if not (self.installed_path / "abrir-playcore.sh").is_file():
                self.fail("El proceso terminó sin crear el lanzador de PlayCore.")
                return
            self.status.setText(f"Instalación de PlayCore {self.version} completada. Ya puedes abrir la aplicación.")
            self.progress.setValue(100)
            self.open_button.setEnabled(True)
            self.install_button.setText("Instalado")
            self.install_button.setEnabled(False)
        else:
            self.fail("No se completó la instalación. Abre los mensajes para consultar el motivo.")

    def fail(self, message):
        self.status.setText(message)
        self.progress.setRange(0, 100)
        self.progress.setValue(0)
        self.install_button.setText("Reintentar instalación")
        self.install_button.setEnabled(True)
        self.close_button.setEnabled(True)

    def process_error(self, error):
        if error == QProcess.ProcessError.FailedToStart:
            self.fail("No se pudo iniciar la instalación: " + self.process.errorString())

    def open_application(self):
        if self.installed_path is None:
            return
        ok, _ = QProcess.startDetached(str(self.installed_path / "abrir-playcore.sh"), [])
        if not ok:
            QMessageBox.warning(self, "PlayCore", "La instalación terminó, pero no se pudo abrir la aplicación.")

    def closeEvent(self, event):
        if self.process.state() != QProcess.ProcessState.NotRunning:
            event.ignore()
        else:
            event.accept()


def main(bundle, arguments=None):
    parser = argparse.ArgumentParser(description="Instalador gráfico de PlayCore")
    parser.add_argument("--dest", type=Path)
    parser.add_argument("--no-shortcuts", action="store_true")
    args = parser.parse_args(arguments)
    app = QApplication.instance() or QApplication(["Instalar PlayCore"])
    app.setApplicationName("Instalar PlayCore")
    window = InstallerWindow(bundle, args.dest, not args.no_shortcuts)
    window.show()
    return app.exec()
