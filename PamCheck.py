# -*- coding: utf-8 -*-
#---------------------------------------------------------------
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : PamCheck.py
# Author          : Michael Scherer
# Created On      : 31/01/2006
# Purpose         : Apply pam policy
#---------------------------------------------------------------

import re

from Filter import addDetails, printError
import AbstractCheck


pam_stack_re = re.compile('^\s*[^#].*pam_stack\.so\s*service')

class PamCheck(AbstractCheck.AbstractFilesCheck):
    def __init__(self):
        AbstractCheck.AbstractFilesCheck.__init__(self, "PamCheck",
                                                  "/etc/pam\.d/.*")

    def check_file(self, pkg, filename):
        lines = pkg.grep(pam_stack_re, filename)
        if lines:
            printError(pkg, 'use-old-pam-stack', filename,
                       '(line %s)' % ", ".join(lines))

check = PamCheck()

addDetails(
'use-old-pam-stack',
'''Update pam file to use include instead of pam_stack.''',
)

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
