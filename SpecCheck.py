#############################################################################
# File		: SpecCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Thu Oct  7 17:06:14 1999
# Version	: $Id$
# Purpose	: check the spec file of a source rpm.
#############################################################################

from Filter import *
import AbstractCheck
import commands
import re
import sys

spec_regex=re.compile(".spec$")
patch_regex=re.compile("^\s*Patch(.*?)\s*:\s*([^\s]+)")
applied_patch_regex=re.compile("^\s*%patch([^\s]*)\s")

def file2string(file):
    fd=open(file, "r")
    content=fd.readlines()
    fd.close()
    return content
    
class SpecCheck(AbstractCheck.AbstractCheck):
    pgp_regex=re.compile("pgp|gpg", re.IGNORECASE)
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "FilesCheck")

    def check(self, pkg, verbose):
        if not pkg.isSource():
            return

        # lookup spec file
        files=pkg.files()
	spec_file=None
	for f in files.keys():
	    if spec_regex.search(f):
                spec_file=pkg.dirName() + "/" + f
                break
        if not spec_file:
            printError(pkg, "no-spec-file")
        else:
            # check content of spec file
            spec=file2string(spec_file)
            patches={}
            applied_patches=[]
            # gather info from spec lines
            for line in spec:
                res=patch_regex.search(line)
                if res:
                    patches[res.group(1)]=res.group(2)
                else:
                    res=applied_patch_regex.search(line)
                    if res:
                        applied_patches.append(res.group(1))
            # process gathered info
            for p in patches.keys():
                if p not in applied_patches:
                    if p == "" and "0" in applied_patches:
                        continue
                    if p == "0" and "" in applied_patches:
                        continue
                    printWarning(pkg, "patch-not-applied", "Patch" + p + ":", patches[p])

# Create an object to enable the auto registration of the test
check=SpecCheck()

# SpecCheck.py ends here
