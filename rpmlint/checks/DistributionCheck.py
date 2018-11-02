#############################################################################
# File          : DistributionCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 00:05:33 1999
# Purpose       : check the Distribution specificities in a binary rpm package.
#############################################################################

import re

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck


class DistributionCheck(AbstractCheck):

    def __init__(self, config, output):
        super().__init__(config, output)
        self.man_regex = re.compile(r'/man(?:\d[px]?|n)/')
        self.info_regex = re.compile(r'(/usr/share|/usr)/info/')
        self.vendor = self.config.configuration['Vendor']
        self.distribution = self.config.configuration['Distribution']
        self.compress_ext = self.config.configuration['CompressExtension']
        distribution_details_dict = {
            'invalid-vendor':
            "In the '%s' distribution, vendor should be '%s'." % (self.distribution, self.vendor),

            'invalid-distribution':
            'The distribution value should be '' + self.distribution + ''.',

            'manpage-not-compressed':
            """This manual page is not compressed with the %s compression method
            (does not have the %s extension). If the compression does not happen
            automatically when the package is rebuilt, make sure that you have the
            appropriate rpm helper and/or config packages for your target distribution
            installed and try rebuilding again; if it still does not happen automatically,
            you can compress this file in the %%install section of the spec file."""
            % (self.compress_ext, self.compress_ext),

            'infopage-not-compressed':
            """This info page is not compressed with the %s compression method
            (does not have the %s extension). If the compression does not happen
            automatically when the package is rebuilt, make sure that you have the
            appropriate rpm helper and/or config packages for your target distribution
            installed and try rebuilding again; if it still does not happen automatically,
            you can compress this file in the %%install section of the spec file."""
            % (self.compress_ext, self.compress_ext),
        }
        self.output.error_details.update(distribution_details_dict)

    def check_binary(self, pkg):
        if self.vendor and pkg[rpm.RPMTAG_VENDOR] != self.vendor:
            self.output.add_info('W', pkg, 'invalid-vendor', pkg[rpm.RPMTAG_VENDOR])

        if self.distribution and pkg[rpm.RPMTAG_DISTRIBUTION] != self.distribution:
            self.output.add_info('W', pkg, 'invalid-distribution', pkg[rpm.RPMTAG_DISTRIBUTION])

        if self.compress_ext:
            for fname in pkg.files():
                if self.man_regex.search(fname):
                    if not fname.endswith(self.compress_ext):
                        self.output.add_info('W', pkg, 'manpage-not-compressed',
                                             self.compress_ext, fname)
                elif self.info_regex.search(fname) and \
                        not fname.endswith('/info/dir'):
                    if not fname.endswith(self.compress_ext):
                        self.output.add_info('W', pkg, 'infopage-not-compressed',
                                             self.compress_ext, fname)
