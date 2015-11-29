# -*- coding: utf-8 -*-
#############################################################################
# File          : SourceCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Wed Oct 27 21:17:03 1999
# Purpose       : verify source package correctness.
#############################################################################

import re

from Filter import addDetails, printError, printWarning
import AbstractCheck
import Config


DEFAULT_VALID_SRC_PERMS = (int("644", 8), int("755", 8))

source_regex = re.compile('\\.(tar|patch|tgz|diff)$')
compress_ext = Config.getOption("CompressExtension", "bz2")
valid_src_perms = Config.getOption("ValidSrcPerms", DEFAULT_VALID_SRC_PERMS)


class SourceCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'SourceCheck')

    def check_source(self, pkg):
        # process file list
        spec_file = None
        for fname, pkgfile in pkg.files().items():
            if fname.endswith('.spec'):
                if spec_file:
                    printError(pkg, 'multiple-specfiles', spec_file, fname)
                else:
                    spec_file = fname
            elif source_regex.search(fname) and compress_ext and \
                    not fname.endswith(compress_ext):
                printWarning(pkg, 'source-or-patch-not-compressed',
                             compress_ext, fname)
            perm = pkgfile.mode & int("7777", 8)
            if perm not in valid_src_perms:
                printWarning(pkg, 'strange-permission', fname, "%o" % perm)

check = SourceCheck()

addDetails(
'multiple-specfiles',
'''Your package contains multiple spec files. To build a
correct package, you need to have only one spec file containing
all your RPM information.''',

'source-or-patch-not-compressed',
'''A source archive or file in your package is not compressed using the %s
compression method (doesn't have the %s extension).''' %
(compress_ext, compress_ext),

'strange-permission',
'''A file that you listed to include in your package has strange
permissions. Usually, a file should have 0644 permissions.''',

)

# SourceCheck.py ends here

# ex: ts=4 sw=4 et
