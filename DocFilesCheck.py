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

from Filter import *

import sys
import rpm
from types import TupleType

import AbstractCheck

# remove version from deps like ['foo', '>', '3']
def _stripVersionedDeps(deps):
    deps = deps[:]
    j    = len(deps)
    while j>=3:
        j = j-1
        if deps[j-1] in ('<', '<=', '=', '>=', '>'):
            del deps[j-1:j+1]

    return deps

class DocFilesCheck(AbstractCheck.AbstractCheck):
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'DocFilesCheck')

    def __checkRequirements(self, pkg):
        file_reqs = pkg.header[rpm.RPMTAG_FILEREQUIRE]
        files     = pkg.header[rpm.RPMTAG_FILENAMES] # not files().keys()!
        doc_files = pkg.docFiles()

        assert(len(file_reqs) == len(files))

        reqs      = {}
        for i in xrange(0,len(files)):
            tmp            = file_reqs[i].split()
            tmp            = _stripVersionedDeps(tmp)
            reqs[files[i]] = tmp

        core_reqs = {}  # dependencies of non-doc files
        doc_reqs  = {}  # dependencies of doc files

        for dep in pkg.header.dsFromHeader():
            if isinstance(dep, TupleType): # rpm-python < 4.3.2
                name = dep[0]
                flags = dep[2]
            else:
                name = dep.N()
                flags = dep.Flags()
            # skip deps which were found by find-requires
            if flags & rpm.RPMSENSE_FIND_REQUIRES != 0:
                continue
            core_reqs[name] = []

        # register things which are provided by the package
        for i in pkg.header[rpm.RPMTAG_PROVIDES] + files:
            core_reqs[i] = []

        for i in files:
            if not reqs[i]:      continue       # skip empty dependencies
            elif i in doc_files: target = doc_reqs
            else:                target = core_reqs

            for r in reqs[i]:
                if not target.has_key(r):
                    target[r] = []

                target[r].append(i)


        # go through the calculated requirements of the %doc files
        for (dep,req_files) in doc_reqs.items():
            if dep not in core_reqs:
                for f in req_files:
                    printWarning(pkg, "doc-file-dependency", f, dep)

    def check(self, pkg):
        if pkg.isSource():
            return
        if not 'RPMTAG_FILEREQUIRE' in dir(rpm): # need rpm >= 4.1.1
            return

        self.__checkRequirements(pkg)


check = DocFilesCheck()

if Config.info:
    addDetails(
'doc-file-dependency',
'''An included file marked as %doc creates a possible additional dependency in
the package.  Usually, this is not wanted and may be caused by eg. example
scripts with executable bits set included in the package's documentation.''',
)

def test():
    for (arg,exp) in ((['a'],['a']),
                      ([], []),
                      (['a','b'], ['a', 'b']),
                      (['a','b', 'c', 'd'], ['a', 'b', 'c', 'd']),
                      (['a','>', '0'], ['a']),
                      (['a','>', '0', 'b'], ['a', 'b']),
                      (['a','>', '0', 'b', '>', '0'], ['a', 'b']),
                      ):
        assert(_stripVersionedDeps(arg) == exp)

# DocFilesCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
