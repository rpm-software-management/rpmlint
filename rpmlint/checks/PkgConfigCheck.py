import re
import stat

from rpmlint.checks.AbstractCheck import AbstractFilesCheck


class PkgConfigCheck(AbstractFilesCheck):
    suspicious_dir = re.compile(r'[=:](?:/usr/src/\w+/BUILD|/var/tmp|/tmp|/home)')

    def __init__(self, config, output):
        super().__init__(config, output, r'.*/pkgconfig/.*\.pc$')

    def check(self, pkg):
        # check for references to /lib when in lib64 mode
        if pkg.arch in ('x86_64', 'ppc64', 's390x', 'aarch64'):
            self.wronglib_dir = re.compile(r'-L/usr/lib\b')
        else:
            self.wronglib_dir = re.compile(r'-L/usr/lib64\b')

        AbstractFilesCheck.check(self, pkg)

    def check_file(self, pkg, filename):
        if pkg.isSource() or not stat.S_ISREG(pkg.files()[filename].mode):
            return

        if pkg.grep(self.suspicious_dir, filename):
            self.output.add_info('E', pkg, 'invalid-pkgconfig-file', filename)

        try:
            pc_file = open(pkg.dirName() + '/' + filename, 'r', encoding='utf-8')
            for l in pc_file:
                if l.startswith('Libs:') and self.wronglib_dir.search(l):
                    self.output.add_info('E', pkg, 'pkgconfig-invalid-libs-dir', filename, l)
                if '//' in l and '://' not in l:
                    self.output.add_info('E', pkg, 'double-slash-in-pkgconfig-path', filename, l)
        except Exception as e:
            self.output.add_info('E', pkg, 'pkgconfig-exception', filename, str(e))
