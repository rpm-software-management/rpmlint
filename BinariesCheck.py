#############################################################################
# File		: BinariesCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 07:01:42 1999
# Version	: $Id$
# Purpose	: check binary files in a binary rpm package.
#############################################################################

import AbstractCheck
import rpm
import re
import commands
import string

class BinaryInfo:

    needed_regex=re.compile("^\s*NEEDED\s*(\S+)")
    rpath_regex=re.compile("^\s*RPATH\s*(\S+)")
    comment_regex=re.compile("^\s*\d+\s+\.comment\s+")
    dynsyms_regex=re.compile("^DYNAMIC SYMBOL TABLE:")
    unrecognized_regex=re.compile("^objdump: (.*?): File format not recognized$")
    
    def __init__(self, path):
	self.needed=[]
	self.rpath=[]
	self.comment=0
	self.dynsyms=0
	
	res=commands.getoutput("objdump --headers --private-headers -T " + path)
	if res:
	    for l in string.split(res, "\n"):
		needed=BinaryInfo.needed_regex.search(l)
		if needed:
		    self.needed.append(needed.group(1))
		else:
		    rpath=BinaryInfo.rpath_regex.search(l)
		    if rpath:
			self.rpath.append(rpath.group(1))
		    elif BinaryInfo.comment_regex.search(l):
			self.comment=1
		    elif BinaryInfo.dynsyms_regex.search(l):
			self.dynsyms=1
		    else:
			r=BinaryInfo.unrecognized_regex.search(l)
			if r:
			    sys.stderr.write("file format not recognized for $1\n." % (r.group(1)))
			    sys.exit(1)
	    
class BinariesCheck(AbstractCheck.AbstractCheck):

    binary_regex=re.compile("ELF|current ar archive")
    usr_share=re.compile("^/usr/share/")
    etc=re.compile("^/etc/")
    not_stripped=re.compile("not stripped")
    unstrippable=re.compile("\.o$|\.static$")
    shared_object_regex=re.compile("shared object")
    executable_regex=re.compile("executable")
    libc_regex=re.compile("libc\.")
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "BinariesCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return
	
        info=pkg.getFilesInfo()
	arch=pkg[rpm.RPMTAG_ARCH]

	for i in info:
	    is_binary=BinariesCheck.binary_regex.search(i[1])

	    if is_binary:
		if arch == "noarch":
		    print "E:", pkg.name, "arch-independent-package-contains-binary-or-object", i[0]
		else:
		    # in /usr/share ?
		    if BinariesCheck.usr_share.search(i[0]):
			print "E:", pkg.name, "arch-dependent-file-in-usr-share", i[0]
		    # in /etc ?
		    if BinariesCheck.etc.search(i[0]):
			print "E:", pkg.name, "binary-in-etc", i[0]

		    # stripped ?
		    if not BinariesCheck.unstrippable.search(i[0]):
			if BinariesCheck.not_stripped.search(i[1]):
			    print "E:", pkg.name, "unstripped-binary-or-object", i[0]

			# inspect binary file
			bin_info=BinaryInfo(pkg.dirName()+i[0])

			# rpath ?
			if bin_info.rpath:
			    print "W:", pkg.name, "binary-or-shlib-defines-rpath", i[0], bin_info.rpath

			# statically linked ?
			if BinariesCheck.shared_object_regex.search(i[1]) or \
			   BinariesCheck.executable_regex.search(i[1]):

			    if not bin_info.needed:
				if BinariesCheck.shared_object_regex.search(i[1]):
				    print "W:", pkg.name, "shared-lib-without-dependency-information", i[0]
				else:
				    print "E:", pkg.name, "statically-linked-binary", i[0]
			    else:
				# linked against libc ?
				if not BinariesCheck.libc_regex.search(i[0]):
				    found_libc=0
				    for lib in bin_info.needed:
					if BinariesCheck.libc_regex.search(lib):
					    found_libc=1
					    break
				    if not found_libc:
					if BinariesCheck.shared_object_regex.search(i[1]):
					    print "W:", pkg.name, "library-not-linked-against-libc", i[0]
					else:
					    print "W:", pkg.name, "program-not-linked-against-libc", i[0]
			    
# Create an object to enable the auto registration of the test
check=BinariesCheck()

# BinariesCheck.py ends here
