import hashlib
import io
import json
import stat
import subprocess
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from playcore.installers import Installer, RELEASE_API, select_release_asset
from playcore.plugin_package import PLUGIN_NAME, deploy_package, validate_package


def make_package(extra=(), manifest=None, package=None):
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as archive:
        archive.writestr(f"{PLUGIN_NAME}/plugin.json", json.dumps(manifest or {"name": PLUGIN_NAME, "flags": []}))
        archive.writestr(f"{PLUGIN_NAME}/package.json", json.dumps(package or {"name": "decky-launch-options", "version": "1.0"}))
        archive.writestr(f"{PLUGIN_NAME}/main.py", "# fixture, never executed\n")
        archive.writestr(f"{PLUGIN_NAME}/dist/index.js", "// fixture\n")
        for name, content in extra:
            archive.writestr(name, content)
    payload = data.getvalue()
    return payload, hashlib.sha256(payload).hexdigest()


class PackageTests(unittest.TestCase):
    def test_valid_plugin_deployed_to_temporary_directory(self):
        payload, digest = make_package()
        with tempfile.TemporaryDirectory() as temp:
            directory = Path(temp)
            self.assertEqual(deploy_package(payload, digest, directory), "1.0")
            self.assertTrue((directory / PLUGIN_NAME / "dist/index.js").is_file())
            self.assertEqual([p.name for p in directory.iterdir()], [PLUGIN_NAME])

    def test_digest_mismatch(self):
        payload, _ = make_package()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            validate_package(payload, "0" * 64)

    def test_existing_plugin_is_not_overwritten(self):
        payload, digest = make_package()
        with tempfile.TemporaryDirectory() as temp:
            target = Path(temp) / PLUGIN_NAME
            target.mkdir()
            marker = target / "keep.txt"
            marker.write_text("original")
            with self.assertRaises(FileExistsError):
                deploy_package(payload, digest, Path(temp))
            self.assertEqual(marker.read_text(), "original")

    def test_traversal_absolute_and_conflicting_paths(self):
        for name in ("../outside", "Launch Options/../outside", "/tmp/outside",
                     "Launch Options/./plugin.json", "Launch Options//plugin.json",
                     "Different/plugin.json", "Launch Options/\\outside"):
            with self.subTest(name=name):
                payload, digest = make_package([(name, "x")])
                with self.assertRaises(ValueError):
                    validate_package(payload, digest)

    def test_symlink_rejected(self):
        entry = zipfile.ZipInfo("Launch Options/link")
        entry.create_system = 3
        entry.external_attr = (stat.S_IFLNK | 0o777) << 16
        payload, digest = make_package([(entry, "/etc/passwd")])
        with self.assertRaises(ValueError):
            validate_package(payload, digest)

    def test_other_plugin_or_root_plugin_rejected(self):
        for manifest in ({"name": "Other"}, {"name": PLUGIN_NAME, "flags": ["root"]}):
            payload, digest = make_package(manifest=manifest)
            with self.assertRaises(ValueError):
                validate_package(payload, digest)

    def test_remote_binaries_not_silently_skipped(self):
        payload, digest = make_package(package={"name": "decky-launch-options", "remote_binary": [{"name": "external"}]})
        with self.assertRaisesRegex(ValueError, "diferente"):
            validate_package(payload, digest)

    def test_extraction_failure_leaves_no_plugin_or_staging(self):
        payload, digest = make_package()
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(zipfile.ZipFile, "extractall", side_effect=OSError("disco lleno")):
                with self.assertRaises(OSError):
                    deploy_package(payload, digest, Path(temp))
            self.assertEqual(list(Path(temp).iterdir()), [])


class InstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.calls = []
        def runner(args, **kwargs):
            self.calls.append((args, kwargs))
            return subprocess.CompletedProcess(args, 0, "completado", "")
        self.installer = Installer(home=self.home, runner=runner, which=lambda _: "/usr/bin/mock")

    def release(self, digest):
        return {"tag_name": "v1.0", "assets": [{"name": "decky-launch-options.zip",
                "browser_download_url": "https://github.com/Wurielle/decky-launch-options/releases/download/v1.0/decky-launch-options.zip",
                "digest": "sha256:" + digest}]}

    def prepare_plugin(self):
        loader = self.home / "homebrew/services/PluginLoader"
        loader.parent.mkdir(parents=True)
        loader.touch()
        payload, digest = make_package()
        release = self.release(digest)
        self.installer.downloader = lambda url, *args: json.dumps(release).encode() if url == RELEASE_API else payload
        return digest

    def test_flatpak_commands_are_user_scoped_and_allowlisted(self):
        self.installer.install("Heroic")
        self.installer.install("ProtonPlus")
        self.assertEqual(len(self.calls), 2)
        for args, kwargs in self.calls:
            self.assertEqual(args[:3], ["flatpak", "install", "--user"])
            self.assertTrue(args[-1].startswith("https://flathub.org/repo/appstream/"))
            self.assertNotIn("shell", kwargs)

    def test_unknown_target_never_executes(self):
        with self.assertRaises(ValueError):
            self.installer.install("arbitrary; command")
        self.assertEqual(self.calls, [])

    def test_missing_decky_never_downloads_or_executes(self):
        self.installer.downloader = lambda *args: self.fail("unexpected download")
        with self.assertRaisesRegex(RuntimeError, "Decky Loader"):
            self.installer.install("Decky Launch Options")
        self.assertEqual(self.calls, [])

    def test_validated_plugin_passed_to_policykit_only_on_request(self):
        digest = self.prepare_plugin()
        self.assertEqual(self.calls, [])
        self.installer.install("Decky Launch Options")
        args, kwargs = self.calls[0]
        self.assertEqual(args[:3], ["pkexec", "/usr/bin/python3", "-I"])
        self.assertEqual(args[-1], digest)
        self.assertFalse(Path(args[-2]).exists())  # Temporary download cleaned up.
        self.assertNotIn("shell", kwargs)

    def test_corrupt_download_never_reaches_policykit(self):
        digest = self.prepare_plugin()
        self.installer.downloader = lambda url, *args: json.dumps(self.release(digest)).encode() if url == RELEASE_API else b"corrupt"
        with self.assertRaises(ValueError):
            self.installer.install("Decky Launch Options")
        self.assertEqual(self.calls, [])

    def test_cancelled_authentication_is_reported(self):
        self.prepare_plugin()
        self.installer.runner = lambda args, **kwargs: subprocess.CompletedProcess(args, 126, "", "")
        with self.assertRaisesRegex(RuntimeError, "No se autorizó"):
            self.installer.install("Decky Launch Options")

    def test_failure_output_is_reported(self):
        self.installer.runner = lambda args, **kwargs: subprocess.CompletedProcess(args, 1, "", "sin espacio")
        with self.assertRaisesRegex(RuntimeError, "sin espacio"):
            self.installer.install("Heroic")

    def test_release_requires_official_url_stable_and_digest(self):
        release = self.release("a" * 64)
        self.assertEqual(select_release_asset(release)[1], "a" * 64)
        for field, value in (("browser_download_url", "https://other.invalid/plugin.zip"), ("digest", None)):
            bad = self.release("a" * 64)
            bad["assets"][0][field] = value
            with self.assertRaises((ValueError, TypeError)):
                select_release_asset(bad)
        release["prerelease"] = True
        with self.assertRaises(ValueError):
            select_release_asset(release)
