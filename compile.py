#!/usr/bin/python
#############################################################################
# File		: compile.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Sat Oct 23 23:40:21 1999
# Version	: $Id$
# Purpose	: byte compile all python files given in arguments.
#############################################################################

import py_compile
import re
import sys

py_regex=re.compile(".*\.py$")

for f in sys.argv[1:]:
    if py_regex.search(f):
	py_compile.compile(f, f+"o")
    
# compile.py ends here
