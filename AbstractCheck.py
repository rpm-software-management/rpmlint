#############################################################################
# File		: AbstractCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 00:22:38 1999
# Version	: $Id$
# Purpose	: Abstract class to hold all the derived classes.
#############################################################################

class AbstractCheck:
    checks=[]
    
    def __init__(self, name):
	AbstractCheck.checks.append(self)
	self.name = name

    def check(self, pkg, verbose):
	pass
    
# AbstractCheck.py ends here
