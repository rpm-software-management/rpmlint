#############################################################################
# File		: SignatureCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Thu Oct  7 17:06:14 1999
# Version	: $Id$
# Purpose	: check the presence of a PGP signature.
#############################################################################

from Filter import *
import AbstractCheck
import commands
import re
import sys

class SignatureCheck(AbstractCheck.AbstractCheck):
    pgp_regex=re.compile("pgp|gpg", re.IGNORECASE)
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "SignatureCheck")

    def check(self, pkg, verbose):
	res=pkg.checkSignature()
	if not res or res[0] != 0:
	    sys.stderr.write("error checking signature of " + pkg.filename + "\n")
	else:
	    if not SignatureCheck.pgp_regex.search(res[1]):
		printError(pkg, "no-signature")
	
# Create an object to enable the auto registration of the test
check=SignatureCheck()

# SignatureCheck.py ends here
