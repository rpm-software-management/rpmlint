# -*- coding: utf-8 -*-
#############################################################################
# File          : ZipCheck.py
# Package       : rpmlint
# Author        : Ville Skyttä
# Created on    : Thu Oct 30 00:14:45 EET 2003
# Purpose       : Verify Zip/Jar file correctness
#############################################################################

import os
import re
import stat
import sys
import zipfile

import rpmlint.AbstractCheck as AbstractCheck
import rpmlint.Config as Config
import rpmlint.Pkg as Pkg
from rpmlint.Filter import addDetails, printError, printWarning


zip_regex = re.compile(r'\.(zip|[ewj]ar)$')
jar_regex = re.compile(r'\.[ewj]ar$')
classpath_regex = re.compile(r'^\s*Class-Path\s*:', re.M | re.I)

want_indexed_jars = Config.getOption('UseIndexedJars', True)


class ZipCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "ZipCheck")

    def check(self, pkg):
        for fname, pkgfile in pkg.files().items():
            path = pkgfile.path
            if zip_regex.search(fname) and os.path.exists(path) and \
               stat.S_ISREG(os.lstat(path)[stat.ST_MODE]) and \
               zipfile.is_zipfile(path):
                z = None  # TODO ZipFile is context manager in 2.7+
                try:
                    z = zipfile.ZipFile(path, 'r')
                    badcrc = z.testzip()
                    if badcrc:
                        printError(pkg, 'bad-crc-in-zip', badcrc, fname)
                except zipfile.error:
                    printWarning(pkg, 'unable-to-read-zip', '%s: %s' %
                                 (fname, sys.exc_info()[1]))
                else:
                    compressed = False
                    for zinfo in z.infolist():
                        if zinfo.compress_type != zipfile.ZIP_STORED:
                            compressed = True
                            break
                    if not compressed:
                        printWarning(pkg, 'uncompressed-zip', fname)

                    # additional jar checks
                    if jar_regex.search(fname):
                        try:
                            mf = Pkg.b2s(z.read('META-INF/MANIFEST.MF'))
                            if classpath_regex.search(mf):
                                printWarning(pkg,
                                             'class-path-in-manifest', fname)
                        except KeyError:
                            # META-INF/* are optional:
                            # http://java.sun.com/j2se/1.4/docs/guide/jar/jar.html
                            pass
                        try:
                            zinfo = z.getinfo('META-INF/INDEX.LIST')
                            if not want_indexed_jars:
                                printWarning(pkg, 'jar-indexed', fname)
                        except KeyError:
                            if want_indexed_jars:
                                printWarning(pkg, 'jar-not-indexed', fname)
                            pass

                z and z.close()


check = ZipCheck()

addDetails(
'bad-crc-in-zip',
'''The reported file in the zip fails the CRC check. Usually this is a
sign of a corrupt zip file.''',

'uncompressed-zip',
'''The zip file is not compressed.''',

'class-path-in-manifest',
'''The META-INF/MANIFEST.MF file in the jar contains a hardcoded Class-Path.
These entries do not work with older Java versions and even if they do work,
they are inflexible and usually cause nasty surprises.''',

'jar-indexed',
'''The jar file is indexed, ie. it contains the META-INF/INDEX.LIST file.
These files are known to cause problems with some older Java versions.''',

'jar-not-indexed',
'''The jar file is not indexed, ie. it does not contain the META-INF/INDEX.LIST
file.  Indexed jars speed up the class searching process of classloaders
in some situations.''',
)

# ZipCheck.py ends here
