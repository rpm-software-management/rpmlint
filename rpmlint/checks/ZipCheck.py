from pathlib import Path
import re
from zipfile import BadZipFile, is_zipfile, ZipFile

from rpmlint.checks.AbstractCheck import AbstractCheck


class ZipCheck(AbstractCheck):
    """
    Validate zip and jar files correctness.
    """
    zip_regex = re.compile(r'\.(zip|[ewj]ar)$')
    jar_regex = re.compile(r'\.[ewj]ar$')

    def check(self, pkg):
        for fname, pkgfile in pkg.files.items():
            path = pkgfile.path
            if self.zip_regex.search(fname) and Path(path).exists() and \
               Path(path).is_file() and is_zipfile(path):
                try:
                    with ZipFile(path, 'r') as z:
                        # zip checks
                        self._check_bad_crc(pkg, fname, z)
                        self._check_compression(pkg, fname, z)

                        # jar checks
                        if self.jar_regex.search(fname):
                            self._check_classpath(pkg, fname, z)
                            self._check_jarindex(pkg, fname, z)
                except BadZipFile as err:
                    self.output.add_info('E', pkg, 'unable-to-read-zip', f'{fname}: {err}')
                except RuntimeError as err:
                    self.output.add_info('W', pkg, 'unable-to-read-zip', f'{fname}: {err}')

    def _check_bad_crc(self, pkg, fname, zipfile):
        """
        Check CRC issues for the files in the zipfile.

        Print an error if there is a file in the archive that fails CRC check.
        """
        badcrc = zipfile.testzip()
        if badcrc:
            self.output.add_info('E', pkg, 'bad-crc-in-zip', badcrc, fname)

    def _check_compression(self, pkg, fname, zipfile):
        """
        Check if zip is actually compressed or not.

        One file with smaller size is enough. Print an error if the zipfile
        is not compressed.
        """
        # check for empty archives which are valid
        filecount = len(zipfile.namelist())
        nullcount = 0
        for zinfo in zipfile.infolist():
            if zinfo.file_size == 0:
                nullcount += 1
            if zinfo.compress_size != zinfo.file_size:
                return

        # empty files only
        if filecount == nullcount:
            return
        self.output.add_info('E', pkg, 'uncompressed-zip', fname)

    def _check_classpath(self, pkg, fname, jarfile):
        """
        Check if META-INF/MANIFEST.MF file in the jar contains a hardcoded
        Class-Path.

        Print a warning if the path is hardcoded.
        """
        classpath_regex = re.compile(r'^\s*Class-Path\s*:', re.MULTILINE | re.IGNORECASE)

        # the META-INF is optional so skip if it is not present
        mf = 'META-INF/MANIFEST.MF'
        if mf not in jarfile.namelist():
            return

        # otherwise check for the hardcoded classpath
        manifest = jarfile.read(mf).decode()
        if classpath_regex.search(manifest):
            self.output.add_info('W', pkg, 'class-path-in-manifest', fname)

    def _check_jarindex(self, pkg, fname, jarfile):
        """
        Check if the .jar file is indexed.

        Print a warning if 'META-INF/INDEX.LIST' file is not present in the
        jarfile.
        """
        index = 'META-INF/INDEX.LIST'
        if index not in jarfile.namelist():
            self.output.add_info('W', pkg, 'jar-not-indexed', fname)
