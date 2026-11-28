"""Regression tests for repository package generation; no Kodi required."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile
from xml.etree import ElementTree

from _repo_generator import Generator


class GeneratorTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.release = Path(self.temporary.name) / "omega"
        self.source = self.release / "script.example"
        self.source.mkdir(parents=True)
        (self.source / "addon.xml").write_text(
            '<addon id="script.example" version="1.2.3"/>', encoding="utf-8")
        (self.source / "main.py").write_text("print('example')\n", encoding="utf-8")
        self.generator = Generator.__new__(Generator)
        self.generator.release_path = str(self.release)
        self.generator.zips_path = str(self.release / "zips")
        self.archive = self.release / "zips/script.example/script.example-1.2.3.zip"
        self.archive.parent.mkdir(parents=True)

    def build(self):
        self.generator._create_zip("script.example", "1.2.3")

    def assert_archive(self):
        with zipfile.ZipFile(self.archive) as archive:
            self.assertIsNone(archive.testzip())
            self.assertEqual(
                set(archive.namelist()), {"script.example/addon.xml", "script.example/main.py"})
            manifest = ElementTree.fromstring(archive.read("script.example/addon.xml"))
            self.assertEqual(manifest.get("version"), "1.2.3")

    def test_missing_archive_is_created(self):
        self.build()
        self.assert_archive()

    def test_zero_byte_archive_is_rebuilt(self):
        self.archive.write_bytes(b"")
        self.build()
        self.assert_archive()

    def test_truncated_archive_is_rebuilt(self):
        self.build()
        self.archive.write_bytes(self.archive.read_bytes()[:30])
        self.build()
        self.assert_archive()

    def test_empty_zip_is_rebuilt(self):
        with zipfile.ZipFile(self.archive, "w"):
            pass
        self.build()
        self.assert_archive()

    def test_wrong_version_is_rebuilt(self):
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("script.example/addon.xml",
                             '<addon id="script.example" version="1.0.0"/>')
        self.build()
        self.assert_archive()

    def test_crc_corruption_is_rebuilt(self):
        with zipfile.ZipFile(self.archive, "w") as archive:
            archive.writestr("script.example/addon.xml", (self.source / "addon.xml").read_bytes())
            archive.writestr("script.example/main.py", b"original payload")
        self.archive.write_bytes(self.archive.read_bytes().replace(b"original payload", b"corrupt! payload"))
        self.build()
        self.assert_archive()

    def test_valid_existing_archive_is_untouched(self):
        self.build()
        original = self.archive.read_bytes()
        os.utime(self.archive, (1000000000, 1000000000))
        with mock.patch("zipfile.ZipFile.write", side_effect=AssertionError("rebuilt valid ZIP")):
            self.build()
        self.assertEqual(self.archive.read_bytes(), original)
        self.assertEqual(self.archive.stat().st_mtime, 1000000000)

    def test_failed_build_keeps_old_archive_and_cleans_temporary_file(self):
        self.archive.write_bytes(b"broken original")
        with mock.patch("zipfile.ZipFile.write", side_effect=OSError("disk full")):
            with self.assertRaises(OSError):
                self.build()
        self.assertEqual(self.archive.read_bytes(), b"broken original")
        self.assertEqual(list(self.archive.parent.iterdir()), [self.archive])

    def test_failed_build_does_not_publish_index_or_checksum(self):
        index = self.release / "zips/addons.xml"
        checksum = self.release / "zips/addons.xml.md5"
        index.write_bytes(b"<addons/>")
        checksum.write_bytes(b"previous digest")
        with mock.patch.object(Generator, "_create_zip", side_effect=OSError("disk full")):
            with self.assertRaises(RuntimeError):
                Generator(str(self.release))
        self.assertEqual(index.read_bytes(), b"<addons/>")
        self.assertEqual(checksum.read_bytes(), b"previous digest")

    def test_checksum_hashes_exact_bytes_including_crlf(self):
        index = self.release / "zips/addons.xml"
        index.write_bytes(b"<addons>\r\n</addons>\r\n")
        self.generator._generate_md5_file()
        self.assertEqual(
            (self.release / "zips/addons.xml.md5").read_text(),
            hashlib.md5(index.read_bytes()).hexdigest())

    def test_generated_index_is_lf_with_matching_checksum(self):
        Generator(str(self.release))
        data = (self.release / "zips/addons.xml").read_bytes()
        self.assertNotIn(b"\r", data)
        self.assertEqual(
            (self.release / "zips/addons.xml.md5").read_text(),
            hashlib.md5(data).hexdigest())
        self.assertEqual(ElementTree.fromstring(data).find("addon").get("version"), "1.2.3")

    def test_failed_metadata_replace_preserves_previous_file(self):
        index = self.release / "zips/addons.xml"
        index.write_bytes(b"previous index")
        with mock.patch("os.replace", side_effect=OSError("access denied")):
            with self.assertRaises(OSError):
                self.generator._save_file(b"new index", str(index))
        self.assertEqual(index.read_bytes(), b"previous index")
        self.assertFalse(list(index.parent.glob("*.tmp")))


if __name__ == "__main__":
    unittest.main()
