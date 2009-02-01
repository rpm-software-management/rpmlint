# -*- coding: utf-8 -*-
#############################################################################
# File          : SourceCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Wed Oct 27 21:17:03 1999
# Version       : $Id$
# Purpose       : verify source package correctness.
#############################################################################

import re

from Filter import addDetails, printError, printWarning
import AbstractCheck
import Config


DEFAULT_VALID_SRC_PERMS = (0644, 0755)

source_regex = re.compile('\\.(tar|patch|tgz|diff)$')
use_bzip2 = Config.getOption('UseBzip2', 1)
valid_src_perms = Config.getOption("ValidSrcPerms", DEFAULT_VALID_SRC_PERMS)

class SourceCheck(AbstractCheck.AbstractCheck):


    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'SourceCheck')

    def check(self, pkg):
        # Check only source package
        if not pkg.isSource():
            return

        # process file list
        spec_file = None
        for fname, pkgfile in pkg.files().items():
            if fname.endswith('.spec'):
                if spec_file:
                    printError(pkg, 'multiple-specfiles', spec_file, fname)
                else:
                    spec_file = fname
            elif source_regex.search(fname):
                if use_bzip2:
                    if not fname.endswith('.bz2'):
                        printWarning(pkg, 'source-or-patch-not-bzipped', fname)
                else:
                    if not fname.endswith('gz'):
                        printWarning(pkg, 'source-or-patch-not-gzipped', fname)
            perm = pkgfile.mode & 07777
            if perm not in valid_src_perms:
                printWarning(pkg, 'strange-permission', fname, oct(perm))

check = SourceCheck()

addDetails(
'multiple-specfiles',
'''Your package contains multiple spec files. To build a
correct package, you need to have only one spec file containing
all your RPM information.''',

'source-or-patch-not-bzipped',
'''A source archive or file in your package is not bzipped (doesn't
have the .bz2 extension). To bzip it, use bzip2.''',

'source-or-patch-not-gzipped',
'''A source archive or file in your package is not gzipped (doesn't
have the .gz extension). To gzip it, use the gzip command.''',

'strange-permission',
'''A file that you listed to include in your package has strange
permissions. Usually, a file should have 0644 permissions.''',

)

# SourceCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
