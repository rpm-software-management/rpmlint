# check the rpm file for various errors.
# $Id$

from Filter import *
import AbstractCheck
import rpm
import os
import Config

class RpmFileCheck(AbstractCheck.AbstractCheck):
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "RpmFileCheck")

    def check(self, pkg):
        # http://en.wikipedia.org/wiki/Joliet_(file_system)
        rpmfile_name = os.path.basename(pkg.filename)
        if len(rpmfile_name) > 64:
            printWarning(pkg, 'filename-too-long-for-joliet', rpmfile_name)

check = RpmFileCheck()

if Config.info:
    addDetails(
'filename-too-long-for-joliet',
'This filename is too long to fit on a joliet filesystem ( limit is 64 unicode chars ).',
)

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
