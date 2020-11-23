import stat
import subprocess

from rpmlint.checks.AbstractCheck import AbstractFilesCheck
from rpmlint.helpers import ENGLISH_ENVIROMENT


class BashismsCheck(AbstractFilesCheck):
    def __init__(self, config, output):
        super().__init__(config, output, r'.*')
        self.use_threads = True
        self._detect_early_fail_option()

    def _detect_early_fail_option(self):
        self.has_early_fail_option = False
        output = subprocess.check_output(['checkbashisms', '--help'],
                                         shell=True, encoding='utf8')
        # FIXME: remove in the future
        self.use_early_fail = '[-e]' in output

    def check_file(self, pkg, filename):
        root = pkg.dirName()
        pkgfile = pkg.files[filename]
        filepath = root + filename

        # We only care about the real files that state they are shell scripts
        if not (stat.S_ISREG(pkgfile.mode) and
                pkgfile.magic.startswith('POSIX shell script')):
            return

        self.check_bashisms(pkg, filepath, filename)

    def check_bashisms(self, pkg, filepath, filename):
        """
        Run dash and then checkbashism on file

        We need to see if it is valid syntax of bash and if there are no
        potential bash issues.
        """
        try:
            r = subprocess.run(['dash', '-n', filepath],
                               stderr=subprocess.DEVNULL,
                               env=ENGLISH_ENVIROMENT)
            if r.returncode == 2:
                self.output.add_info('W', pkg, 'bin-sh-syntax-error', filename)
            elif r.returncode == 127:
                raise FileNotFoundError(filename)
        except UnicodeDecodeError:
            pass

        try:
            cmd = ['checkbashisms', filepath]
            # --early-fail option can rapidly speed up the check
            if self.use_early_fail:
                cmd.append('-e')
            r = subprocess.run(cmd,
                               stderr=subprocess.DEVNULL,
                               env=ENGLISH_ENVIROMENT)
            if r.returncode == 1:
                self.output.add_info('W', pkg, 'potential-bashisms', filename)
            elif r.returncode == 2:
                raise FileNotFoundError(filename)
        except UnicodeDecodeError:
            pass
