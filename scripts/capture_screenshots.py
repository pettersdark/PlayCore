#!/usr/bin/env python3
"""Captura widgets reales con datos de demostración, sin leer ni modificar el equipo."""
import argparse
import importlib.util
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from PySide6.QtWidgets import QApplication
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


def capture(output):
    output.mkdir(parents=True, exist_ok=True)
    app = QApplication.instance() or QApplication([])
    app.setApplicationName("PlayCore")
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)
    scanner = SimpleNamespace(home=Path("/home/gamer"), env={})
    window = MainWindow(scanner=scanner, auto_scan=False, installer=DemoInstaller())
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
    release = Release("1.3.0", "Ejemplo de novedades · versión de demostración\n\n"
                      "• Mejoras de estabilidad y correcciones.\n"
                      "• Actualización desde PlayCore conservando tus componentes.\n\n"
                      "Esta versión es un ejemplo para la captura; no está publicada.",
                      "https://github.com/pettersdark/PlayCore/releases/tag/v1.3.0",
                      "PlayCore-1.3.0-Bazzite-x86_64.run", "", "", 85 * 1024**2)
    with patch("playcore.ui.installation_destination", return_value=Path("/home/gamer/.local/share/playcore")):
        window.update_install_hint.hide()
        window.show_update_release(release)
        app.processEvents()
        assert window.grab().save(str(output / "actualizaciones.png"))
    window.close()

    spec = importlib.util.spec_from_file_location("screenshot_installer_gui", ROOT / "packaging/installer_gui.py")
    gui = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(gui)
    installer = gui.InstallerWindow(Path("/tmp/playcore-demo"), Path("/home/gamer/.local/share/playcore"))
    installer.show()
    app.processEvents()
    assert installer.grab().save(str(output / "instalador.png"))
    installer.close()
    print(f"Capturas reales con datos de demostración: {output}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "docs/images/v1.2")
    capture(parser.parse_args().output.resolve())
