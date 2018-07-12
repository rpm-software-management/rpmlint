# -*- coding: utf-8 -*-
#############################################################################
# File          : SignatureCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Thu Oct  7 17:06:14 1999
# Purpose       : check the presence of a PGP signature.
#############################################################################

import re

import rpmlint.AbstractCheck as AbstractCheck
import rpmlint.Pkg as Pkg
from rpmlint.Filter import addDetails, printError


class SignatureCheck(AbstractCheck.AbstractCheck):
    pgp_regex = re.compile(r"pgp|gpg", re.IGNORECASE)
    unknown_key_regex = re.compile(r"\(MISSING KEYS:(?:\([^)]+\))?\s+([^\)]+)\)")

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "SignatureCheck")

    def check(self, pkg):
        res = pkg.checkSignature()
        if not res or res[0] != 0:
            if res and res[1]:
                kres = SignatureCheck.unknown_key_regex.search(res[1])
            else:
                kres = None
            if kres:
                printError(pkg, "unknown-key", kres.group(1))
            else:
                Pkg.warn("Error checking signature of %s: %s" %
                         (pkg.filename, res[1]))
        else:
            if not SignatureCheck.pgp_regex.search(res[1]):
                printError(pkg, "no-signature")


# Create an object to enable the auto registration of the test
check = SignatureCheck()

addDetails(
'no-signature',
'''You have to include your pgp or gpg signature in your package.
For more information on signatures, please refer to www.gnupg.org.''',

'unknown-key',
'''The package was signed, but with an unknown key.
See the rpm --import option for more information.''',
)

# SignatureCheck.py ends here
