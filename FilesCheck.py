#############################################################################
# File		: FilesCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Mon Oct  4 19:32:49 1999
# Version	: $Id$
# Purpose	: test various aspects on files: locations, owner, groups,
#		permission, setuid, setgid...
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import re
import stat
import string
import os

STANDARD_USERS=('root','bin','daemon','adm','lp','sync','shutdown','halt','mail','news','uucp','operator','games','gopher','ftp','nobody','lists','gdm','xfs')

STANDARD_GROUPS=('root','bin','daemon','sys','adm','tty','disk','lp','mem','kmem','wheel','floppy','mail','news','uucp','man','games','gopher','dip','ftp','smb','cdrom','pppusers','cdwriter','audio','dos','nobody','users','console','utmp','lists','gdm','xfs','popusers','slipusers','slocate', 'x10', 'urpmi')

class FilesCheck(AbstractCheck.AbstractCheck):
    tmp_regex=re.compile("^/tmp/|^(/var|/usr)/tmp/")
    mnt_regex=re.compile("^/mnt/")
    opt_regex=re.compile("^/opt/")
    home_regex=re.compile("^/home/")
    etc_regex=re.compile("^/etc/")
    sub_bin_regex=re.compile("^(/usr)?/s?bin/\S+/")
    backup_regex=re.compile("~$|\#[^/]+\#$")
    compr_regex=re.compile("\.(gz|z|Z|zip|bz2)$")
    absolute_regex=re.compile("^/([^/]+)")
    absolute2_regex=re.compile("^/?([^/]+)")
    points_regex=re.compile("^../(.*)")
    doc_regex=re.compile("^/usr/(doc|man|info)|^/usr/share/(doc|man|info)")
    bin_regex=re.compile("^(/usr)?/s?bin/")
    includefile_regex=re.compile("\.h$|\.a$")
    sofile_regex=re.compile("\.so$")
    devel_regex=re.compile("-(devel|source)$")
    lib_regex=re.compile("lib/lib[^/]*\.so\..*")
    ldconfig_regex=re.compile("^[^#]*ldconfig",re.MULTILINE)
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "FilesCheck")

    def check(self, pkg, verbose):
	# Check only binary package
	if pkg.isSource():
	    return

        # Check if the package is a development package
	devel_pkg=FilesCheck.devel_regex.search(pkg.name)

	files=pkg.files()
	config_files=pkg.configFiles()
	ghost_files=pkg.ghostFiles()
	doc_files=pkg.docFiles()

	if doc_files == []:
	    printWarning(pkg, "no-documentation")
	    
	for f in files.keys():
	    enreg=files[f]
	    mode=enreg[0]
	    user=enreg[1]
	    group=enreg[2]

	    if stat.S_ISREG(mode) and FilesCheck.doc_regex.search(f) and not f in doc_files:
		printError(pkg, "not-listed-as-documentation", f)

	    if not user in STANDARD_USERS:
		printError(pkg, "non-standard-uid", f, user)
	    if not group in STANDARD_GROUPS:
		printError(pkg, "non-standard-gid", f, group)

            # check ldconfig call in %post and %postun
            if stat.S_ISREG(mode) and FilesCheck.lib_regex.search(f):
                postin=pkg[rpm.RPMTAG_POSTIN] or pkg[rpm.RPMTAG_POSTINPROG]
                if not postin:
                    printError(pkg, "library-without-ldconfig-postin", f)
                else:
                    if not FilesCheck.ldconfig_regex.search(postin):
                        printError(pkg, "postin-without-ldconfig", f)                    
                    
                postun=pkg[rpm.RPMTAG_POSTUN] or pkg[rpm.RPMTAG_POSTUNPROG]
                if not postun:
                    printError(pkg, "library-without-ldconfig-postun", f)
                else:
                    if not FilesCheck.ldconfig_regex.search(postun):
                        printError(pkg, "postun-without-ldconfig", f)

	    if FilesCheck.tmp_regex.search(f):
		printError(pkg, "dir-or-file-in-tmp", f)
	    elif FilesCheck.mnt_regex.search(f):
		printError(pkg, "dir-or-file-in-mnt", f)
	    elif FilesCheck.opt_regex.search(f):
		printError(pkg, "dir-or-file-in-opt", f)
	    elif FilesCheck.sub_bin_regex.search(f):
		printError(pkg, "subdir-in-bin", f)
	    elif FilesCheck.backup_regex.search(f):
		printError(pkg, "backup-file-in-package", f)
            elif FilesCheck.home_regex.search(f):
		printError(pkg, "dir-or-file-in-home", f)
            elif f == "/usr/info/dir" or f == "/usr/share/info/dir":
                printError(pkg, "info-dir-file", f)
	    if FilesCheck.etc_regex.search(f) and stat.S_ISREG(mode):
		if not f in config_files and not f in ghost_files:
		    printWarning(pkg, "non-conffile-in-etc", f)
	    link=enreg[3]
	    if link != '':
		ext=FilesCheck.compr_regex.search(link)
		if ext:
		    if not re.compile("\." + ext.group(1) + "$").search(f):
			printError(pkg, "compressed-symlink-with-wrong-ext", f, link)

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
			printError(pkg, "setuid-gid-binary", f, setuid, setgid, oct(perm))
		    elif setuid:
			printError(pkg, "setuid-binary", f, setuid, oct(perm))
		    elif setgid:
			printError(pkg, "setgid-binary", f, setgid, oct(perm))
		    elif mode & 0777 != 0755:
			printError(pkg, "non-standard-executable-perm", f, oct(perm))

            # normal file check
            if stat.S_ISREG(mode):
                if FilesCheck.bin_regex.search(f) and mode & 0111 == 0:
                    printWarning(pkg, "non-executable-in-bin", f, oct(perm))
                if not devel_pkg and FilesCheck.includefile_regex.search(f):
                    printWarning(pkg, "devel-file-in-non-devel-package", f)
                
	    # normal executable check
	    elif stat.S_ISREG(mode) and mode & stat.S_IXUSR:
		if perm != 0755:
		    printError(pkg, "non-standard-executable-perm", f, oct(perm))
		    
	    # normal dir check
            elif stat.S_ISDIR(mode):
                if perm != 0755:
                    printError(pkg, "non-standard-dir-perm", f, oct(perm))
