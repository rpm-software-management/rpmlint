import re
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractFilesCheck


class BuildRootCheck(AbstractFilesCheck):
    def __init__(self, config, output):
        super().__init__(config, output, r'.*')
        self.prepare_regex(rpm.expandMacro('%buildroot'))

    def prepare_regex(self, buildroot):
        for m in ('name', 'version', 'release', 'NAME', 'VERSION', 'RELEASE'):
            buildroot = buildroot.replace('%%{%s}' % (m), r'[\w\!-\.]{1,20}')
        self.build_root_re = re.compile(buildroot)

    def check_file(self, pkg, filename):
        if filename.startswith('/usr/lib/debug') or pkg.is_source:
            return
        if not stat.S_ISREG(pkg.files[filename].mode):
            return

        if pkg.grep(self.build_root_re, filename):
            self.output.add_info('E', pkg, 'file-contains-buildroot', filename)
