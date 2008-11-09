#############################################################################
# File          : DistributionCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 00:05:33 1999
# Version       : $Id$
# Purpose       : check the Distribution specificities in a binary rpm package.
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import re
import Config

man_regex = re.compile("/man(?:\d[px]?|n)/")
info_regex = re.compile("(/usr/share|/usr)/info/")
info_dir_regex = re.compile("/info/dir$")
vendor = Config.getOption("Vendor")
distribution = Config.getOption("Distribution")
use_bzip2 = Config.getOption("UseBzip2", 1)
use_lzma = Config.getOption("UseLzma", 0)

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

        for f in pkg.files().keys():
            if man_regex.search(f):
                if use_bzip2:
                    if not f.endswith('.bz2'):
                        printWarning(pkg, "manpage-not-bzipped", f)
                if use_lzma:
                    if not f.endswith('.lzma'):
                        printWarning(pkg, "manpage-not-compressed-wth-lzma", f)

                elif not f.endswith('.gz'):
                    printWarning(pkg, "manpage-not-gzipped", f)
            if info_regex.search(f) and not info_dir_regex.search(f):
                if use_bzip2:
                    if not f.endswith('.bz2'):
                        printWarning(pkg, "infopage-not-bzipped", f)
                if use_lzma:
                    if not f.endswith('.lzma'):
                        printWarning(pkg, "infopage-not-compressed-wth-lzma", f)
                elif not f.endswith('.gz'):
                    printWarning(pkg, "infopage-not-gzipped", f)

# Create an object to enable the auto registration of the test
check = DistributionCheck()

if Config.info:
    addDetails(
'invalid-vendor',
'In the ' + distribution + ' distribution, the vendor should be "' + vendor + '".',

'invalid-distribution',
'The distribution value should be "' + distribution + '".',

'manpage-not-compressed-with-lzma',
'''Manual Pages are not compressed using the .lzma extension/format. Please
run lzma <man page file> to compress it in the %install section and
rebuild the package. You can also use the spec-helper package
that automates this task.''',

'manpage-not-bzipped',
'''Manual Pages are not compressed using the .bz2 extension/format. Please
run bzip2 <man page file> to bzip it in the %install section and
rebuild the package. You can also use the spec-helper package
that automates this task.''',

'manpage-not-gzipped',
'''Manual Pages are not compressed using the .gz extension/format. Please
run gzip <man page file> to gzip it in the %install section and rebuild the
package.''',

'infopage-not-compressed-with-lzma',
'''An info page are not compressed using the .lzma extension/format. Please
run lzma <info page file> to compress it in the %install section and
rebuild the package. You can also use the spec-helper package
that automates this task.''',

'infopage-not-bzipped',
'''An info page is not compressed using the .bz2 extension/format. Please
run bzip2 <info page file> to bzip it in the %install section and rebuild the
package. You can also use the spec-helper package that automates this task.''',

'infopage-not-gzipped',
'''An info page is not compressed using the .gz extension/format. Please
run gzip <info page file> to gzip it in the %install section and rebuild the
package.''',

)

# DistributionCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
