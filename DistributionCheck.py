# -*- coding: utf-8 -*-
#############################################################################
# File          : DistributionCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 00:05:33 1999
# Version       : $Id$
# Purpose       : check the Distribution specificities in a binary rpm package.
#############################################################################

import re

import rpm

from Filter import addDetails, printWarning
import AbstractCheck
import Config


man_regex = re.compile("/man(?:\d[px]?|n)/")
info_regex = re.compile("(/usr/share|/usr)/info/")
vendor = Config.getOption("Vendor")
distribution = Config.getOption("Distribution")
use_bzip2 = Config.getOption("UseBzip2", True)
use_lzma = Config.getOption("UseLzma", False)
use_xz = Config.getOption("UseXz", False)

class DistributionCheck(AbstractCheck.AbstractCheck):


    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "DistributionCheck")

    def check(self, pkg):
        # Check only binary package
        if pkg.isSource():
            return

        if vendor and pkg[rpm.RPMTAG_VENDOR] != vendor:
            printWarning(pkg, "invalid-vendor", pkg[rpm.RPMTAG_VENDOR])

        if distribution and pkg[rpm.RPMTAG_DISTRIBUTION] != distribution:
            printWarning(pkg, "invalid-distribution", pkg[rpm.RPMTAG_DISTRIBUTION])

        for fname in pkg.files():

            if man_regex.search(fname):
                if use_bzip2:
                    if not fname.endswith('.bz2'):
                        printWarning(pkg, "manpage-not-compressed-with-bzip2",
                                     fname)
                elif use_lzma:
                    if not fname.endswith('.lzma'):
                        printWarning(pkg, "manpage-not-compressed-with-lzma",
                                     fname)
                elif use_xz:
                    if not fname.endswith('.xz'):
                        printWarning(pkg, "manpage-not-compressed-with-xz",
                                     fname)
                elif not fname.endswith('.gz'):
                    printWarning(pkg, "manpage-not-compressed-with-gzip",
                                 fname)

            if info_regex.search(fname) and not fname.endswith("/info/dir"):
                if use_bzip2:
                    if not fname.endswith('.bz2'):
                        printWarning(pkg, "infopage-not-compressed-with-bzip2",
                                     fname)
                elif use_lzma:
                    if not fname.endswith('.lzma'):
                        printWarning(pkg, "infopage-not-compressed-with-lzma",
                                     fname)
                elif use_xz:
                    if not fname.endswith('.xz'):
                        printWarning(pkg, "infopage-not-compressed-with-xz",
                                     fname)
                elif not fname.endswith('.gz'):
                    printWarning(pkg, "infopage-not-compressed-with-gzip",
                                 fname)

# Create an object to enable the auto registration of the test
check = DistributionCheck()

addDetails(
'invalid-vendor',
'In the ' + distribution + ' distribution, the vendor should be "' + vendor + '".',

'invalid-distribution',
'The distribution value should be "' + distribution + '".',
)

for compr in ('gzip', 'bzip2', 'lzma', 'xz'):
    addDetails('manpage-not-compressed-with-%s' % compr,
'''This manual page is not compressed with %s. If the compression does not
happen automatically when the package is rebuilt, make sure that you have the
appropriate rpm helper and/or config packages for your target distribution
installed and try rebuilding again; if it still does not happen automatically,
you can compress this file in the %%install section of the spec file.''' \
% compr)
    addDetails('infopage-not-compressed-with-%s' % compr,
'''This info page is not compressed with %s. If the compression does not happen
automatically when the package is rebuilt, make sure that you have the
appropriate rpm helper and/or config packages for your target distribution
installed and try rebuilding again; if it still does not happen automatically,
you can compress this file in the %%install section of the spec file.''' \
% compr)

# DistributionCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
