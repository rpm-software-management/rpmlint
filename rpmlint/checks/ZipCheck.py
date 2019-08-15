import os
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
        for fname, pkgfile in pkg.files().items():
            path = pkgfile.path
            if self.zip_regex.search(fname) and os.path.exists(path) and \
               os.path.isfile(path) and is_zipfile(path):
                try:
                    with ZipFile(path, 'r') as z:
                        # Check CRC issues
                        badcrc = z.testzip()
                        if badcrc:
                            self.output.add_info('E', pkg, 'bad-crc-in-zip', badcrc, fname)
                        # Check compression
                        if not self._check_compression(z):
                            self.output.add_info('E', pkg, 'uncompressed-zip', fname)

                        # additional jar checks
                        if self.jar_regex.search(fname):
                            if self._check_classpath(z):
                                self.output.add_info('W', pkg, 'class-path-in-manifest', fname)
                            if self._check_jarindex(z):
                                self.output.add_info('W', pkg, 'jar-not-indexed', fname)
                except BadZipFile as err:
                    self.output.add_info('E', pkg, 'unable-to-read-zip', f'{fname}: {err}')
                except RuntimeError as err:
                    self.output.add_info('W', pkg, 'unable-to-read-zip', f'{fname}: {err}')

    @staticmethod
    def _check_compression(zipfile):
        """
        Check if zip is actually compressed.
        One file with smaller size is enough.
        """
        # check for empty archives which are walid
        filecount = len(zipfile.namelist())
        nullcount = 0
        for zinfo in zipfile.infolist():
            if zinfo.file_size == 0:
                nullcount += 1
            if zinfo.compress_size != zinfo.file_size:
                return True
        # empty files only
        if filecount == nullcount:
            return True
        return False

    @staticmethod
    def _check_classpath(zipfile):
        """
        Check if package contains MANIFEST.MF without classpath
        """
        classpath_regex = re.compile(r'^\s*Class-Path\s*:', re.MULTILINE | re.IGNORECASE)

        mf = 'META-INF/MANIFEST.MF'
        # The META-INF is optional so skip if it is not present
        if mf not in zipfile.namelist():
            return False
        # otherwise check for the classpath
        manifest = zipfile.read(mf).decode()
        if classpath_regex.search(manifest):
            return True
        return False

    @staticmethod
    def _check_jarindex(zipfile):
        """
        Check if there is index in the jar
        """
        mf = 'META-INF/MANIFEST.MF'
        # The META-INF is optional so skip if it is not present
        if mf not in zipfile.namelist():
            return True
        # otherwise we have to have index
        index = 'META-INF/INDEX.LIST'
        if index not in zipfile.namelist():
            return False
        return True
