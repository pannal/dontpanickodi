""" 
    Put this script in the root folder of your repo and it will
    zip up all addon folders, create a new zip in your zips folder
    and then update the md5 and addons.xml file
"""

import re
import os
import shutil
import hashlib
import zipfile
import zlib
import sys
import tempfile
from xml.etree import ElementTree

KODI_VERSIONS = ["krypton", "leia", "matrix", "nexus", "omega", "repo"]
IGNORE = [
    ".git",
    ".github",
    ".gitignore",
    ".DS_Store",
    "thumbs.db",
    ".idea",
    "venv",
]

ADDON_RE = re.compile(r'(<addon id="(?!repository)(?P<id>.+?)".*?version="(?P<version>.+?)".*?</addon>)',
                      re.DOTALL | re.MULTILINE)


class Generator:
    """
    Generates a new addons.xml file from each addons addon.xml file
    and a new addons.xml.md5 hash file. Must be run from the root of
    the checked-out repo.
    """

    def __init__(self, release, onlyMD5=False):
        self.release_path = release
        self.zips_path = os.path.join(self.release_path, "zips")

        if not os.path.exists(self.zips_path):
            os.makedirs(self.zips_path)

        if not onlyMD5:
            self._remove_binaries()

            self._generate_addons_file(release)
        self._generate_md5_file()

    def _remove_binaries(self):
        """
        Removes any and all compiled Python files before operations.
        """

        for parent, dirnames, filenames in os.walk(self.release_path):
            for fn in filenames:
                if fn.lower().endswith("pyo") or fn.lower().endswith("pyc"):
                    compiled = os.path.join(parent, fn)
                    try:
                        os.remove(compiled)
                        print("Removed compiled python file:")
                        print(compiled)
                        print("-----------------------------")
                    except:
                        print("Failed to remove compiled python file:")
                        print(compiled)
                        print("-----------------------------")
            for dir in dirnames:
                if "pycache" in dir.lower():
                    compiled = os.path.join(parent, dir)
                    try:
                        shutil.rmtree(compiled)
                        print("Removed __pycache__ cache folder:")
                        print(compiled)
                        print("-----------------------------")
                    except:
                        print("Failed to remove __pycache__ cache folder:")
                        print(compiled)
                        print("-----------------------------")

    def _create_zip(self, addon_id, version):
        """
        Creates a zip file in the zips directory for the given addon.
        """
        addon_folder = os.path.join(self.release_path, addon_id)
        zip_folder = os.path.join(self.zips_path, addon_id)
        if not os.path.exists(zip_folder):
            os.makedirs(zip_folder)

        final_zip = os.path.join(zip_folder, "{0}-{1}.zip".format(addon_id, version))
        if not self._valid_zip(final_zip, addon_id, version):
            print("CREATING ZIP FOR: {0} - version={1}".format(addon_id, version))
            fd, temporary_zip = tempfile.mkstemp(dir=zip_folder, suffix=".tmp")
            os.close(fd)
            try:
                with zipfile.ZipFile(temporary_zip, "w", compression=zipfile.ZIP_DEFLATED) as archive:
                    for root, dirs, files in os.walk(addon_folder):
                        dirs[:] = [d for d in dirs if d not in IGNORE]
                        for filename in files:
                            if any(filename.startswith(i) for i in IGNORE):
                                continue
                            fullpath = os.path.join(root, filename)
                            archive_name = os.path.relpath(fullpath, self.release_path)
                            archive.write(fullpath, archive_name)
                if not self._valid_zip(temporary_zip, addon_id, version):
                    raise ValueError("Invalid generated archive: " + final_zip)
                os.replace(temporary_zip, final_zip)
            finally:
                if os.path.exists(temporary_zip):
                    os.remove(temporary_zip)

    @staticmethod
    def _valid_zip(path, addon_id, version):
        """Only reuse complete archives containing the expected addon manifest."""
        try:
            with zipfile.ZipFile(path) as archive:
                manifest = ElementTree.fromstring(archive.read(addon_id + "/addon.xml"))
                return (manifest.get("id") == addon_id
                        and manifest.get("version") == version
                        and archive.testzip() is None)
        except (OSError, zipfile.BadZipFile, zlib.error, KeyError, ElementTree.ParseError, RuntimeError, EOFError):
            return False

    def _copy_meta_files(self, addon_id, addon_folder):
        """
        Copy the addon.xml and relevant art files into the relevant folders in the repository.
        """

        tree = ElementTree.parse(os.path.join(self.release_path, addon_id, "addon.xml"))
        root = tree.getroot()

        copyfiles = ["addon.xml"]
        for ext in root.findall("extension"):
            if ext.get("point") in ["xbmc.addon.metadata", "kodi.addon.metadata"]:
                assets = ext.find("assets")
                if not assets:
                    continue
                for art in [a for a in assets if a.text]:
                    copyfiles.append(os.path.normpath(art.text))

        src_folder = os.path.join(self.release_path, addon_id)
        for file in copyfiles:
            addon_path = os.path.join(src_folder, file)
            zips_path = os.path.join(addon_folder, file)
            asset_path = os.path.split(zips_path)[0]
            if not os.path.exists(asset_path):
                os.makedirs(asset_path)

            shutil.copy(addon_path, zips_path)

    def _get_existing_versions(self):
        try:
            addons_xml = os.path.join(self.zips_path, "addons.xml")
            with open(addons_xml, encoding="utf-8") as source:
                return ADDON_RE.findall(source.read())
        except IOError:
            return {}

    def _generate_addons_file(self, release_name):
        """
        Generates a zip for each found addon, and updates the addons.xml file accordingly.
        """
        addons_xml = '<?xml version="1.0" encoding="UTF-8"?>\n<addons>\n'

        folders = [
            i
            for i in os.listdir(self.release_path)
            if os.path.isdir(os.path.join(self.release_path, i))
            and i != "zips"
            and not i.startswith(".")
            and os.path.exists(os.path.join(self.release_path, i, "addon.xml"))
        ]

        existing_addons = self._get_existing_versions()
        versions_seen = {}

        for addon in folders:
            try:
                _path = os.path.join(self.release_path, addon, "addon.xml")
                with open(_path, "r", encoding="utf-8") as source:
                    xml_lines = source.read().splitlines()
                addon_xml = ""
                version = None

                # loop thru cleaning each line
                ver_found = False
                for line in xml_lines:
                    if line.find("<?xml") >= 0:
                        continue
                    if 'version="' in line and not ver_found:
                        version = re.compile('version="(.+?)"').findall(line)[0]
                        ver_found = True
                    addon_xml += line.rstrip() + "\n"
                addons_xml += addon_xml.rstrip() + "\n\n"

                if version:
                    versions_seen[addon] = version

                # Create the zip files
                self._create_zip(addon, version)
                self._copy_meta_files(addon, os.path.join(self.zips_path, addon))
            except Exception as e:
                raise RuntimeError("Failed to generate {0}: {1}".format(_path, e)) from e

        # clean and add closing tag
        addons_xml = addons_xml.strip()

        # add old addons
        for addon_xml, addon_id, version in existing_addons:
            if addon_id in versions_seen and version != versions_seen[addon_id] \
                    and os.path.exists(os.path.join(self.zips_path, addon_id, "{0}-{1}.zip".format(addon_id, version))):
                print("Adding known addon: {}/{}:{}".format(release_name, addon_id, version))
                addons_xml += "\n\n" + addon_xml.rstrip()

        addons_xml += "\n</addons>\n"
        self._save_file(
            addons_xml.encode("utf-8"),
            file=os.path.join(self.zips_path, "addons.xml"),
            decode=True,
        )
        print("Successfully updated {}/addons.xml".format(release_name))

    def _generate_md5_file(self):
        """
        Generates a new addons.xml.md5 file.
        """
        with open(os.path.join(self.zips_path, "addons.xml"), "rb") as source:
            m = hashlib.md5(source.read()).hexdigest()
        self._save_file(m, file=os.path.join(self.zips_path, "addons.xml.md5"))
        print("Successfully updated addons.xml.md5")

    def _save_file(self, data, file, decode=False):
        """Atomically save exact bytes, preserving LF on every operating system."""
        if isinstance(data, str):
            data = data.encode("utf-8")
        fd, temporary_file = tempfile.mkstemp(dir=os.path.dirname(file), suffix=".tmp")
        try:
            with os.fdopen(fd, "wb") as output:
                output.write(data)
            os.replace(temporary_file, file)
        finally:
            if os.path.exists(temporary_file):
                os.remove(temporary_file)


if __name__ == "__main__":
    onlyMD5 = len(sys.argv) > 1 and sys.argv[1] == "md5"
    for release in [r for r in KODI_VERSIONS if os.path.exists(r)]:
        Generator(release, onlyMD5=onlyMD5)
