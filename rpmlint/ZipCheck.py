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

from rpmlint import Pkg
from rpmlint.AbstractCheck import AbstractCheck


class ZipCheck(AbstractCheck):
    zip_regex = re.compile(r'\.(zip|[ewj]ar)$')
    jar_regex = re.compile(r'\.[ewj]ar$')
    classpath_regex = re.compile(r'^\s*Class-Path\s*:', re.MULTILINE | re.IGNORECASE)

    def __init__(self, config, output):
        super().__init__(config, output, 'ZipCheck')
        zip_details_dict = {
            'bad-crc-in-zip':
            """The reported file in the zip fails the CRC check. Usually this is a
            sign of a corrupt zip file.""",
            'uncompressed-zip':
            """The zip file is not compressed.""",
            'class-path-in-manifest':
            """The META-INF/MANIFEST.MF file in the jar contains a hardcoded Class-Path.
            These entries do not work with older Java versions and even if they do work,
            they are inflexible and usually cause nasty surprises.""",
            'jar-indexed':
            """The jar file is indexed, ie. it contains the META-INF/INDEX.LIST file.
            These files are known to cause problems with some older Java versions.""",
            'jar-not-indexed':
            """The jar file is not indexed, ie. it does not contain the META-INF/INDEX.LIST
            file.  Indexed jars speed up the class searching process of classloaders
            in some situations.""",
        }
        self.output.error_details.update(zip_details_dict)
        self.want_indexed_jars = config.configuration['UseIndexedJars']

    def check(self, pkg):
        for fname, pkgfile in pkg.files().items():
            path = pkgfile.path
            if self.zip_regex.search(fname) and os.path.exists(path) and \
               stat.S_ISREG(os.lstat(path)[stat.ST_MODE]) and \
               zipfile.is_zipfile(path):
                z = None  # TODO ZipFile is context manager in 2.7+
                try:
                    z = zipfile.ZipFile(path, 'r')
                    badcrc = z.testzip()
                    if badcrc:
                        self.output.add_info('E', pkg, 'bad-crc-in-zip', badcrc, fname)
                except zipfile.error:
                    self.output.add_info('W', pkg, 'unable-to-read-zip', '%s: %s' %
                                         (fname, sys.exc_info()[1]))
                else:
                    compressed = False
                    for zinfo in z.infolist():
                        if zinfo.compress_type != zipfile.ZIP_STORED:
                            compressed = True
                            break
                    if not compressed:
                        self.output.add_info('W', pkg, 'uncompressed-zip', fname)

                    # additional jar checks
                    if self.jar_regex.search(fname):
                        try:
                            mf = Pkg.b2s(z.read('META-INF/MANIFEST.MF'))
                            if self.classpath_regex.search(mf):
                                self.output.add_info('W', pkg,
                                                     'class-path-in-manifest', fname)
                        except KeyError:
                            # META-INF/* are optional:
                            # http://java.sun.com/j2se/1.4/docs/guide/jar/jar.html
                            pass
                        try:
                            zinfo = z.getinfo('META-INF/INDEX.LIST')
                            if not self.want_indexed_jars:
                                self.output.add_info('W', pkg, 'jar-indexed', fname)
                        except KeyError:
                            if self.want_indexed_jars:
                                self.output.add_info('W', pkg, 'jar-not-indexed', fname)
                            pass

                z and z.close()
