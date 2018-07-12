# -*- coding: utf-8 -*-
#############################################################################
# File          : SourceCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Wed Oct 27 21:17:03 1999
# Purpose       : verify source package correctness.
#############################################################################

import re

import rpmlint.AbstractCheck as AbstractCheck
import rpmlint.Config as Config
from rpmlint.Filter import addDetails, printError, printWarning


DEFAULT_VALID_SRC_PERMS = (0o644, 0o755)

source_regex = re.compile(r'\\.(tar|patch|tgz|diff)$')
compress_ext = Config.getOption("CompressExtension", "bz2")
valid_src_perms = Config.getOption("ValidSrcPerms", DEFAULT_VALID_SRC_PERMS)

compressed_fileext_magic = {
    'xz': 'XZ compressed',
    'gz': 'gzip compressed',
    'tgz': 'gzip compressed',
    'bz2': 'bzip2 compressed'
}


class SourceCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'SourceCheck')

    def check_source(self, pkg):
        # process file list
        spec_file = None
        for fname, pkgfile in pkg.files().items():
            file_ext = fname.rpartition('.')[2]
            if (file_ext in compressed_fileext_magic and
                    pkgfile.magic and
                    compressed_fileext_magic[file_ext] not in pkgfile.magic):
                printWarning(pkg, 'inconsistent-file-extension', fname)

            if fname.endswith('.spec'):
                if spec_file:
                    printError(pkg, 'multiple-specfiles', spec_file, fname)
                else:
                    spec_file = fname
            elif source_regex.search(fname) and compress_ext and \
                    not fname.endswith(compress_ext):
                printWarning(pkg, 'source-or-patch-not-compressed',
                             compress_ext, fname)
            perm = pkgfile.mode & 0o7777
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

'inconsistent-file-extension',
'''The file name extension indicates a different compression format than
what is actually used (as checked by file(1))''',
)

# SourceCheck.py ends here
