import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from playcore.catalog import CSS_DEPENDENCIES, PLUGINS
from playcore.detection import Scanner
from playcore.system import detect_system, read_os_release


class DetectionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.home = self.root / "home/player"
        self.home.mkdir(parents=True)
        self.scanner = Scanner(self.home, self.root, {}, which=lambda _: None)

    def put(self, relative, content=""):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return path

    def test_steamos_and_hostname(self):
        self.put("etc/os-release", 'ID=steamos\nPRETTY_NAME="SteamOS"\nVERSION_ID=3.7\n')
        self.put("etc/hostname", "playdeck\n")
        info = detect_system(self.root, {"XDG_CURRENT_DESKTOP": "KDE", "XDG_SESSION_TYPE": "wayland"})
        self.assertEqual((info.distribution, info.hostname, info.desktop, info.session),
                         ("steamos", "playdeck", "KDE", "wayland"))
        self.assertTrue(info.supported)

    def test_bazzite_variant_and_fallback_os_release(self):
        self.put("usr/lib/os-release", 'ID=fedora\nIMAGE_ID=bazzite-deck\nPRETTY_NAME="Bazzite"')
        self.assertEqual(detect_system(self.root, {}).distribution, "bazzite")

    def test_bazzite_id(self):
        self.put("etc/os-release", 'ID=bazzite\n')
        self.assertTrue(detect_system(self.root, {}).supported)

    def test_unknown_system_and_hostname_fallback(self):
        with patch("playcore.system.socket.gethostname", return_value="fallback"):
            info = detect_system(self.root, {})
        self.assertFalse(info.supported)
        self.assertEqual(info.hostname, "fallback")

    def test_release_is_data_never_shell(self):
        path = self.put("etc/os-release", 'ID=steamos\nBAD="unterminated\nNAME="$(touch /tmp/no-execute)"\n# comment\n')
        data = read_os_release(path)
        self.assertNotIn("BAD", data)
        self.assertEqual(data["NAME"], "$(touch /tmp/no-execute)")

    def test_user_and_system_flatpak(self):
        calls = []
        def runner(args, **kwargs):
            calls.append((args, kwargs))
            app = "com.heroicgameslauncher.hgl" if "--user" in args else "com.vysp3r.ProtonPlus"
            return subprocess.CompletedProcess(args, 0, app + "\n", "")
        scanner = Scanner(self.home, self.root, {}, runner=runner,
                          which=lambda x: "/usr/bin/flatpak" if x == "flatpak" else None)
        self.assertEqual([f.status for f in scanner.applications()], ["Detectado", "Detectado"])
        self.assertEqual(len(calls), 2)
        self.assertTrue(all(c[0][:2] == ["flatpak", "list"] for c in calls))
        self.assertTrue(all(c[1]["timeout"] == 5 and "shell" not in c[1] for c in calls))

    def test_flatpak_failure_is_unknown(self):
        def runner(args, **kwargs):
            raise subprocess.TimeoutExpired(args, 5)
        scanner = Scanner(self.home, self.root, {}, runner=runner,
                          which=lambda x: "/usr/bin/flatpak" if x == "flatpak" else None)
        self.assertTrue(all(f.status == "Desconocido" for f in scanner.applications()))
        self.assertEqual(len(scanner.warnings), 2)

    def test_native_executable(self):
        self.scanner.which = lambda x: "/usr/bin/heroic" if x == "heroic" else None
        result = self.scanner.applications()
        self.assertEqual(result[0].status, "Detectado")
        self.assertEqual(result[1].status, "No detectado")

    def test_leftover_flatpak_data_is_not_installation(self):
        self.put("home/player/.var/app/com.heroicgameslauncher.hgl/config/settings.json", "{}")
        self.assertEqual(self.scanner.applications()[0].status, "No detectado")

    def test_flatpak_active_metadata_and_xdg(self):
        self.scanner.env["XDG_DATA_HOME"] = str(self.home / "custom-data")
        self.put("home/player/custom-data/flatpak/app/com.heroicgameslauncher.hgl/current/active/metadata", "[Application]")
        self.put("var/lib/flatpak/app/com.vysp3r.ProtonPlus/current/active/metadata", "[Application]")
        self.assertTrue(all(f.status == "Detectado" for f in self.scanner.applications()))

    def test_proton_native_and_flatpak_deduplicated(self):
        for base in (".local/share/Steam", ".var/app/com.valvesoftware.Steam/data/Steam"):
            for filename in ("compatibilitytool.vdf", "proton"):
                self.put(f"home/player/{base}/compatibilitytools.d/proton-cachyos-11/{filename}")
        (self.home / ".steam").mkdir()
        (self.home / ".steam/root").symlink_to(self.home / ".local/share/Steam")
        result = self.scanner.proton()[0]
        self.assertEqual(result.status, "Detectado")
        self.assertEqual(len(result.evidence.split("; ")), 2)

    def test_empty_proton_folder_not_detected(self):
        self.put("home/player/.local/share/Steam/compatibilitytools.d/proton-cachyos/README")
        self.assertEqual(self.scanner.proton()[0].status, "No detectado")

    def test_proton_ge_native_flatpak_and_incomplete_folder(self):
        for base in (".local/share/Steam", ".var/app/com.valvesoftware.Steam/data/Steam"):
            for filename in ("proton", "compatibilitytool.vdf"):
                self.put(f"home/player/{base}/compatibilitytools.d/GE-Proton11-11/{filename}")
        self.put("home/player/.local/share/Steam/compatibilitytools.d/GE-Proton-incomplete/README")
        results = {finding.name: finding for finding in self.scanner.proton()}
        self.assertEqual(results["Proton-CachyOS"].status, "No detectado")
        self.assertEqual(results["Proton-GE"].status, "Detectado")
        self.assertEqual(len(results["Proton-GE"].evidence.split("; ")), 2)
        self.assertNotIn("incomplete", results["Proton-GE"].evidence)

    def test_decky_plugins_by_manifest_not_directory(self):
        self.put("home/player/homebrew/services/PluginLoader")
        for i, aliases in enumerate(PLUGINS.values()):
            self.put(f"home/player/homebrew/plugins/arbitrary-{i}/plugin.json", json.dumps({"name": aliases[0]}))
        snapshot = self.scanner.scan()
        self.assertEqual(len(snapshot.decky), 5)
        self.assertTrue(all(f.status == "Detectado" for f in snapshot.decky))

    def test_themes_and_profiles(self):
        for i, name in enumerate(("Machine Ready", *CSS_DEPENDENCIES)):
            self.put(f"home/player/homebrew/themes/theme-{i}/theme.json", json.dumps({"name": name}))
        (self.home / "homebrew/themes/Soft Play.profile").mkdir()
        self.put("home/player/homebrew/themes/not-a-directory.profile")
        snapshot = self.scanner.scan()
        self.assertEqual(len(snapshot.themes), 15)
        self.assertTrue(all(f.status == "Detectado" for f in snapshot.themes))
        self.assertEqual(snapshot.profiles, ("Soft Play.profile",))

    def test_corrupt_manifests_do_not_abort_scan(self):
        self.put("home/player/homebrew/plugins/broken/plugin.json", "{")
        self.put("home/player/homebrew/themes/broken/theme.json", "[]")
        snapshot = self.scanner.scan()
        self.assertEqual(len(snapshot.warnings), 2)
        self.assertEqual(snapshot.themes[0].status, "No detectado")

    def test_unreadable_directory_is_reported(self):
        with patch.object(Path, "iterdir", side_effect=PermissionError("denegado")):
            result = self.scanner.children(self.home)
        self.assertEqual(result, [])
        self.assertIn("denegado", self.scanner.warnings[0])

    def test_scan_does_not_modify_inventory(self):
        self.put("etc/os-release", "ID=steamos")
        self.put("home/player/homebrew/themes/test/theme.json", '{"name": "Better Blur"}')
        def tree():
            return {str(p.relative_to(self.root)): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        before = tree()
        self.scanner.scan()
        self.assertEqual(tree(), before)


if __name__ == "__main__":
    unittest.main()
