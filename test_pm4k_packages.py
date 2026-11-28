"""Validate built PM4K releases: python -B -m unittest -q test_pm4k_packages.

Requires the same Python dependencies as PM4K's offline test harness.
DONT_PANIC_ROOT can point at a candidate repository before publication.
"""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import zipfile
from xml.etree import ElementTree

ROOT = Path(os.environ.get("DONT_PANIC_ROOT", Path(__file__).resolve().parent))
FEEDS = (("matrix", 19), ("nexus", 20), ("omega", 21))


def current_package(feed):
    source = ROOT / feed / "script.plexmod/addon.xml"
    version = ElementTree.parse(source).getroot().get("version")
    return ROOT / feed / "zips/script.plexmod" / ("script.plexmod-" + version + ".zip")


def payload(path):
    with zipfile.ZipFile(path) as archive:
        if archive.testzip() is not None:
            raise AssertionError("Corrupt archive: " + str(path))
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise AssertionError("Duplicate archive members: " + str(path))
        return {name: hashlib.sha256(archive.read(name)).hexdigest()
                for name in names if not name.endswith("/")}


class PM4KPackageTests(unittest.TestCase):
    def test_modern_variants_contain_identical_release_files(self):
        reference = payload(current_package("matrix"))
        for feed, _ in FEEDS:
            with self.subTest(feed=feed):
                actual = payload(current_package(feed))
                different = sorted(name for name in set(reference) | set(actual)
                                   if reference.get(name) != actual.get(name))
                self.assertEqual(different, [], "Inconsistent release source: " + feed)

    def test_package_payload_matches_staging_source(self):
        for feed, _ in FEEDS:
            with self.subTest(feed=feed):
                for name, digest in payload(current_package(feed)).items():
                    source = ROOT / feed / name
                    self.assertTrue(source.is_file(), str(source))
                    self.assertEqual(hashlib.sha256(source.read_bytes()).hexdigest(), digest, name)

    def test_main_imports_from_each_extracted_package(self):
        for feed, kodi_major in FEEDS:
            with self.subTest(feed=feed), tempfile.TemporaryDirectory() as directory:
                with zipfile.ZipFile(current_package(feed)) as archive:
                    archive.extractall(directory)
                code = """
import os, sys, traceback
try:
    import tests
    from kodienv import ENV
    ENV.infolabels['System.BuildVersion'] = '{major}.0 ({major}.0.0)'
    import lib.main
except BaseException:
    traceback.print_exc()
    sys.stderr.flush()
    os._exit(1)
print('PM4K main import passed', flush=True)
# The imported addon starts worker threads. This subprocess only tests imports,
# not Kodi's GUI or shutdown; the parent owns and removes its extracted files.
os._exit(0)
""".format(major=kodi_major)
                result = subprocess.run(
                    [sys.executable, "-B", "-c", code],
                    cwd=Path(directory) / "script.plexmod",
                    capture_output=True, text=True, timeout=30)
                self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
                self.assertIn("PM4K main import passed", result.stdout)


if __name__ == "__main__":
    unittest.main()
