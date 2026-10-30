import io
import json
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

from playcore.content_packages import install_machine_zip, install_proton_archive, install_theme_zip, prepare_proton_latest


def theme_zip(entries):
    stream = io.BytesIO()
    with zipfile.ZipFile(stream, "w") as archive:
        for name, data in entries.items():
            archive.writestr(name, data)
    return stream.getvalue()


class ContentTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def test_theme_validation_and_existing_theme_preserved(self):
        payload = theme_zip({"Better Blur/theme.json": '{"name":"Better Blur"}', "Better Blur/shared.css": "body {}"})
        self.assertTrue(install_theme_zip(payload, self.root, "Better Blur"))
        css = self.root / "Better Blur/shared.css"
        css.write_text("custom")
        self.assertFalse(install_theme_zip(payload, self.root, "Better Blur"))
        self.assertEqual(css.read_text(), "custom")

    def test_css_store_alias_is_accepted_but_other_theme_is_not(self):
        payload = theme_zip({"no_home_tabs/theme.json": '{"name":"no_home_tabs"}'})
        self.assertTrue(install_theme_zip(payload, self.root, ("No Home Tabs", "no_home_tabs")))
        with self.assertRaises(ValueError):
            install_theme_zip(payload, self.root, "Other")

    def test_zip_traversal_is_rejected_before_extracting(self):
        payload = theme_zip({"../outside": "x"})
        with self.assertRaises(ValueError):
            install_theme_zip(payload, self.root, "Better Blur")
        self.assertEqual(list(self.root.iterdir()), [])

    def test_machine_copies_themes_and_profiles_without_activating(self):
        payload = theme_zip({
            "Machine-Ready-TV-sha/Machine Ready/theme.json": '{"name":"Machine Ready"}',
            "Machine-Ready-TV-sha/Profiles/Example.profile/theme.json": '{"name":"Example", "flags":["PRESET"]}',
            "Machine-Ready-TV-sha/scripts/install.sh": "never executed",
        })
        added, skipped = install_machine_zip(payload, self.root)
        self.assertEqual(set(added), {"Machine Ready", "Example.profile"})
        self.assertEqual(skipped, [])
        self.assertFalse((self.root / "scripts").exists())
        self.assertFalse((self.root / "STORE").exists())
        added, skipped = install_machine_zip(payload, self.root)
        self.assertEqual(added, [])
        self.assertEqual(len(skipped), 2)

    def make_tar(self, links=(), extra=()):
        destination = self.root / "proton.tar.xz"
        with tarfile.open(destination, "w:xz") as archive:
            for name in ("proton-cachyos-test/proton", "proton-cachyos-test/compatibilitytool.vdf", *extra):
                entry = tarfile.TarInfo(name)
                data = b"fixture"
                entry.size = len(data)
                entry.mode = 0o755
                archive.addfile(entry, io.BytesIO(data))
            for name, linkname in links:
                entry = tarfile.TarInfo(name)
                entry.type = tarfile.SYMTYPE
                entry.linkname = linkname
                archive.addfile(entry)
        return destination

    def test_proton_preserves_internal_symlinks_and_executable_mode(self):
        archive = self.make_tar([("proton-cachyos-test/alias", "proton")])
        steam = self.root / "Steam"
        result = install_proton_archive(archive, steam)
        self.assertTrue((result / "alias").is_symlink())
        self.assertTrue((result / "proton").stat().st_mode & 0o111)
        with self.assertRaises(FileExistsError):
            install_proton_archive(archive, steam)

    def test_latest_manifest_keeps_other_fields_and_rejects_ambiguous_tools(self):
        manifest = self.root / "compatibilitytool.vdf"
        for wrapper in (False, True):
            content = ('// upstream name\n"compat_tools" { "GE-Proton11-11" { '
                       '"display_name" "GE-Proton11-11" "install_path" "." '
                       '"from_oslist" "windows" "to_oslist" "linux" } }')
            if wrapper:
                content = '"compatibilitytools" { ' + content + ' }'
            manifest.write_text(content)
            prepare_proton_latest(self.root, "Proton-GE", {"tag": "GE-Proton11-11"})
            self.assertEqual(manifest.read_text().count('"Proton-GE Latest"'), 2)
            self.assertIn('"from_oslist" "windows"', manifest.read_text())
            self.assertEqual(json.loads((self.root / ".protonplus").read_text())["tag"], "GE-Proton11-11")
        for invalid in ('fixture', '"compat_tools" { "one" { "display_name" "One" } "two" { "display_name" "Two" } }',
                        '"compat_tools" { "one" { "install_path" "." } }'):
            manifest.write_text(invalid)
            with self.assertRaises(ValueError):
                prepare_proton_latest(self.root, "Proton-GE", {})
            self.assertEqual(manifest.read_text(), invalid)

    def test_proton_rejects_external_links_and_path_traversal(self):
        for link in ("/etc/passwd", "../../outside"):
            with self.subTest(link=link):
                archive = self.make_tar([("proton-cachyos-test/link", link)])
                with self.assertRaises(ValueError):
                    install_proton_archive(archive, self.root / "Steam")
        archive = self.make_tar(extra=("../outside",))
        with self.assertRaises(ValueError):
            install_proton_archive(archive, self.root / "Steam")
        self.assertEqual(list((self.root / "Steam/compatibilitytools.d").iterdir()), [])
