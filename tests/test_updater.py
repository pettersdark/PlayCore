import hashlib
import io
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from playcore.updater import (Updater, check_latest, installation_destination,
                              parse_release, version_tuple)


def release_data(version="1.4.0", payload=b"installer"):
    name = f"PlayCore-{version}-Bazzite-x86_64.run"
    base = f"https://github.com/pettersdark/PlayCore/releases/download/v{version}/"
    digest = hashlib.sha256(payload).hexdigest()
    return {"tag_name": "v" + version, "body": "Novedades de prueba",
            "assets": [{"name": name, "browser_download_url": base + name,
                        "size": len(payload), "digest": "sha256:" + digest},
                       {"name": name + ".sha256", "browser_download_url": base + name + ".sha256"}]}


class Response(io.BytesIO):
    def geturl(self):
        return "https://release-assets.githubusercontent.com/fixture"


class UpdaterTests(unittest.TestCase):
    def test_numeric_versions_and_only_newer_stable_releases(self):
        self.assertGreater(version_tuple("v1.10.0"), version_tuple("1.9.0"))
        for version in ("1.0.0", "1.1.0"):
            self.assertIsNone(parse_release(release_data(version)))
        self.assertEqual(parse_release(release_data()).version, "1.4.0")
        for flag in ("draft", "prerelease"):
            self.assertIsNone(parse_release(dict(release_data(), **{flag: True})))
        for invalid in ("1.2", "1.4.0-beta", "../../1.4.0", None):
            with self.assertRaises(ValueError):
                version_tuple(invalid)

    def test_incomplete_or_foreign_release_is_rejected(self):
        data = release_data()
        data["assets"].pop()
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            parse_release(data)
        data = release_data()
        data["assets"][0]["browser_download_url"] = "https://example.com/evil.run"
        with self.assertRaisesRegex(ValueError, "oficial"):
            parse_release(data)

    def test_only_installed_copy_can_update_itself(self):
        self.assertIsNone(installation_destination())
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            install = root / "versions/1.1.0-test"
            source = install / "app/playcore/updater.py"
            source.parent.mkdir(parents=True)
            source.touch()
            self.assertIsNone(installation_destination(source))
            (install / "package.json").write_text("{}")
            (install / "abrir-playcore.sh").touch()
            self.assertEqual(installation_destination(source), root)

    def download(self, payload, checksum_payload=None, digest_override=None):
        original = b"verified installer"
        data = release_data(payload=original)
        if digest_override is not None:
            data["assets"][0]["digest"] = digest_override
        release = parse_release(data)
        checksum = (hashlib.sha256(original).hexdigest() + "  " + release.filename).encode()
        updater = Updater()
        self.addCleanup(updater.cleanup)
        progress = []
        with patch("playcore.updater.request", side_effect=[Response(checksum_payload or checksum), Response(payload)]):
            path = updater.download(release, progress.append)
        return updater, path, progress

    def test_download_verifies_hash_and_size_and_cleans_up(self):
        updater, path, progress = self.download(b"verified installer")
        self.assertEqual(path.read_bytes(), b"verified installer")
        self.assertEqual(progress[-1], 100)
        updater.cleanup()
        self.assertFalse(path.exists())

    def test_corrupt_truncated_oversized_or_wrong_checksum_never_installs(self):
        for payload in (b"corrupt installer!", b"short", b"too large" * 10):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.download(payload)
        with self.assertRaisesRegex(ValueError, "SHA-256"):
            self.download(b"verified installer", checksum_payload=b"invalid checksum")
        with self.assertRaisesRegex(ValueError, "GitHub"):
            self.download(b"verified installer", digest_override="sha256:" + "0" * 64)

    def test_network_errors_have_actionable_messages(self):
        for code, message in ((404, "pública"), (403, "limitado"), (500, "HTTP 500")):
            with patch("playcore.updater.request", side_effect=HTTPError("url", code, "", {}, None)):
                with self.assertRaisesRegex(RuntimeError, message):
                    check_latest()
        with patch("playcore.updater.request", side_effect=URLError("offline")):
            with self.assertRaisesRegex(RuntimeError, "conexión"):
                check_latest()
