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
import re
import sys
import rpm
import string

spec_regex=re.compile(".spec$")
patch_regex=re.compile("^\s*Patch(.*?)\s*:\s*([^\s]+)")
applied_patch_regex=re.compile("^\s*%patch([^\s]*)\s")
source_dir_regex=re.compile("[^#]*(\$RPM_SOURCE_DIR|%{?_sourcedir}?)")
obsolete_tags_regex=re.compile("^(Copyright|Serial)\s*:\s*([^\s]+)")
buildroot_regex=re.compile('Buildroot\s*:\s*([^\s]+)', re.IGNORECASE)
tmp_regex=re.compile('^/')
clean_regex=re.compile('^%clean')
changelog_regex=re.compile('^%changelog')
configure_start_regex=re.compile('\./configure')
configure_libdir_spec_regex=re.compile('\./configure[^#]*--libdir=([^\s]+)[^#]*')

# Only check for /lib, /usr/lib, /usr/X11R6/lib
# TODO: better handling of X libraries and modules.
hardcoded_library_paths='(/lib|/usr/lib|/usr/X11R6/lib/(?!([^/]+/)+)[^/]*\\.([oa]|la|so[0-9.]*))'
hardcoded_library_path_regex=re.compile('^[^#]*((^|\s+|\.\./\.\.|\${?RPM_BUILD_ROOT}?|%{?buildroot}?)' + hardcoded_library_paths + '(?=[\s;/])([^\s;]*))')

def file2string(file):
    fd=open(file, "r")
    content=fd.readlines()
    fd.close()
    return content
    
class SpecCheck(AbstractCheck.AbstractCheck):
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "SpecCheck")

    def check(self, pkg):
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
            buildroot=0
            clean=0
            changelog=0
            configure=0
            configure_cmdline=""
            
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
				
                res=changelog_regex.search(line)
                if res:
                    changelog=1
                
                if configure:
                    if configure_cmdline[-1] == "\\":
                        configure_cmdline=configure_cmdline[:-1] + string.strip(line)
                    else:
                        configure=0
                        res=configure_libdir_spec_regex.search(configure_cmdline)
                        if not res:
                            printError(pkg, "configure-without-libdir-spec")
                        else:
                            res=re.match(hardcoded_library_paths, res.group(1))
                            if res:
                                printError(pkg, "hardcoded-library-path", res.group(1), "in configure options")
                
                res=configure_start_regex.search(line)
                if not changelog and res:
                    configure=1
                    configure_cmdline=string.strip(line)
                
                res=hardcoded_library_path_regex.search(line)
                if not changelog and res:
                    printError(pkg, "hardcoded-library-path", "in", string.lstrip(res.group(1)))
                
                res=buildroot_regex.search(line)
                if res:
                    buildroot=1
                    if tmp_regex.search(res.group(1)):
                        printWarning(pkg, 'hardcoded-path-in-buildroot-tag', res.group(1))

                if not clean and clean_regex.search(line):
                    clean=1
                    
            if not buildroot:
                printError(pkg, 'no-buildroot-tag')

            if not clean:
                printError(pkg, 'no-%clean-section')
                
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

'no-buildroot-tag',
'''The BuildRoot tag isn't used in your spec. It must be used to
allow build as non root.''',

'hardcoded-path-in-buildroot-tag',
'''A path is hardcoded in your Buildroot tag. It should be replaced
by something like %{_tmppath}/%name-root.''',

'hardcoded-library-path',
'''A library path is hardcoded to one of the following paths: /lib,
/usr/lib. It should be replaced by something like /%{_lib} or %{_libdir}.''',

'configure-without-libdir-spec',
'''A configure script is run without specifying the libdir. Configure
options must be augmented with something like libdir=%{_libdir}.''',

'no-%clean-section',
'''The spec file doesn't contain a %clean section to remove the files installed
by the %install section.''',

)

# SpecCheck.py ends here
