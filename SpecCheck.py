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
import rpm

spec_regex=re.compile(".spec$")
patch_regex=re.compile("^\s*Patch(.*?)\s*:\s*([^\s]+)")
applied_patch_regex=re.compile("^\s*%patch([^\s]*)\s")
source_dir_regex=re.compile("[^#]*\$RPM_SOURCE_DIR")
obsolete_tags_regex=re.compile("^(Copyright|Serial)\s*:\s*([^\s]+)")

def file2string(file):
    fd=open(file, "r")
    content=fd.readlines()
    fd.close()
    return content
    
class SpecCheck(AbstractCheck.AbstractCheck):
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "SpecCheck")

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
            if f != pkg[rpm.RPMTAG_NAME] + ".spec":
                printError(pkg, "invalid-spec-name", f)
                
            # check content of spec file
            spec=file2string(spec_file)
            patches={}
            applied_patches=[]
            source_dir=None
            # gather info from spec lines
            for line in spec:
                res=patch_regex.search(line)
                if res:
                    patches[res.group(1)]=res.group(2)
                else:
                    res=applied_patch_regex.search(line)
                    if res:
                        applied_patches.append(res.group(1))
                    elif not source_dir:
                        res=source_dir_regex.search(line)
                        if res:
                            source_dir=1
                            printError(pkg, "use-of-RPM_SOURCE_DIR")
                res=obsolete_tags_regex.search(line)
                if res:
                    printWarning(pkg, "obsolete-tag", res.group(1))

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

# Add information about checks
if Config.info:
    addDetails(
'no-spec-file',
'''No spec file was specified in your RPM building. Please specify a valid
SPEC file to build a valid RPM package.''',

'invalid-spec-name',
'''Your spec file must finish with '.spec'. If it's not the case, rename your
file and rebuild your package.''',

'use-of-RPM_SOURCE_DIR',
'''You use RPM_SOURCE_DIR in your spec file. If you have to use a directory
for building, use RPM_BUILD_ROOT instead.''',

'patch-not-applied',
'''A patch is included in your package but was not applied. Refer to the patches
documentation to see what's wrong.''',

'obsolete-tag',
'''The following tags are obsolete: Copyright and Serial. They must
be replaced by License and Epoch respectively.''',

)

# SpecCheck.py ends here
