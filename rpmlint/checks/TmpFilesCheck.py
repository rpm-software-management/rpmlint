from pathlib import Path
import re
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck


class TmpFilesCheck(AbstractCheck):
    """
    Validate that temporary files meet tmpfiles.d packaging rules.
    """

    # interesting types in tmpfiles.d configuration file (see tmpfiles.d(5))
    interesting_types = ('f', 'F', 'w', 'd', 'D', 'p', 'L', 'c', 'b')

    def check(self, pkg):
        if pkg.is_source:
            return

        for fname, pkgfile in pkg.files.items():
            if not fname.startswith('/usr/lib/tmpfiles.d/'):
                continue
            if not stat.S_ISREG(pkgfile.mode):
                self.output.add_info('W', pkg, 'tmpfile-not-regular-file',
                                     fname)
                continue

            if pkgfile.is_ghost:
                continue

            self._check_pre_tmpfile(fname, pkg)
            self._check_post_tmpfile(fname, pkg)
            self._check_tmpfile_in_filelist(pkgfile, pkg)

    def _check_pre_tmpfile(self, fname, pkg):
        """
        Check if the %pre section doesn't contain 'systemd-tmpfiles --create'
        call.

        Print a warning if there is systemd-tmpfiles call in the %pre section.
        """
        pre = pkg[rpm.RPMTAG_PREIN]

        basename = Path(fname).name
        tmpfiles_regex = re.compile(r'systemd-tmpfiles --create .*%s'
                                    % re.escape(basename))

        if pre and tmpfiles_regex.search(pre):
            self.output.add_info('W', pkg, 'pre-with-tmpfile-creation', fname)

    def _check_post_tmpfile(self, fname, pkg):
        """
        Check if the %post section contains 'systemd-tmpfiles --create' call.

        Print a warning if there is no such call in the %post section.
        """
        post = pkg[rpm.RPMTAG_POSTIN]

        basename = Path(fname).name
        tmpfiles_regex = re.compile(r'systemd-tmpfiles --create .*%s'
                                    % re.escape(basename))

        if post and tmpfiles_regex.search(post):
            return
        self.output.add_info('W', pkg, 'post-without-tmpfile-creation', fname)

    def _check_tmpfile_in_filelist(self, pkgfile, pkg):
        """
        Check if the tmpfile is listed in the filelist and marked as %ghost.

        Please note that a tmpfile that doesn't exist during the build can't
        be in the filelist without %ghost directive otherwise rpm wouldn't
        build it.

        Print a 'tmpfile-not-in-filelist' warning while it's not in the
        filelist (and therefore not marked as %ghost).
        """
        with open(pkgfile.path) as inputf:
            for line in inputf:
                # skip comments
                line = line.split('#')[0].split('\n')[0]
                line = line.lstrip()
                if not len(line):
                    continue

                # the format is:
                # Type Path Mode UID  GID  Age Argument
                line = re.split(r'\s+', line)
                if len(line) < 3:
                    continue
                # we only need Type and Path
                tmpfiles_type = line[0]
                tmpfiles_path = line[1]
                if tmpfiles_type.endswith('!'):
                    tmpfiles_type = tmpfiles_type[:-1]
                if tmpfiles_type not in self.interesting_types:
                    continue

                if tmpfiles_path not in pkg.files:
                    self.output.add_info('W', pkg, 'tmpfile-not-in-filelist',
                                         tmpfiles_path)
