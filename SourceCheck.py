#############################################################################
# File          : SourceCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Wed Oct 27 21:17:03 1999
# Version       : $Id$
# Purpose       : verify source package correctness.
#############################################################################

from Filter import *
import AbstractCheck
import re
import Config

DEFAULT_VALID_SRC_PERMS=(0644, 0755)

spec_regex=re.compile('.spec$')
bz2_regex=re.compile('.bz2$')
gz_regex=re.compile('gz$')
source_regex=re.compile('\\.(tar|patch|tgz|diff)$')
use_bzip2=Config.getOption('UseBzip2', 1)
valid_src_perms=Config.getOption("ValidSrcPerms", DEFAULT_VALID_SRC_PERMS)

class SourceCheck(AbstractCheck.AbstractCheck):


    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'SourceCheck')

    def check(self, pkg):
        # Check only source package
        if not pkg.isSource():
            return

        # process file list
        files=pkg.files()
        spec_file=None
        for f in files.keys():
            if spec_regex.search(f):
                if spec_file:
                    printError(pkg, 'multiple-specfiles', spec_file, f)
                else:
                    spec_file=f
            elif source_regex.search(f):
                if use_bzip2:
                    if not bz2_regex.search(f):
                        printWarning(pkg, 'source-or-patch-not-bzipped', f)
                else:
                    if not gz_regex.search(f):
                        printWarning(pkg, 'source-or-patch-not-gzipped', f)
            perm=files[f][0] & 07777
            if perm not in valid_src_perms:
                printWarning(pkg, 'strange-permission', f, oct(perm))

check=SourceCheck()

if Config.info:
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
