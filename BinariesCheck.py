#############################################################################
# File		: BinariesCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 07:01:42 1999
# Version	: $Id$
# Purpose	: check binary files in a binary rpm package.
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import re
import commands
import string
import sys
import Config

DEFAULT_SYSTEM_LIB_PATHS=('/lib', '/usr/lib', '/usr/X11R6/lib')

class BinaryInfo:

    needed_regex=re.compile('^\s*NEEDED\s*(\S+)')
    rpath_regex=re.compile('^\s*RPATH\s*(\S+)')
    soname_regex=re.compile('^\s*SONAME\s*(\S+)')
    comment_regex=re.compile('^\s*\d+\s+\.comment\s+')
    dynsyms_regex=re.compile('^DYNAMIC SYMBOL TABLE:')
    unrecognized_regex=re.compile('^objdump: (.*?): File format not recognized$')
    non_pic_regex=re.compile('^\s+\d+\s+\.rela?\.(data|text)')
    
    def __init__(self, path, file):
	self.needed=[]
	self.rpath=[]
	self.comment=0
	self.dynsyms=0
	self.soname=0
        self.non_pic=1

	res=commands.getoutput('objdump --headers --private-headers -T ' + path)
	if res:
	    for l in string.split(res, '\n'):
		needed=BinaryInfo.needed_regex.search(l)
		if needed:
		    self.needed.append(needed.group(1))
		else:
		    rpath=BinaryInfo.rpath_regex.search(l)
		    if rpath:
                        for p in string.split(rpath.group(1), ':'):
                            self.rpath.append(p)
		    elif BinaryInfo.comment_regex.search(l):
			self.comment=1
		    elif BinaryInfo.dynsyms_regex.search(l):
			self.dynsyms=1
                    elif BinaryInfo.non_pic_regex.search(l):
                        self.non_pic=0
		    else:
			r=BinaryInfo.unrecognized_regex.search(l)
			if r:
			    sys.stderr.write('file format not recognized for %s in %s\n' % (r.group(1), file))
			    #sys.exit(1)
		    r=BinaryInfo.soname_regex.search(l)
                    if r:
			self.soname=r.group(1)

path_regex=re.compile('(.*/)([^/]+)')
versioned_dir_regex=re.compile('[0-9.][0-9.]+')
binary_regex=re.compile('ELF|current ar archive')
usr_share=re.compile('^/usr/share/')
etc=re.compile('^/etc/')
not_stripped=re.compile('not stripped')
unstrippable=re.compile('\.o$|\.static$')
shared_object_regex=re.compile('shared object')
executable_regex=re.compile('executable')
libc_regex=re.compile('libc\.')
so_regex=re.compile('/lib/[^/]+\.so')
validso_regex=re.compile('\.so\.[0-9]+')
sparc_regex=re.compile('SPARC32PLUS|SPARC V9|UltraSPARC')
system_lib_paths=Config.getOption('SystemLibPaths', DEFAULT_SYSTEM_LIB_PATHS)
usr_lib_regex=re.compile('^/usr/lib/')
bin_regex=re.compile('^(/usr(/X11R6)?)?/s?bin/')

def dir_base(path):
    res=path_regex.search(path)
    if res:
        return res.group(1), res.group(2)
    else:
        return '', path
    
