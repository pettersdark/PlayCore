"""Inventario de solo lectura con rutas y ejecutor inyectables para pruebas."""
import json
import os
import re
import shutil
import subprocess
from pathlib import Path

from .catalog import APPLICATIONS, CSS_ALIASES, CSS_DEPENDENCIES, PLUGINS
from .models import Finding, Snapshot
from .system import detect_system
from .accounts import current_account, password_status


def normalized(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", value.casefold())


class Scanner:
    def __init__(self, home=None, root=Path("/"), environ=None,
                 runner=subprocess.run, which=shutil.which):
        self.home = Path.home() if home is None else Path(home)
        self.root = Path(root)
        self.env = dict(os.environ if environ is None else environ)
        self.runner = runner
        self.which = which
        self.warnings: list[str] = []

    def children(self, path):
        try:
            return sorted(path.iterdir()) if path.exists() else []
        except OSError as exc:
            self.warnings.append(f"No se puede leer {path}: {exc}")
            return []

    def manifests(self, directory, filename):
        found = {}
        for folder in self.children(directory):
            manifest = folder / filename
            try:
                if not manifest.is_file():
                    continue
                data = json.loads(manifest.read_text(encoding="utf-8"))
                name = data.get("name") if isinstance(data, dict) else None
                if not isinstance(name, str) or not name.strip():
                    raise ValueError("falta un nombre válido")
                found[normalized(name)] = str(manifest)
            except (OSError, ValueError, UnicodeError) as exc:
                self.warnings.append(f"No se pudo interpretar {manifest}: {exc}")
        return found

    def applications(self):
        ids = set()
        uncertain = False
        if self.which("flatpak"):
            for scope in ("--user", "--system"):
                try:
                    completed = self.runner(
                        ["flatpak", "list", scope, "--app", "--columns=application"],
                        capture_output=True, text=True, timeout=5, check=False,
                    )
                    if completed.returncode:
                        raise RuntimeError(completed.stderr.strip() or "consulta fallida")
                    ids.update(completed.stdout.splitlines())
                except (OSError, subprocess.TimeoutExpired, RuntimeError) as exc:
                    uncertain = True
                    self.warnings.append(f"Flatpak {scope}: {exc}")
        results = []
        data_home = Path(self.env.get("XDG_DATA_HOME", str(self.home / ".local/share")))
        for app in APPLICATIONS:
            evidence = []
            if app.flatpak_id in ids:
                evidence.append(f"Flatpak: {app.flatpak_id}")
            # Metadata activa, no ~/.var/app: los datos pueden quedar tras desinstalar.
            for base in (data_home / "flatpak", self.root / "var/lib/flatpak"):
                active = base / "app" / app.flatpak_id / "current/active/metadata"
                if active.is_file():
                    evidence.append(str(active))
            for executable in app.executables:
                location = self.which(executable)
                if location:
                    evidence.append(location)
            results.append(Finding(app.name, "Detectado" if evidence else
                                   "Desconocido" if uncertain else "No detectado", "; ".join(evidence)))
        return tuple(results)

    def steam_roots(self):
        data = Path(self.env.get("XDG_DATA_HOME", str(self.home / ".local/share")))
        return (data / "Steam", self.home / ".steam/steam", self.home / ".steam/root",
                self.home / ".var/app/com.valvesoftware.Steam/data/Steam")

    def proton(self):
        matches = {"Proton-CachyOS": set(), "Proton-GE": set()}
        for steam in self.steam_roots():
            for folder in self.children(steam / "compatibilitytools.d"):
                name = normalized(folder.name)
                component = "Proton-CachyOS" if "cachyos" in name else (
                    "Proton-GE" if name.startswith(("geproton", "protonge")) else None)
                if component and folder.is_dir():
                    if (folder / "compatibilitytool.vdf").is_file() and (folder / "proton").is_file():
                        matches[component].add(str(folder.resolve()))
        return tuple(Finding(component, "Detectado" if paths else "No detectado",
                             "; ".join(sorted(paths))) for component, paths in matches.items())

    def scan(self):
        self.warnings.clear()
        applications = self.applications()
        proton = self.proton()
        homebrew = self.home / "homebrew"
        plugins = self.manifests(homebrew / "plugins", "plugin.json")
        loader = homebrew / "services/PluginLoader"
        decky = [Finding("Decky Loader", "Detectado" if loader.is_file() else "No detectado",
                         str(loader) if loader.is_file() else "")]
        for name, aliases in PLUGINS.items():
            evidence = next((plugins[normalized(a)] for a in aliases if normalized(a) in plugins), "")
            decky.append(Finding(name, "Detectado" if evidence else "No detectado", evidence))
        themes_dir = homebrew / "themes"
        manifests = self.manifests(themes_dir, "theme.json")
        themes = []
        for name in ("Machine Ready", *CSS_DEPENDENCIES):
            evidence = next((manifests[normalized(alias)] for alias in CSS_ALIASES.get(name, (name,))
                             if normalized(alias) in manifests), "")
            themes.append(Finding(name, "Detectado" if evidence else "No detectado", evidence))
        profiles = tuple(p.name for p in self.children(themes_dir)
                         if p.is_dir() and p.name.endswith(".profile"))
        try:
            free = shutil.disk_usage(self.home).free
        except OSError as exc:
            free = -1
            self.warnings.append(f"Espacio libre: {exc}")
        return Snapshot(detect_system(self.root, self.env), applications, proton,
                        tuple(decky), tuple(themes), profiles, tuple(self.warnings), free,
                        current_account(), password_status(self.runner, self.which))
