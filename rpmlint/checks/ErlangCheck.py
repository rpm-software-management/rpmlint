# vim:sw=4:et
#############################################################################
# File          : ErlangCheck.py
# Package       : rpmlint
# Author        : Matwey V. Kornilov
# Purpose       : Check for erlang compiled files
#############################################################################

import AbstractCheck
import Filter
import Pkg
import re
import rpm

from pybeam import BeamFile


class ErlangCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        AbstractCheck.AbstractFilesCheck.__init__(
            self, "ErlangCheck", r'.*?\.beam$')
        build_dir = rpm.expandMacro("%_builddir")
        self.source_re = re.compile(build_dir)

    def check_file(self, pkg, filename):
        beam = BeamFile(pkg.files()[filename].path)
        if 'debug_info' not in beam.compileinfo['options']:
            Filter.printWarning(
                pkg, "beam-compiled-without-debug_info", filename)
        if not self.source_re.match(Pkg.b2s(beam.compileinfo['source'].value)):
            Filter.printWarning(
                pkg, "beam-was-not-recompiled", filename,
                beam.compileinfo['source'].value)


check = ErlangCheck()

Filter.addDetails(
'beam-compiled-without-debug_info',
""""Your beam file indicates that it doesn't contain debug_info.
Please, make sure that you compile with +debug_info.""",

'beam-was-not-recompiled',
"""It seems that your beam file was not compiled by you, but was
just copied in binary form to destination. Please, make sure
that you really compile it from the sources.""",
)
