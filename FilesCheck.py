#############################################################################
# File		: FilesCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Mon Oct  4 19:32:49 1999
# Version	: $Id$
# Purpose	: test various aspects on files: locations, owner, groups,
#		permission, setuid, setgid...
#############################################################################

import AbstractCheck
import rpm
import re
import stat
import string

class FilesCheck(AbstractCheck.AbstractCheck):
    tmp_regex=re.compile("^/tmp/|^(/var|/usr)/tmp/")
    mnt_regex=re.compile("^/mnt/")
    opt_regex=re.compile("^/opt/")
    etc_regex=re.compile("^/etc/")
    sub_bin_regex=re.compile("^(/usr)?/s?bin/\S+/")
    backup_regex=re.compile("~$|\#[^/]+\#$")
    compr_regex=re.compile("\.(gz|z|Z|zip|bz2)$")
    absolute_regex=re.compile("^/([^/]+)")
    absolute2_regex=re.compile("^/?([^/]+)")
    points_regex=re.compile("^../(.*)")
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "FilesCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return
	
	files=pkg.files()
	config_files=pkg.configFiles()
	for f in files.keys():
	    enreg=files[f]
	    mode=enreg[0]
	    if FilesCheck.tmp_regex.search(f):
		print "E:", pkg.name, "dir-or-file-in-tmp", f
	    elif FilesCheck.mnt_regex.search(f):
		print "E:", pkg.name, "dir-or-file-in-mnt", f
	    elif FilesCheck.opt_regex.search(f):
		print "E:", pkg.name, "dir-or-file-in-opt", f
	    elif FilesCheck.sub_bin_regex.search(f):
		print "E:", pkg.name, "subdir-in-bin", f
	    elif FilesCheck.backup_regex.search(f):
		print "E:", pkg.name, "backup-file-in-package", f
	    if FilesCheck.etc_regex.search(f) and stat.S_ISREG(mode):
		if not f in config_files:
		    print "W:", pkg.name, "non-conffile-in-etc", f
	    link=enreg[3]
	    if link != '':
		ext=FilesCheck.compr_regex.search(link)
		if ext:
		    if not re.compile("\." + ext.group(1) + "$").search(f):
			print "E:", pkg.name, "compressed-symlink-with-wrong-ext", f, link

	    perm=mode & 07777

	    # bit s check
	    if stat.S_ISGID & mode or stat.S_ISUID & mode:
		# check only normal files
		if stat.S_ISREG(mode):
		    user=enreg[1]
		    group=enreg[2]
		    setuid=None
		    setgid=None
		    if stat.S_ISUID & mode:
			setuid=user
		    if stat.S_ISGID & mode:
			setgid=group
		    if setuid and setgid:
			print "W:", pkg.name, "setuid-gid-binary", f, setuid, setgid, oct(perm)
		    elif setuid:
			print "W:", pkg.name, "setuid-binary", f, setuid, oct(perm)
		    elif setgid:
			print "W:", pkg.name, "setgid-binary", f, setgid, oct(perm)
		    elif mode & 0777 != 0755:
			print "W:", pkg.name, "non-standard-executable-perm", f, oct(perm)

	    # normal executable check
	    elif stat.S_ISREG(mode) and mode & stat.S_IXUSR:
		if perm != 0755:
		    print "W:", pkg.name, "non-standard-executable-perm", f, oct(perm)
		    
	    # normal dir check
	    elif stat.S_ISDIR(mode) and perm != 0755:
		print "W:", pkg.name, "non-standard-dir-perm", f, oct(perm)

	    # symbolic link check
	    elif stat.S_ISLNK(mode):
		r=FilesCheck.absolute_regex.search(link)
		# absolute link
		if r:
		    linktop=r.group(1)
		    r=FilesCheck.absolute_regex.search(f)
		    if r:
			filetop=r.group(1)
			if filetop == linktop:
			    # absolute links within one toplevel directory are _not_ ok!
			    print "E:", pkg.name ,"symlink-should-be-relative", f, link
		# relative link
		else:
		    pathcomponents=string.split(f, '/')[1:]
		    r=FilesCheck.points_regex.search(link)
		    lastpop=None
		    mylink=None
		    
		    while r:
			mylink=r.group(1)
			if len(pathcomponents) == 0:
			    print "E:", pkg.name, "symlink-has-too-many-up-segments", f, link
			    break
			else:
			    lastpop=pathcomponents[0]
			    pathcomponents=pathcomponents[1:]
			    r=FilesCheck.points_regex.search(mylink)

		    if mylink and lastpop:
			r=FilesCheck.absolute2_regex.search(mylink)
			linktop=r.group(1)
			
			# does the link go up and then down into the same directory?
			if linktop == lastpop:
			    print "W:", pkg.name, "lengthy-symlink", f, link
		    
			if len(pathcomponents) == 0:
			    # we've reached the root directory
			    if linktop != lastpop:
				# relative link into other toplevel directory
				print "W:", pkg.name, "symlink-should-be-absolute", f, link
			# check additional segments for mistakes like `foo/../bar/'
			for linksegment in string.split(mylink, '/'):
			    if linksegment == '..':
				print "E:", pkg.name, "symlink-contains-up-and-down-segments", f, link
			    
# Create an object to enable the auto registration of the test
check=FilesCheck()

# FilesCheck.py ends here
