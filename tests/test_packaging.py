import hashlib
import importlib.util
import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

SPEC = importlib.util.spec_from_file_location("playcore_bundle_installer", Path(__file__).resolve().parents[1] / "packaging/install.py")
installer = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(installer)


class PackagingTests(unittest.TestCase):
    def test_manifest_detects_modified_or_unexpected_payload(self):
        with tempfile.TemporaryDirectory() as temp:
            bundle = Path(temp)
            (bundle / "app").mkdir()
            (bundle / "wheels").mkdir()
            source = bundle / "app/test.py"
            source.write_bytes(b"fixture")
            metadata = {"files": {"app/test.py": hashlib.sha256(b"fixture").hexdigest()}}
            (bundle / "manifest.json").write_text(json.dumps(metadata))
            self.assertEqual(installer.verify_bundle(bundle), metadata)
            source.write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "modificado"):
                installer.verify_bundle(bundle)
            source.write_bytes(b"fixture")
            (bundle / "app/unexpected.py").write_text("extra")
            with self.assertRaisesRegex(ValueError, "inesperados"):
                installer.verify_bundle(bundle)

    def test_shortcuts_work_with_spaces_and_desktop_entry_is_valid(self):
        with tempfile.TemporaryDirectory(prefix="playcore shortcuts ") as temp:
            root = Path(temp)
            installation = root / "installation with spaces"
            installation.mkdir()
            launcher = installation / "abrir-playcore.sh"
            launcher.write_text('#!/bin/sh\nprintf "%s\\n" "$1"\n')
            launcher.chmod(0o755)
            binary, desktop = installer.write_shortcuts(installation, root / "user home")
            completed = subprocess.run([str(binary), "argument with spaces"], capture_output=True, text=True, check=True)
            self.assertEqual(completed.stdout.strip(), "argument with spaces")
            from shutil import which
            if which("desktop-file-validate"):
                subprocess.run(["desktop-file-validate", str(desktop)], check=True)
            self.assertEqual(installer.write_shortcuts(installation, root / "user home"), (binary, desktop))

    def test_unrelated_launcher_is_never_overwritten(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            binary = root / ".local/bin/playcore"
            binary.parent.mkdir(parents=True)
            binary.write_text("unrelated command")
            with self.assertRaises(FileExistsError):
                installer.write_shortcuts(root / "installation", root)
            self.assertEqual(binary.read_text(), "unrelated command")

    def test_installer_refuses_root(self):
        with patch.object(installer.os, "geteuid", return_value=0):
            with self.assertRaisesRegex(RuntimeError, "sin sudo"):
                installer.check_platform()