#                 for file in files.keys():
#                     if f != file and string.find(file, f, 0) != -1:
#                         printInfo(pkg, "non-empty-dir-listed", f)
#                         break

	    # symbolic link check
	    elif stat.S_ISLNK(mode):
		r=FilesCheck.absolute_regex.search(link)
                is_so=FilesCheck.sofile_regex.search(f)
                if not devel_pkg and is_so:
                    printWarning(pkg, "devel-file-in-non-devel-package", f)
		# absolute link
		if r:
                    if not is_so and link not in files.keys():
                        printWarning(pkg, "dangling-symlink", f, link)
		    linktop=r.group(1)
		    r=FilesCheck.absolute_regex.search(f)
		    if r:
			filetop=r.group(1)
			if filetop == linktop:
			    # absolute links within one toplevel directory are _not_ ok!
			    printWarning(pkg ,"symlink-should-be-relative", f, link)
		# relative link
		else:
                    if not is_so:
                        file = '%s%s/%s' % (pkg.dirName(), os.path.dirname(f), link)
                        file = os.path.normpath(file)
                        if not os.path.exists(file):
                            printWarning(pkg, "dangling-symlink", f, link)
                            sys.exit(0)
		    pathcomponents=string.split(f, '/')[1:]
		    r=FilesCheck.points_regex.search(link)
		    lastpop=None
		    mylink=None
		    
		    while r:
			mylink=r.group(1)
			if len(pathcomponents) == 0:
			    printError(pkg, "symlink-has-too-many-up-segments", f, link)
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
			    printWarning(pkg, "lengthy-symlink", f, link)
		    
			if len(pathcomponents) == 0:
			    # we've reached the root directory
			    if linktop != lastpop:
				# relative link into other toplevel directory
				printWarning(pkg, "symlink-should-be-absolute", f, link)
			# check additional segments for mistakes like `foo/../bar/'
			for linksegment in string.split(mylink, '/'):
			    if linksegment == '..':
				printError(pkg, "symlink-contains-up-and-down-segments", f, link)
			    
# Create an object to enable the auto registration of the test
check=FilesCheck()

# FilesCheck.py ends here
