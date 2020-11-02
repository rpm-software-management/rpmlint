import re
import stat

from rpmlint.checks.AbstractCheck import AbstractFilesCheck


class PkgConfigCheck(AbstractFilesCheck):
    """
    Validate that .pc files are correct.
    """
    suspicious_dir = re.compile(r'[=:](?:/usr/src/\w+/BUILD|/var/tmp|/tmp|/home)')

    def __init__(self, config, output):
        super().__init__(config, output, r'.*/pkgconfig/.*\.pc$')

    def check(self, pkg):
        # check for references to /lib when in lib64 mode and vice versa
        if pkg.arch in ('x86_64', 'ppc64', 's390x', 'aarch64'):
            self.wronglib_dir = re.compile(r'-L/usr/lib\b')
        else:
            self.wronglib_dir = re.compile(r'-L/usr/lib64\b')

        AbstractFilesCheck.check(self, pkg)

    def check_file(self, pkg, filename):
        if pkg.is_source or not stat.S_ISREG(pkg.files[filename].mode):
            return

        try:
            with open(pkg.dirName() + '/' + filename, 'r', encoding='utf-8') as pc_file:
                for line in pc_file:
                    self._check_invalid_pkgconfig_file(pkg, filename, line)
                    self._check_invalid_libs_dir(pkg, filename, line)
                    self._check_double_slash(pkg, filename, line)
        except Exception as e:
            self.output.add_info('E', pkg, 'pkgconfig-exception', filename, str(e))

    def _check_invalid_pkgconfig_file(self, pkg, filename, line):
        """
        Check that .pc file is valid (it runs various checks).

        E.g. it doesn't contain traces of $RPM_BUILD_ROOT or $RPM_BUILD_DIR,
        unreplaced macros or invalid paths.
        """
        if self.suspicious_dir.search(line):
            self.output.add_info('E', pkg, 'invalid-pkgconfig-file', filename)

    def _check_invalid_libs_dir(self, pkg, filename, line):
        """
        Check that .pc file contains correct libs dir based on the build
        target (32-bit, 64-bit).

        That means:
         -L/usr/lib or -L/lib for 32-bit,
         -L/usr/lib64 or -L/lib64 for 64-bit
        """
        if line.startswith('Libs:') and self.wronglib_dir.search(line):
            self.output.add_info('E', pkg, 'pkgconfig-invalid-libs-dir', filename, line.rstrip())

    def _check_double_slash(self, pkg, filename, line):
        """
        Check that .pc file doesn't contain a path with a double slash ('//')
        """
        if '//' in line and '://' not in line:
            self.output.add_info('E', pkg, 'double-slash-in-pkgconfig-path', filename, line.rstrip())
