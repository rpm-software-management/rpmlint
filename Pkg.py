#############################################################################
# File		: Pkg.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 07:18:06 1999
# Version	: $Id$
# Purpose	: provide an API to handle a rpm package either by accessing
#		the rpm file or by accessing the files contained inside.
#############################################################################

import os
import rpm
import os.path
import stat
import commands
import re
import string

RPMFILE_CONFIG=(1 << 0)
RPMFILE_DOC=(1 << 1)
RPMFILE_DONOTUSE=(1 << 2)
RPMFILE_MISSINGOK=(1 << 3)
RPMFILE_NOREPLACE=(1 << 4)
RPMFILE_SPECFILE=(1 << 5)
RPMFILE_GHOST=(1 << 6)
RPMFILE_LICENSE=(1 << 7)
RPMFILE_README=(1 << 8)

class Pkg:
    file_regex=re.compile("\.([^:]+):\s+(.*)")

    def __init__(self, filename, dirname):
	self.filename=filename
	self.extracted=0
	self.dirname=dirname
	self.file_info=None
	self.config_files=None
	
	# Create a package object from the file name
	fd=os.open(filename, os.O_RDONLY)
	(self.header, self.is_source)=rpm.headerFromPackage(fd)
	os.close(fd)

	self.name=self.header[rpm.RPMTAG_NAME]
	
    def isSource(self):
	return self.is_source
    
    def __getitem__(self, key):
	return self.header[key]

    def dirName(self):
	if not self.extracted:
	    self._extract()
	return self.dirname

    def _extract(self):
	s=os.stat(self.dirname)
        if not stat.S_ISDIR(s[stat.ST_MODE]):
            print "unable to access dir", self.dirname
        else:
            self.dirname = "%s/%s" % (self.dirname, os.path.basename(self.filename))
            os.mkdir(self.dirname)
            str="rpm2cpio %s | (cd %s; cpio -id)" % (self.filename, self.dirname)
            cmd=commands.getstatusoutput(str)
	    self.extracted=1
	    
    def getFilesInfo(self):
	if self.file_info == None:
	    self.file_info=[]
	    lines=commands.getoutput("cd %s; find . -type f -print0 | xargs -0r file" % (self.dirName()))
	    lines=string.split(lines, "\n")
	    for l in lines:
		#print l
		res=Pkg.file_regex.search(l)
		if res:
		    self.file_info.append([res.group(1), res.group(2)])
	    #print self.file_info
	return self.file_info
    
    def cleanup(self):
	commands.getstatusoutput("rm -rf " + self.dirname)
	pass

    def configFiles(self):
	if self.config_files != None:
	    return self.config_files
	self.config_files=[]
	flags=self.header[rpm.RPMTAG_FILEFLAGS]
	files=self.header[rpm.RPMTAG_FILENAMES]
	if flags:
	    for idx in range(0, len(flags)):
		if flags[idx] & RPMFILE_CONFIG:
		    self.config_files.append(files[idx])
	return self.config_files

# Pkg.py ends here
