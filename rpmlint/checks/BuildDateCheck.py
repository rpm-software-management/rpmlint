import re
import stat
import time

from rpmlint.checks.AbstractCheck import AbstractFilesCheck


class BuildDateCheck(AbstractFilesCheck):
    """
    Check that the file doesn't contain the current date or time.

    If so, it causes the package to rebuild when it's not needed.
    """
    def __init__(self, config, output):
        super().__init__(config, output, r'.*')
        self.looksliketime = re.compile('(2[0-3]|[01]?[0-9]):([0-5]?[0-9]):([0-5]?[0-9])')
        self.istoday = re.compile(time.strftime('%b %e %Y'))

    def check_file(self, pkg, filename):
        if filename.startswith('/usr/lib/debug') or pkg.is_source or \
                not stat.S_ISREG(pkg.files[filename].mode):
            return

        grep_date = pkg.grep(self.istoday, filename)

        if len(grep_date):
            grep_time = pkg.grep(self.looksliketime, filename)

            if len(grep_time):
                self.output.add_info('E', pkg, 'file-contains-date-and-time', filename)
            else:
                self.output.add_info('E', pkg, 'file-contains-current-date', filename)
