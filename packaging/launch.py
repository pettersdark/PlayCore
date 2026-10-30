"""Entrada del paquete instalado, independiente de la carpeta de trabajo."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from playcore.__main__ import main

raise SystemExit(main())