class BinariesCheck(AbstractCheck.AbstractCheck):
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, 'BinariesCheck')

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return
	
        info=pkg.getFilesInfo()
	arch=pkg[rpm.RPMTAG_ARCH]
        files=pkg.files()
        exec_files=[]
        has_lib=[]
        
	for i in info:
	    is_binary=binary_regex.search(i[1])

	    if is_binary:
		if arch == 'noarch':
		    printError(pkg, 'arch-independent-package-contains-binary-or-object', i[0])
		else:
		    # in /usr/share ?
		    if usr_share.search(i[0]):
			printError(pkg, 'arch-dependent-file-in-usr-share', i[0])
		    # in /etc ?
		    if etc.search(i[0]):
			printError(pkg, 'binary-in-etc', i[0])

                    if arch == 'sparc' and sparc_regex.search(i[1]):
                        printError(pkg, 'non-sparc32-binary', i[0])

		    # stripped ?
		    if not unstrippable.search(i[0]):
			if not_stripped.search(i[1]):
			    printWarning(pkg, 'unstripped-binary-or-object', i[0])

			# inspect binary file
			bin_info=BinaryInfo(pkg.dirName()+i[0], i[0])

                        # so name in library
                        if so_regex.search(i[0]):
                            has_lib.append(i[0])
                            if not bin_info.soname:
                                printWarning(pkg, 'no-soname', i[0])
                            else:
                                if not validso_regex.search(bin_info.soname):
                                    printError(pkg, 'invalid-soname', i[0], bin_info.soname)
                                else:
                                    (dir, base) = dir_base(i[0])
                                    try:
                                        symlink = dir + bin_info.soname
                                        (perm, owner, group, link) = files[symlink]
                                        if link != i[0] and link != base and link != '':
                                            printError(pkg, 'invalid-ldconfig-symlink', i[0], link)
                                    except KeyError:
                                        printError(pkg, 'no-ldconfig-symlink', i[0])
                                    
                            if bin_info.non_pic:
                                printError(pkg, 'shlib-with-non-pic-code', i[0])
                                
			# rpath ?
			if bin_info.rpath:
                            for p in bin_info.rpath:
                                if p in system_lib_paths or \
                                   not usr_lib_regex.search(p):
                                    printError(pkg, 'binary-or-shlib-defines-rpath', i[0], bin_info.rpath)
                                    break

			# statically linked ?
                        is_exec=executable_regex.search(i[1])
			if shared_object_regex.search(i[1]) or \
			   is_exec:

                            if is_exec and bin_regex.search(i[0]):
                                exec_files.append(i[0])
                                
			    if not bin_info.needed:
				if shared_object_regex.search(i[1]):
				    printWarning(pkg, 'shared-lib-without-dependency-information', i[0])
				else:
				    printError(pkg, 'statically-linked-binary', i[0])
			    else:
				# linked against libc ?
				if not libc_regex.search(i[0]):
				    found_libc=0
				    for lib in bin_info.needed:
					if libc_regex.search(lib):
					    found_libc=1
					    break
				    if not found_libc:
					if shared_object_regex.search(i[1]):
					    printWarning(pkg, 'library-not-linked-against-libc', i[0])
					else:
					    printWarning(pkg, 'program-not-linked-against-libc', i[0])
        if has_lib != []:
            if exec_files != []:
                for f in exec_files:
                    printError(pkg, 'executable-in-library-package', f)
            for f in files.keys():
                if not f in exec_files and not so_regex.search(f) and not versioned_dir_regex.search(f):
                    printError(pkg, 'non-versioned-file-in-library-package', f)
                    
# Create an object to enable the auto registration of the test
check=BinariesCheck()

# Add information about checks
if Config.info:
    addDetails(
'arch-independent-package-contains-binary-or-object',
'''The package contains a binary or object file but is tagged
Architecture: noarch.''',

'arch-dependent-file-in-usr-share',
'''This package installs an ELF binary in the /usr/share
 hierarchy, which is reserved for architecture-independent files.''',

'binary-in-etc',
'''This package installs an ELF binary in /etc.  Both the
FHS and the FSSTND forbid this.''',

# 'non-sparc32-binary',
# '',

'invalid-soname',
'''The soname of the library isn't in the form lib<libname>.so.<major>.''',

'invalid-ldconfig-symlink',
'''The symbolic link references the wrong file. (It should reference
the shared library.)''',

'no-ldconfig-symlink',
'''The package should not only include the shared library itself, but
also the symbolic link which ldconfig would produce. (This is
necessary, so that the link gets removed by dpkg automatically when
the package gets removed.)  If the symlink is in the package, check
that the SONAME of the library matches the info in the shlibs
file.''',

'shlib-with-non-pic-code',
'''The listed shared libraries contain object code that was compiled
without -fPIC. All object code in shared libraries should be
recompiled separately from the static libraries with the -fPIC option.

Another common mistake that causes this problem is linking with 
``gcc -Wl,-shared'' instead of ``gcc -shared''.''',

'binary-or-shlib-defines-rpath',
'''The binary or shared library defines the `RPATH'. Usually this is a
bad thing because it hard codes the path to search libraries and so it
makes difficult to move libraries around.  Most likely you will find a
Makefile with a line like: gcc test.o -o test -Wl,--rpath.''',

'statically-linked-binary',
'''The package installs a statically linked binary or object file.

Usually this is a bug. Otherwise, please contact
<flepied@mandrakesoft.com> about this so that this error gets included
in the exception file for rpmlint. (With that, rpmlint will ignore
this bug in the future.)''',

'executable-in-library-package',
'''The package mixes up libraries and executables. Mixing up these
both types of files makes upgrades quite impossible.''',

'non-versioned-file-in-library-package',
'''The package contains files in non versioned directories. This makes
impossible to have multiple major versions of the libraries installed.
One solution can be to change the directories which contain the files
to subdirs of /usr/lib/<name>-<version> or /usr/share/<name>-<version>.
Another solution can be to include a version number in the file names
themselves.''',

)

# BinariesCheck.py ends here
