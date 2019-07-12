#############################################################################
# File          : SignatureCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Thu Oct  7 17:06:14 1999
# Purpose       : check the presence of a PGP signature.
#############################################################################

import re

from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import print_warning


class SignatureCheck(AbstractCheck):
    pgp_regex = re.compile(r'pgp|gpg', re.IGNORECASE)
    unknown_key_regex = re.compile(r'\(MISSING KEYS:(?:\([^)]+\))?\s+([^\)]+)\)')

    def __init__(self, config, output):
        super().__init__(config, output)
        self.output.error_details.update({
        'no-signature':
            """You have to include your pgp or gpg signature in your package.
            For more information on signatures, please refer to www.gnupg.org.""",
        'unknown-key':
            """The package was signed, but with an unknown key.
            See the rpm --import option for more information.""",
        })

    def check(self, pkg):
        res = pkg.checkSignature()
        if not res or res[0] != 0:
            if res and res[1]:
                kres = SignatureCheck.unknown_key_regex.search(res[1])
            else:
                kres = None
            if kres:
                self.output.add_info('E', pkg, 'unknown-key', kres.group(1))
            else:
                print_warning('Error checking signature of %s: %s' %
                              (pkg.filename, res[1]))
        else:
            if not SignatureCheck.pgp_regex.search(res[1]):
                self.output.add_info('E', pkg, 'no-signature')
