import hashlib
import io
import json
import subprocess
import tempfile
import unittest
import zipfile
import tarfile
from pathlib import Path
from unittest.mock import patch

from playcore.catalog import CSS_THEME_IDS
from playcore.installers import CSS_API, DECKY_CDN, DECKY_STORE, Installer, download_file
from playcore.plugin_package import PLUGIN_SPECS, validate_package


class CatalogInstallerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name)
        self.calls = []
        def runner(args, **kwargs):
            self.calls.append(args)
            return subprocess.CompletedProcess(args, 0, "ok", "")
        self.installer = Installer(home=self.home, runner=runner, which=lambda _: "/usr/bin/mock")

    def decky(self):
        path = self.home / "homebrew/services/PluginLoader"
        path.parent.mkdir(parents=True)
        path.touch()
        manifest = self.home / "homebrew/plugins/SDH-CssLoader/plugin.json"
        manifest.parent.mkdir(parents=True)
        manifest.write_text('{"name":"CSS Loader"}')

    def test_each_store_plugin_is_verified_then_sent_to_helper(self):
        self.decky()
        for component in ("CSS Loader", "HLTB", "SteamGridDB"):
            root, name, package = PLUGIN_SPECS[component]
            stream = io.BytesIO()
            with zipfile.ZipFile(stream, "w") as archive:
                archive.writestr(root + "/plugin.json", json.dumps({"name": name}))
                archive.writestr(root + "/package.json", json.dumps({"name": package, "version": "1.0"}))
                archive.writestr(root + "/dist/index.js", "// fixture")
            payload = stream.getvalue()
            digest = hashlib.sha256(payload).hexdigest()
            catalog = [{"name": name, "versions": [{"name": "1.0", "hash": digest}]}]
            def download(url, *args):
                if url == DECKY_STORE:
                    return json.dumps(catalog).encode()
                self.assertEqual(url, DECKY_CDN + digest + ".zip")
                return payload
            self.installer.downloader = download
            self.assertEqual(validate_package(payload, digest, component), "1.0")
            self.installer.install(component)
            self.assertEqual(self.calls[-1][-3], component)

    def test_loader_uses_verified_official_release_and_never_overwrites(self):
        payload = b"#!/bin/bash\n# never executed by this test\n"
        digest = hashlib.sha256(payload).hexdigest()
        release = {"assets": [{"name": "install_release.sh", "digest": "sha256:" + digest,
                    "browser_download_url": "https://github.com/SteamDeckHomebrew/decky-installer/releases/download/v1/install_release.sh"}]}
        self.installer.downloader = lambda url, *args: payload if url.endswith(".sh") else json.dumps(release).encode()
        self.installer.install("Decky Loader")
        self.assertEqual(self.calls[-1][-3], "Decky Loader")
        self.decky()
        with self.assertRaises(FileExistsError):
            self.installer.install("Decky Loader")
        self.assertEqual(len(self.calls), 1)

    def test_css_downloads_correct_blob_and_preserves_existing_installation(self):
        self.decky()
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w") as archive:
            archive.writestr("Better Blur/theme.json", '{"name":"Better Blur"}')
        urls = []
        def download(url, *args):
            urls.append(url)
            if url == CSS_API + "/themes/" + CSS_THEME_IDS["Better Blur"]:
                return json.dumps({"name": "Better Blur", "approved": True,
                                   "download": {"id": "blob"}, "dependencies": []}).encode()
            self.assertEqual(url, CSS_API + "/blobs/blob")
            return stream.getvalue()
        self.installer.downloader = download
        self.installer.install("Better Blur")
        self.assertTrue((self.home / "homebrew/themes/Better Blur/theme.json").is_file())
        count = len(urls)
        self.installer.install("Better Blur")
        self.assertEqual(len(urls), count)
        self.assertEqual(self.calls, [])

    def test_unapproved_theme_never_downloads_blob(self):
        self.decky()
        self.installer.downloader = lambda *args: b'{"name":"Better Blur", "approved":false}'
        with self.assertRaisesRegex(ValueError, "aprobado"):
            self.installer.install("Better Blur")
        self.assertFalse((self.home / "homebrew/themes").exists())

    def test_proton_requires_manual_target_when_multiple_steam_installations(self):
        for path in (".local/share/Steam", ".var/app/com.valvesoftware.Steam/data/Steam"):
            (self.home / path).mkdir(parents=True)
        with patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(ValueError, "Selecciona"):
                self.installer.install("Proton-CachyOS")
            with self.assertRaisesRegex(ValueError, "destino"):
                self.installer.install("Proton-CachyOS", steam_target="/tmp/other")
        self.assertEqual(self.calls, [])

    def test_proton_pipeline_selects_baseline_asset_and_installs_to_chosen_steam(self):
        target = self.home / ".var/app/com.valvesoftware.Steam/data/Steam"
        target.mkdir(parents=True)
        source = self.home / "fixture.tar.xz"
        with tarfile.open(source, "w:xz") as archive:
            for name in ("proton", "compatibilitytool.vdf"):
                member = tarfile.TarInfo("proton-cachyos-test/" + name)
                member.size = 1
                archive.addfile(member, io.BytesIO(b"x"))
        repository = "CachyOS/proton-cachyos"
        url = f"https://github.com/{repository}/releases/download/v1/proton-cachyos-test-slr-x86_64.tar.xz"
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        release = {"assets": [{"name": "proton-cachyos-test-slr-x86_64.tar.xz", "size": 1,
                               "browser_download_url": url, "digest": "sha256:" + digest}]}
        self.installer.downloader = lambda *args: json.dumps(release).encode()
        def copy(url_arg, destination, digest_arg, progress):
            self.assertEqual((url_arg, digest_arg), (url, digest))
            destination.write_bytes(source.read_bytes())
        self.installer.file_downloader = copy
        with patch.dict("os.environ", {}, clear=True), patch("playcore.installers.platform.machine", return_value="x86_64"), patch("playcore.installers.shutil.disk_usage") as usage:
            usage.return_value.free = 10 * 1024**3
            message = self.installer.install("Proton-CachyOS", steam_target=str(target))
        self.assertIn("Reinicia Steam", message)
        self.assertTrue((target / "compatibilitytools.d/proton-cachyos-test/proton").is_file())
        self.assertEqual(self.calls, [])

    def test_streamed_download_verifies_sha256(self):
        payload = b"fixture streamed to disk"
        destination = self.home / "download"
        with patch("playcore.installers.urllib.request.urlopen", return_value=io.BytesIO(payload)):
            download_file("https://github.com/example", destination, hashlib.sha256(payload).hexdigest(), lambda _: None)
        self.assertEqual(destination.read_bytes(), payload)
        with patch("playcore.installers.urllib.request.urlopen", return_value=io.BytesIO(payload)):
            with self.assertRaisesRegex(ValueError, "SHA-256"):
                download_file("https://github.com/example", destination, "0" * 64, lambda _: None)

    def test_ge_selects_architecture_and_installs_gzip_archive(self):
        target = self.home / ".local/share/Steam"
        target.mkdir(parents=True)
        source = self.home / "fixture.tar.gz"
        with tarfile.open(source, "w:gz") as archive:
            for name in ("proton", "compatibilitytool.vdf"):
                member = tarfile.TarInfo("GE-Proton11-11/" + name)
                member.size = 1
                archive.addfile(member, io.BytesIO(b"x"))
        digest = hashlib.sha256(source.read_bytes()).hexdigest()
        prefix = "https://github.com/GloriousEggroll/proton-ge-custom/releases/download/GE-Proton11-11/"
        release = {"assets": [{"name": "GE-Proton11-11-" + arch + ".tar.gz", "size": 1,
                    "browser_download_url": prefix + "GE-Proton11-11-" + arch + ".tar.gz",
                    "digest": "sha256:" + digest} for arch in ("x86_64", "aarch64")]}
        self.installer.downloader = lambda *args: json.dumps(release).encode()
        def copy(url, destination, sha, progress):
            self.assertTrue(url.endswith("-x86_64.tar.gz"))
            self.assertEqual(sha, digest)
            destination.write_bytes(source.read_bytes())
        self.installer.file_downloader = copy
        with patch.dict("os.environ", {}, clear=True), patch("playcore.installers.platform.machine", return_value="x86_64"), patch("playcore.installers.shutil.disk_usage") as usage:
            usage.return_value.free = 10 * 1024**3
            message = self.installer.install("Proton-GE", steam_target=target)
        self.assertIn("Instalación de Proton-GE completada.", message)
        self.assertTrue((target / "compatibilitytools.d/GE-Proton11-11/proton").is_file())
        self.assertEqual(self.calls, [])
