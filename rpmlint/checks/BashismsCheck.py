import stat
import subprocess

from rpmlint.checks.AbstractCheck import AbstractFilesCheck


class BashismsCheck(AbstractFilesCheck):
    def __init__(self, config, output):
        super().__init__(config, output, r'.*')

    def check_file(self, pkg, filename):
        root = pkg.dirName()
        pkgfile = pkg.files()[filename]
        fullpath = root + filename

        if not (stat.S_ISREG(pkgfile.mode) and
                pkgfile.magic.startswith('POSIX shell script')):
            return

        try:
            r = subprocess.run(['dash', '-n', fullpath],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r.returncode == 2:
                self.output.add_info('W', pkg, 'bin-sh-syntax-error', filename)

            r = subprocess.run(['checkbashisms', fullpath],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if r.returncode == 1:
                self.output.add_info('W', pkg, 'potential-bashisms', filename)
        except (FileNotFoundError, UnicodeDecodeError):
            pass
