import argparse
import sys


def main():
    try:
        from PySide6.QtWidgets import QApplication
    except ImportError:
        print("Falta PySide6. Consulta README.md para preparar el entorno local.", file=sys.stderr)
        return 1
    from .ui import MainWindow
    parser = argparse.ArgumentParser(description="PlayCore: inventario e instalación bajo demanda")
    parser.add_argument("--section", choices=[name for name, _ in MainWindow.SECTIONS], default="Sistema")
    arguments, qt_arguments = parser.parse_known_args()
    app = QApplication([sys.argv[0], *qt_arguments])
    app.setApplicationName("PlayCore")
    app.setOrganizationName("PlayCore")
    app.setApplicationVersion("1.0.0")
    # Qt utiliza el plugin de plataforma y estilo del escritorio, sin QSS ni paleta forzada.
    window = MainWindow()
    window.navigation.setCurrentRow([name for name, _ in MainWindow.SECTIONS].index(arguments.section))
    window.show()
    return app.exec()


if __name__ == "__main__":
    raise SystemExit(main())
