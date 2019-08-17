import re

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck


class LSBCheck(AbstractCheck):
    """
    Validate that package name, version and release number are LSB compliant.

    The rules are the intersection of compatible NVRs between RPM v3 and DPKG
    for supporting portability across RPM and Debian systems through tools
    like alien.

    Note: It uses values gained from rpm (RPMTAGs) not parsed from .rpm
    filename.
    """
    name_regex = re.compile('^[a-z0-9.+-]+$')
    version_regex = re.compile('^[a-zA-Z0-9.+]+$')

    def check(self, pkg):
        self._check_lsb_name(pkg)
        self._check_lsb_version(pkg)
        self._check_lsb_release(pkg)

    def _check_lsb_name(self, pkg):
        """
        Check if the package name is LSB compliant (only lowercase
        letters, numbers, '.', '+' or '-' characters).
        """
        name = pkg.name
        if name and not self.name_regex.search(name):
            self.output.add_info('E', pkg, 'non-lsb-compliant-package-name', pkg.name)

    def _check_lsb_version(self, pkg):
        """
        Check if the package version number is LSB compliant (only alphanumeric
        symbols, '.' or '+' characters).
        """
        version = pkg[rpm.RPMTAG_VERSION]
        if version and not self.version_regex.search(version):
            self.output.add_info('E', pkg, 'non-lsb-compliant-version', pkg[rpm.RPMTAG_VERSION])

    def _check_lsb_release(self, pkg):
        """
        Check if the package release number is LSB compliant (only alphanumeric
        symbols, '.' or '+' characters).
        """
        release = pkg[rpm.RPMTAG_RELEASE]
        if release and not self.version_regex.search(release):
            self.output.add_info('E', pkg, 'non-lsb-compliant-release', pkg[rpm.RPMTAG_RELEASE])
