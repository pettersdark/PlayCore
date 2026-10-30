#!/usr/bin/env python3
"""Captura widgets reales con datos de demostración, sin leer ni modificar el equipo."""
import argparse
import importlib.util
import json
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QSettings
from playcore import __version__
from playcore.catalog import CSS_DEPENDENCIES
from playcore.models import Finding, Snapshot, SystemInfo
from playcore.ui import MainWindow
from playcore.updater import Release


def demo_snapshot():
    steam = "/home/gamer/.local/share/Steam"
    return Snapshot(
        SystemInfo("bazzite", "Bazzite · KDE Plasma", "Demostración", "playcore-demo",
                   "Linux x86_64", "KDE Plasma", "Wayland"),
        (Finding("Heroic", "Detectado", "Flatpak: com.heroicgameslauncher.hgl"),
         Finding("ProtonPlus", "Detectado", "Flatpak: com.vysp3r.ProtonPlus")),
        (Finding("Proton-CachyOS", "Detectado", steam + "/compatibilitytools.d/proton-cachyos"),
         Finding("Proton-GE", "No detectado")),
        tuple(Finding(name, "Detectado",
                      "~/homebrew/" + location if location else "")
              for name, location in (("Decky Loader", "services/PluginLoader"),
                                     ("SteamGridDB", "plugins/decky-steamgriddb/plugin.json"),
                                     ("HLTB", "plugins/hltb-for-deck/plugin.json"),
                                     ("CSS Loader", "plugins/SDH-CssLoader/plugin.json"),
                                     ("Decky Launch Options", "plugins/launch-options/plugin.json"))),
        tuple(Finding(name, "Detectado", "~/homebrew/themes/" + name + "/theme.json")
              for name in ("Machine Ready", *CSS_DEPENDENCIES)),
        ("MR - Back 2 Basic.profile", "MR - Clean Glass.profile", "MR - Soft Play.profile"),
        (), 128 * 1024**3, "gamer", "Configurada",
    )


class DemoInstaller:
    def install(self, *_):
        raise RuntimeError("La sesión de capturas no permite instalaciones.")


def capture(output, language="es"):
    output.mkdir(parents=True, exist_ok=True)
    temporary = tempfile.TemporaryDirectory(prefix="playcore-preview-")
    settings = QSettings(str(Path(temporary.name) / "preferences.ini"), QSettings.Format.IniFormat)
    settings.setValue("ui/language", language)
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("PlayCore")
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    scanner = SimpleNamespace(home=Path("/home/gamer"), env={})
    window = MainWindow(scanner=scanner, auto_scan=False, installer=DemoInstaller(), settings=settings)
    window.resize(1280, 800)
    with patch("playcore.ui.steam_installations", return_value=(Path("/home/gamer/.local/share/Steam"),)):
        window.render_snapshot(demo_snapshot())
    window.show()
    for index, filename in ((0, "sistema.png"), (1, "aplicaciones.png"), (2, "proton.png"),
                            (3, "decky.png"), (4, "temas.png"), (5, "mantenimiento.png")):
        window.resize(1280, 980 if index == 4 else 800)
        window.navigation.setCurrentRow(index)
        app.processEvents()
        assert window.grab().save(str(output / filename)), filename
    window.navigation.setCurrentRow(3)
    window.operation_summary = "Instalación de CSS Loader completada."
    for log in window.install_logs:
        log.setPlainText("Instalación solicitada: CSS Loader")
    window.install_message("CSS Loader: paquete verificado.\nInstalación de CSS Loader completada.")
    window.message_panels[2].toggle.setChecked(True)
    app.processEvents()
    assert window.grab().save(str(output / "mensajes.png"))
    window.navigation.setCurrentRow(6)
    window.statusBar().showMessage("Vista de demostración del actualizador")
    window.show_update_release(None)
    app.processEvents()
    assert window.grab().save(str(output / "actualizaciones-al-dia.png"))
    # Versión futura simulada, mostrada como ejemplo de la interfaz instalada.
    notes = ("Ejemplo de novedades · versión de demostración\n\n"
                      "• Mejoras de estabilidad y correcciones.\n"
                      "• Actualización desde PlayCore conservando tus componentes.\n\n"
                      "Esta versión es un ejemplo para la captura; no está publicada." if language == "es" else
                      "Sample release notes · demonstration version\n\n"
                      "• Stability improvements and fixes.\n"
                      "• Update from PlayCore while preserving your components.\n\n"
                      "This version is a screenshot example; it has not been published.")
    release = Release("1.4.0", notes,
                      "https://github.com/pettersdark/PlayCore/releases/tag/v1.4.0",
                      "PlayCore-1.4.0-Bazzite-x86_64.run", "", "", 85 * 1024**2)
    with patch("playcore.ui.installation_destination", return_value=Path("/home/gamer/.local/share/playcore")):
        window.update_install_hint.hide()
        window.show_update_release(release)
        app.processEvents()
        assert window.grab().save(str(output / "actualizaciones.png"))
    window.close()

    spec = importlib.util.spec_from_file_location("screenshot_installer_gui", ROOT / "packaging/installer_gui.py")
    gui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gui)
    bundle = Path(temporary.name) / "bundle"
    bundle.mkdir()
    (bundle / "manifest.json").write_text(json.dumps({"version": __version__}))
    installer = gui.InstallerWindow(bundle, Path("/home/gamer/.local/share/playcore"), settings=settings)
    installer.show()
    app.processEvents()
    assert installer.grab().save(str(output / "instalador.png"))
    installer.close()
    temporary.cleanup()
    print(f"Capturas reales con datos de demostración: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--language", choices=("es", "en"), default="es")
    args = parser.parse_args()
    capture((args.output or ROOT / "docs/images/v1.3" / args.language).resolve(), args.language)
