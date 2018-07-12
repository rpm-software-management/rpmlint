# -*- coding: utf-8 -*-
# Copyright (C) 2005 Enrico Scholz <enrico.scholz@informatik.tu-chemnitz.de>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA

import rpm

import rpmlint.AbstractCheck as AbstractCheck
from rpmlint.Filter import addDetails, printWarning
from rpmlint.Pkg import b2s


class DocFilesCheck(AbstractCheck.AbstractCheck):
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'DocFilesCheck')

    def __checkRequirements(self, pkg):

        doc_files = pkg.docFiles()
        files = pkg.files()

        reqs = {}
        for fname, pkgfile in files.items():
            reqs[fname] = [x[0] for x in pkgfile.requires]

        core_reqs = {}  # dependencies of non-doc files
        doc_reqs = {}   # dependencies of doc files

        for dep in pkg.header.dsFromHeader():
            # skip deps which were found by find-requires
            if dep.Flags() & rpm.RPMSENSE_FIND_REQUIRES != 0:
                continue
            core_reqs[dep.N()] = []

        # register things which are provided by the package
        for i in pkg.header[rpm.RPMTAG_PROVIDES]:
            core_reqs[b2s(i)] = []
        for i in files:
            core_reqs[i] = []

        for i in files:
            if not reqs[i]:
                continue  # skip empty dependencies
            if i in doc_files:
                target = doc_reqs
            else:
                target = core_reqs

            for r in reqs[i]:
                if r not in target:
                    target[r] = []
                target[r].append(i)

        # go through the calculated requirements of the %doc files
        for (dep, req_files) in doc_reqs.items():
            if dep not in core_reqs:
                for f in req_files:
                    printWarning(pkg, "doc-file-dependency", f, dep)

    def __checkUnwantedFiles(self, pkg):

        for docfile in pkg.docFiles():
            if docfile.endswith("/INSTALL"):
                printWarning(pkg, "install-file-in-docs", docfile)

    def check_binary(self, pkg):

        if not pkg.docFiles():
            return

        self.__checkRequirements(pkg)
        self.__checkUnwantedFiles(pkg)


check = DocFilesCheck()

addDetails(
'doc-file-dependency',
'''An included file marked as %doc creates a possible additional dependency in
the package.  Usually, this is not wanted and may be caused by eg. example
scripts with executable bits set included in the package's documentation.''',

'install-file-in-docs',
'''A file whose name suggests that it contains installation instructions is
included in the package.  Such instructions are often not relevant for already
installed packages; if this is the case for this file and it does not contain
any information that is of interest after the package has been built and
installed, do not include the file in the binary package.''',
)

# DocFilesCheck.py ends here
