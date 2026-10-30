import json
from pathlib import Path
import tempfile
import unittest

from playcore.detection import Scanner
from playcore.launch_options import import_script, launch_options


class LaunchOptionsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.scanner = Scanner(self.home, self.home, {}, which=lambda _: None)

    def install_manifest(self, name="Launch Options"):
        manifest = self.home / "homebrew/plugins/dlo/plugin.json"
        manifest.parent.mkdir(parents=True, exist_ok=True)
        manifest.write_text(json.dumps({"name": name}))
        return manifest

    def test_missing_or_unrelated_plugin_blocks_preparation(self):
        with self.assertRaisesRegex(RuntimeError, "no detectado"):
            import_script(self.scanner)
        self.install_manifest("Other Plugin")
        with self.assertRaises(RuntimeError):
            import_script(self.scanner)

    def test_exact_profiles_are_exclusive_and_inactive(self):
        profiles = launch_options()
        self.assertEqual([(p["id"], p["valueName"], p["on"]) for p in profiles], [
            ("playcore-optiscaler", "OptiScaler", "PROTON_USE_OPTISCALER=1 %command%"),
            ("playcore-fsr4", "FSR 4 Upgrade", "PROTON_FSR4_UPGRADE=1 %command%"),
            ("playcore-optiscaler-fsr4", "OptiScaler + FSR 4",
             "PROTON_USE_OPTISCALER=1 PROTON_FSR4_UPGRADE=1 %command%"),
        ])
        self.assertEqual(len({p["valueId"] for p in profiles}), 1)
        self.assertTrue(profiles[0]["valueId"])
        self.assertEqual([p["name"] for p in profiles],
                         ["OptiScaler", "FSR 4 Upgrade", "OptiScaler + FSR 4"])
        for profile in profiles:
            self.assertIs(profile["enableGlobally"], False)
            self.assertIs(profile["fallbackValue"], False)
            self.assertEqual(profile["off"], "")

    def test_repeated_requests_are_identical_and_never_write_plugin_files(self):
        manifest = self.install_manifest()
        before = {p.relative_to(self.home): p.read_bytes()
                  for p in self.home.rglob("*") if p.is_file()}
        script = import_script(self.scanner)
        self.assertEqual(script, import_script(self.scanner))
        self.assertIn("window.hasDeckyLaunchOptions !== true", script)
        self.assertIn("new CustomEvent('dlo-add-launch-options'", script)
        payload = script.split("detail: ", 1)[1].split("\n  }));", 1)[0]
        self.assertEqual(json.loads(payload), launch_options())
        self.assertEqual(before, {p.relative_to(self.home): p.read_bytes()
                                  for p in self.home.rglob("*") if p.is_file()})
        manifest.unlink()
        with self.assertRaises(RuntimeError):
            import_script(self.scanner)
