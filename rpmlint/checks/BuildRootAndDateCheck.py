import re
import stat
import time

import rpm
from rpmlint.checks.AbstractCheck import AbstractFilesCheck


class BuildRootAndDateCheck(AbstractFilesCheck):
    """
    Check that the file doesn't contain the current date or time.
    And check the file does not contain build root reference.

    If so, it causes the package to rebuild when it's not needed.
    """
    def __init__(self, config, output):
        super().__init__(config, output, r'.*')
        self.looksliketime = re.compile('(2[0-3]|[01]?[0-9]):([0-5]?[0-9]):([0-5]?[0-9])')
        self.istoday = re.compile(time.strftime('%b %e %Y'))
        self.prepare_regex(rpm.expandMacro('%{?buildroot}') or '^/.*/BUILDROOT/')

    def prepare_regex(self, buildroot):
        for m in ('name', 'version', 'release', 'NAME', 'VERSION', 'RELEASE'):
            buildroot = buildroot.replace('%%{%s}' % (m), r'[\w\!-\.]{1,20}')
        self.build_root_re = re.compile(buildroot)

    def check_file(self, pkg, filename):
        if filename.startswith('/usr/lib/debug') or pkg.is_source or \
                not stat.S_ISREG(pkg.files[filename].mode):
            return

        data = pkg.read_with_mmap(filename)
        if self.istoday.search(data):
            if self.looksliketime.search(data):
                self.output.add_info('E', pkg, 'file-contains-date-and-time', filename)
            else:
                self.output.add_info('E', pkg, 'file-contains-current-date', filename)
        if self.build_root_re.search(data):
            self.output.add_info('E', pkg, 'file-contains-buildroot', filename)
