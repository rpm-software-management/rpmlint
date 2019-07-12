#############################################################################
# Project         : Mandriva Linux
# Module          : rpmlint
# File            : PamCheck.py
# Author          : Michael Scherer
# Created On      : 31/01/2006
# Purpose         : Apply pam policy
#############################################################################

import re

from rpmlint.checks.AbstractCheck import AbstractFilesCheck


class PamCheck(AbstractFilesCheck):
    pam_stack_re = re.compile(r'^\s*[^#].*pam_stack\.so\s*service')

    def __init__(self, config, output):
        AbstractFilesCheck.__init__(self, config, output, r'/etc/pam\.d/.*')
        self.output.error_details.update(pam_details_dict)

    def check_file(self, pkg, filename):
        lines = pkg.grep(self.pam_stack_re, filename)
        if lines:
            self.output.add_info('E', pkg, 'use-old-pam-stack', filename,
                                 '(line %s)' % ', '.join(lines))


pam_details_dict = {
'use-old-pam-stack':
"""Update pam file to use include instead of pam_stack.""",
}
