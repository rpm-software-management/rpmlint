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

# must be kept in sync with the filesystem package
STANDARD_DIRS=(
    '/bin',
    '/boot',
    '/etc',
    '/etc/X11',
    '/etc/opt',
    '/etc/skel',
    '/etc/xinetd.d',
    '/home',
    '/lib',
    '/lib64',
    '/lib/modules',
    '/mnt',
    '/mnt/cdrom',
    '/mnt/disk',
    '/mnt/floppy',
    '/opt',
    '/proc',
    '/root',
    '/sbin',
    '/tmp',
    '/usr',
    '/usr/X11R6',
    '/usr/X11R6/bin',
    '/usr/X11R6/doc',
    '/usr/X11R6/include',
    '/usr/X11R6/lib',
    '/usr/X11R6/lib64',
    '/usr/X11R6/man',
    '/usr/X11R6/man/man1',
    '/usr/X11R6/man/man2',
    '/usr/X11R6/man/man3',
    '/usr/X11R6/man/man4',
    '/usr/X11R6/man/man5',
    '/usr/X11R6/man/man6',
    '/usr/X11R6/man/man7',
    '/usr/X11R6/man/man8',
    '/usr/X11R6/man/man9',
    '/usr/X11R6/man/mann',
    '/usr/bin',
    '/usr/bin/X11',
    '/usr/etc',
    '/usr/games',
    '/usr/include',
    '/usr/lib',
    '/usr/lib64',
    '/usr/lib/X11',
    '/usr/lib/games',
    '/usr/lib/gcc-lib',
    '/usr/lib64/gcc-lib',
    '/usr/local',
    '/usr/local/bin',
    '/usr/local/doc',
    '/usr/local/etc',
    '/usr/local/games',
    '/usr/local/info',
    '/usr/local/lib',
    '/usr/local/lib64',
    '/usr/local/man',
    '/usr/local/man/man1',
    '/usr/local/man/man2',
    '/usr/local/man/man3',
    '/usr/local/man/man4',
    '/usr/local/man/man5',
    '/usr/local/man/man6',
    '/usr/local/man/man7',
    '/usr/local/man/man8',
    '/usr/local/man/man9',
    '/usr/local/man/mann',
    '/usr/local/sbin',
    '/usr/local/src',
    '/usr/sbin',
    '/usr/share',
    '/usr/share/dict',
    '/usr/share/icons',
    '/usr/share/doc',
    '/usr/share/info',
    '/usr/share/man',
    '/usr/share/man/man1',
    '/usr/share/man/man2',
    '/usr/share/man/man3',
    '/usr/share/man/man4',
    '/usr/share/man/man5',
    '/usr/share/man/man6',
    '/usr/share/man/man7',
    '/usr/share/man/man8',
    '/usr/share/man/man9',
    '/usr/share/man/mann',
    '/usr/share/misc',
    '/usr/src',
    '/usr/tmp',
    '/var',
    '/var/cache',
    '/var/db',
    '/var/lib',
    '/var/lib/games',
    '/var/lib/misc',
    '/var/lib/rpm',
    '/var/local',
    '/var/lock',
    '/var/lock/subsys',
    '/var/log',
    '/var/mail',
    '/var/nis',
    '/var/opt',
    '/var/preserve',
    '/var/run',
    '/var/spool',
    '/var/spool/mail',
    '/var/tmp',
    '/etc/profile.d'
    )

DEFAULT_GAMES_GROUPS='Games'

DEFAULT_DANGLING_EXCEPTIONS = (['consolehelper$', 'usermode'],
                               )

tmp_regex=re.compile('^/tmp/|^(/var|/usr)/tmp/')
mnt_regex=re.compile('^/mnt/')
opt_regex=re.compile('^/opt/')
home_regex=re.compile('^/home/')
etc_regex=re.compile('^/etc/')
sub_bin_regex=re.compile('^(/usr)?/s?bin/\S+/')
backup_regex=re.compile('~$|\#[^/]+\#$')
compr_regex=re.compile('\.(gz|z|Z|zip|bz2)$')
absolute_regex=re.compile('^/([^/]+)')
absolute2_regex=re.compile('^/?([^/]+)')
points_regex=re.compile('^../(.*)')
doc_regex=re.compile('^/usr/(doc|man|info)|^/usr/share/(doc|man|info)')
bin_regex=re.compile('^(/usr)?/s?bin/')
includefile_regex=re.compile('\.[ch]$|\.a$')
sofile_regex=re.compile('/lib(64)?/[^/]+\.so$')
devel_regex=re.compile('-(devel|source)$')
lib_regex=re.compile('lib(64)?/lib[^/]*\.so\..*')
ldconfig_regex=re.compile('^[^#]*ldconfig', re.MULTILINE)
info_regex=re.compile('^/usr/share/info')
install_info_regex=re.compile('^[^#]*install-info', re.MULTILINE)
perl_temp_file=re.compile('.*perl.*(bs|\.packlist)$')
cvs_regex=re.compile('/CVS/[^/]+$|/.cvsignore$')
games_path_regex=re.compile('/usr/(lib/)?/games')
games_group_regex=re.compile(Config.getOption('RpmGamesGroups', DEFAULT_GAMES_GROUPS))
source_regex=re.compile('(.c|.cc|.cpp|.ui)$')
dangling_exceptions=Config.getOption('DanglingSymlinkExceptions', DEFAULT_DANGLING_EXCEPTIONS)
logrotate_regex=re.compile('^/etc/logrotate.d/(.*)')
kernel_modules_regex=re.compile('^/lib/modules/')
kernel_package_regex=re.compile('^kernel(22)?(-)?(smp|enterprise|secure|BOOT)?')
normal_zero_length_regex=re.compile('^/etc/security/console.apps/|/.nosearch$|/__init__.py$')
perl_regex=re.compile('^/usr/lib/perl5/(?:site_perl/)?([0-9]+\.[0-9]+)\.([0-9]+)/')
python_regex=re.compile('^/usr/lib/python([.0-9]+)/')
cross_compile_regex=re.compile('-mandrake-linux-[^/]+$')
perl_version_trick=Config.getOption('PerlVersionTrick', 1)
log_regex=re.compile('^/var/log/[^/]+$')
lib_path_regex=re.compile('^(/usr(/X11R6)?)?/lib(64)?')
lib_package_regex=re.compile('^(lib|.+-libs)')
hidden_file_regex=re.compile('/\.[^/]*$')

for idx in range(0, len(dangling_exceptions)):
    dangling_exceptions[idx][0]=re.compile(dangling_exceptions[idx][0])

class FilesCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, 'FilesCheck')

    def check(self, pkg):
	# Check only binary package
	if pkg.isSource():
	    return

        # Check if the package is a development package
	devel_pkg=devel_regex.search(pkg.name)

	files=pkg.files()
	config_files=pkg.configFiles()
	ghost_files=pkg.ghostFiles()
	doc_files=pkg.docFiles()
        req_names=pkg.req_names()
        deps=pkg.requires()+pkg.prereq()
        prein=pkg[rpm.RPMTAG_PREIN]
        lib_package=lib_package_regex.search(pkg.name)

        # erport these errors only once
        perl_dep_error=0
        python_dep_error=0
        lib_file=0
        non_lib_file=0
        
        if doc_files == [] and not (pkg.name[:3] == 'lib' and string.find(pkg.name, '-devel')):
	    printWarning(pkg, 'no-documentation')
	    
	for f in files.keys():
	    enreg=files[f]
	    mode=enreg[0]
	    user=enreg[1]
	    group=enreg[2]
            size=enreg[4]
            
	    if not user in Config.STANDARD_USERS:
		printError(pkg, 'non-standard-uid', f, user)
	    if not group in Config.STANDARD_GROUPS:
		printError(pkg, 'non-standard-gid', f, group)

            if kernel_modules_regex.search(f) and not kernel_package_regex.search(pkg.name):
                printError(pkg, "kernel-modules-not-in-kernel-packages", f)
                
            if tmp_regex.search(f):
		printError(pkg, 'dir-or-file-in-tmp', f)
	    elif mnt_regex.search(f):
		printError(pkg, 'dir-or-file-in-mnt', f)
	    elif opt_regex.search(f):
		printError(pkg, 'dir-or-file-in-opt', f)
	    elif sub_bin_regex.search(f):
		printError(pkg, 'subdir-in-bin', f)
	    elif backup_regex.search(f):
		printError(pkg, 'backup-file-in-package', f)
            elif home_regex.search(f):
		printError(pkg, 'dir-or-file-in-home', f)
            elif cvs_regex.search(f):
		printError(pkg, 'cvs-internal-file', f)
	    elif hidden_file_regex.search(f):	
		printWarning(pkg, 'hidden-file-or-dir', f)
            elif f == '/usr/info/dir' or f == '/usr/share/info/dir':
                printError(pkg, 'info-dir-file', f)

            res=logrotate_regex.search(f)
            if res and res.group(1) != pkg.name:
                printError(pkg, 'incoherent-logrotate-file', f)
	    if etc_regex.search(f) and stat.S_ISREG(mode):
		if not f in config_files and not f in ghost_files:
		    printWarning(pkg, 'non-conffile-in-etc', f)
	    link=enreg[3]
	    if link != '':
		ext=compr_regex.search(link)
		if ext:
		    if not re.compile('\.' + ext.group(1) + '$').search(f):
			printError(pkg, 'compressed-symlink-with-wrong-ext', f, link)

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
			printError(pkg, 'setuid-gid-binary', f, setuid, setgid, oct(perm))
		    elif setuid:
			printError(pkg, 'setuid-binary', f, setuid, oct(perm))
		    elif setgid:
                        if not (group == 'games' and
                                (games_path_regex.search(f) or games_group_regex.search(pkg[rpm.RPMTAG_GROUP]))):
                            printError(pkg, 'setgid-binary', f, setgid, oct(perm))
		    elif mode & 0777 != 0755:
			printError(pkg, 'non-standard-executable-perm', f, oct(perm))

            # normal file check
            if stat.S_ISREG(mode):

                if not devel_pkg:
                    if lib_path_regex.search(f):
                        lib_file=1
                    elif f not in doc_files:
                        non_lib_file=f

                if log_regex.search(f):
                    if user != 'root':
                        printError(pkg, 'non-root-user-log-file', f, user)
                    if group != 'root':
                        printError(pkg, 'non-root-group-log-file', f, group)
                    if not f in ghost_files:
                        printError(pkg, 'non-ghost-file', f)
                        
                if doc_regex.search(f) and not f in doc_files:
                    printError(pkg, 'not-listed-as-documentation', f)
                #elif cross_compile_regex.search(f):
                #    printError(pkg, 'cross-compile-name', f)

                # check ldconfig call in %post and %postun
                if lib_regex.search(f):
                    postin=pkg[rpm.RPMTAG_POSTIN] or pkg[rpm.RPMTAG_POSTINPROG]
                    if not postin:
                        printError(pkg, 'library-without-ldconfig-postin', f)
                    else:
                        if not ldconfig_regex.search(postin):
                            printError(pkg, 'postin-without-ldconfig', f)                    
                        
                    postun=pkg[rpm.RPMTAG_POSTUN] or pkg[rpm.RPMTAG_POSTUNPROG]
                    if not postun:
                        printError(pkg, 'library-without-ldconfig-postun', f)
                    else:
                        if not ldconfig_regex.search(postun):
                            printError(pkg, 'postun-without-ldconfig', f)
                    
                # check install-info call in %post and %postun
                if info_regex.search(f):
                    postin=pkg[rpm.RPMTAG_POSTIN]
                    if not postin:
                        printError(pkg, 'info-files-without-install-info-postin', f)
                    else:
                        if not install_info_regex.search(postin):
                            printError(pkg, 'postin-without-install-info', f)                    
                        
                    postun=pkg[rpm.RPMTAG_POSTUN]
                    preun=pkg[rpm.RPMTAG_PREUN]
                    if not postun and not preun:
                        printError(pkg, 'info-files-without-install-info-postun', f)
                    else:
                        if (not postun or not install_info_regex.search(postun)) and \
                           (not preun or not install_info_regex.search(preun)):
                            printError(pkg, 'postin-without-install-info', f)
    
               
                # check perl temp file
                if perl_temp_file.search(f):
                    printWarning(pkg, 'perl-temp-file', f)

                if bin_regex.search(f) and mode & 0111 == 0:
                    printWarning(pkg, 'non-executable-in-bin', f, oct(perm))
                if not devel_pkg and includefile_regex.search(f) and not f in doc_files:
                    printWarning(pkg, 'devel-file-in-non-devel-package', f)
                if mode & 0444 != 0444 and perm & 07000 == 0 and f[0:len('/var/log')] != '/var/log':
                    printError(pkg, 'non-readable', f, oct(perm))
                if size == 0 and not normal_zero_length_regex.search(f) and f not in ghost_files:
                    printError(pkg, 'zero-length', f)

                if not perl_dep_error:
                    res=perl_regex.search(f)
                    if res:
                        if perl_version_trick:
                            vers = res.group(1) + '0' + res.group(2)
                        else:
                            vers = res.group(1) + res.group(2)
                        if not (pkg.check_versioned_dep('perl-base', vers) or
                                pkg.check_versioned_dep('perl', vers)):
                            printError(pkg, 'no-dependancy', 'perl-base', vers)
                            perl_dep_error=1

                if not python_dep_error:
                    res=python_regex.search(f)
                    if res:
                        if not (pkg.check_versioned_dep('python-base', res.group(1)) or
                                pkg.check_versioned_dep('python', res.group(1))):
                            printError(pkg, 'no-dependancy', 'python-base', res.group(1))
                            python_dep_error=1
                
	    # normal executable check
	    elif stat.S_ISREG(mode) and mode & stat.S_IXUSR:
		if perm != 0755:
		    printError(pkg, 'non-standard-executable-perm', f, oct(perm))
		    
	    # normal dir check
            elif stat.S_ISDIR(mode):
                if perm != 0755:
                    printError(pkg, 'non-standard-dir-perm', f, oct(perm))
                if pkg[rpm.RPMTAG_NAME] != 'filesystem':
                    if f in STANDARD_DIRS:
                        printError(pkg, 'standard-dir-owned-by-package', f)
		if hidden_file_regex.search(f):	
			printWarning(pkg, 'hidden-file-or-dir', f)
 	

	    # symbolic link check
	    elif stat.S_ISLNK(mode):
		r=absolute_regex.search(link)
                is_so=sofile_regex.search(f)
                if not devel_pkg and is_so:
                    printWarning(pkg, 'devel-file-in-non-devel-package', f)
		# absolute link
		if r:
                    if (not is_so) and link not in files.keys():
                        is_exception=0
                        for e in dangling_exceptions:
                            if e[0].search(link):
                                is_exception=e[1]
                                break
                        if is_exception:
                            if is_exception not in req_names:
                                printWarning(pkg, 'no-dependancy-on', is_exception)
                        else:
                            printWarning(pkg, 'dangling-symlink', f, link)
		    linktop=r.group(1)
		    r=absolute_regex.search(f)
		    if r:
			filetop=r.group(1)
			if filetop == linktop:
			    # absolute links within one toplevel directory are _not_ ok!
			    printWarning(pkg ,'symlink-should-be-relative', f, link)
		# relative link
		else:
                    if not is_so:
                        file = '%s%s/%s' % (pkg.dirName(), os.path.dirname(f), link)
                        file = os.path.normpath(file)
                        pkgfile = '%s/%s' % (os.path.dirname(f), link)
                        pkgfile = os.path.normpath(pkgfile)
                        if not (files.has_key(pkgfile) or os.path.exists(file)):
                            is_exception=0
                            for e in dangling_exceptions:
                                if e[0].search(link):
                                    is_exception=e[1]
                                    break
                            if is_exception:
                                if not is_exception in map(lambda x: x[0], pkg.requires() + pkg.prereq()):
                                    printWarning(pkg, 'no-dependancy-on', is_exception)
                            else:
                                printWarning(pkg, 'dangling-relative-symlink', f, link)
		    pathcomponents=string.split(f, '/')[1:]
		    r=points_regex.search(link)
		    lastpop=None
		    mylink=None
		    
		    while r:
			mylink=r.group(1)
			if len(pathcomponents) == 0:
			    printError(pkg, 'symlink-has-too-many-up-segments', f, link)
			    break
			else:
			    lastpop=pathcomponents[0]
			    pathcomponents=pathcomponents[1:]
			    r=points_regex.search(mylink)

		    if mylink and lastpop:
			r=absolute2_regex.search(mylink)
			linktop=r.group(1)
			
			# does the link go up and then down into the same directory?
			#if linktop == lastpop:
			#    printWarning(pkg, 'lengthy-symlink', f, link)
		    
			if len(pathcomponents) == 0:
			    # we've reached the root directory
			    if linktop != lastpop:
				# relative link into other toplevel directory
				printWarning(pkg, 'symlink-should-be-absolute', f, link)
			# check additional segments for mistakes like `foo/../bar/'
			for linksegment in string.split(mylink, '/'):
			    if linksegment == '..':
				printError(pkg, 'symlink-contains-up-and-down-segments', f, link)
        if lib_package and lib_file and non_lib_file:
            printError(pkg, 'outside-libdir-files', non_lib_file)
            
# Create an object to enable the auto registration of the test
check=FilesCheck()

if Config.info:
    addDetails(
'no-documentation',
'''The package contains no documentation (README, doc, etc).
You have to include documentation files.''',

'not-listed-as-documentation',
'''The documentation files of this package are not listed with
the standard %doc tag.''',

'non-standard-uid',
'''A file in this package is owned by a non standard owner.
Standard owners are:

- root		- bin
- daemon	- adm
- lp		- sync
- shutdown	- halt
- mail		- news
- uucp		- operator
- games		- gopher
- ftp		- nobody
- nobody	- lists
- gdm		- xfs
- apache	- postgres
- rpcuser	- rpm''',

'non-standard-gid',
'''A file in this package is owned by a non standard group.
Standard groups are:

- root		- bin		- dip
- daemon	- sys		- ftp
- adm		- tty		- smb
- disk		- lp		- cdrom
- mem		- kmem		- pppusers
- wheel		- floppy	- cdwriter
- mail		- news		- audio
- uucp		- man		- dos
- games		- gopher	- nobody
- users		- console	- utmp
- lists		- gdm		- xfs
- popusers	- slipusers	- slocate
- x10		- urpmi		- apache
- postgres	- rpcuser	- rpm''',

'library-without-ldconfig-postin',
'''This package contains a library and provides no %post with a call to ldconfig.''',

'postin-without-ldconfig',
'''This package contains a library and its %post doesn't call ldconfig.''',

'library-without-ldconfig-postun',
'''This package contains a library and provides no %postun with a call to ldconfig.''',

'postun-without-ldconfig',
'''This package contains a library and its %postun doesn't call ldconfig.''',

'info-files-without-install-info-postin',
'''This package contains info files and provides no %post with a call to install-info.''',

'postin-without-install-info',
'''This package contains info files and its %post doesn't call install-info.''',

'info-files-without-install-info-postun',
'''This package contains info files and provides no %postun with a call to install-info.''',

'postun-without-install-info',
'''This package contains info files and its %postun doesn't call install-info.''',

'perl-temp-file',
'''You have a perl temporary file in your package. Usually, this
file is beginning with a dot (.) and contain "perl" in its name.''',

'dir-or-file-in-tmp',
'''A file in the package is located in /tmp. It's not permitted
to put a file in this directory.''',

'dir-or-file-in-mnt',
'''A file in the package is located in /mnt. It's not permitted
to put a file in this directory.''',

'dir-or-file-in-opt',
'''A file in the package is located in /opt. It's not permitted
to put a file in this directory.''',

'subdir-in-bin',
'''The package contains a sub-directory in the /usr/bin. You can't
create a subdir there. Create it in /usr/lib/ instead.''',

'backup-file-in-package',
'''You have a backup file in your package. The files are usually
beginning with ~ (vi) or #file# (emacs). Please remove it and rebuild
your package.''',

'dir-or-file-in-home',
'''A file in the package is located in /home. It's not permitted
to put a file in this directory.''',

'cvs-internal-file',
'''You have file(s) from your CVS build directory. Move your CVS directory
out of the package and rebuild it.''',

'info-dir-file',
'''You have /usr/info/dir or /usr/share/info/dir in your package. It's not allowed.
Please remove it and rebuild your package.''',

'non-conffile-in-etc',
'''A file in your package is being installed in /etc, but is not a
configuration file. All the files in /etc MUST be configuration files
(add the %config option to the file in the spec file).''',

'compressed-symlink-with-wrong-ext',
'''The symlink points to a compressed file but doesn't use the same extension.''',

'setuid-gid-binary',
'''The file is setuid and setgid. Usually this is a bug. Otherwise, please contact
<flepied@mandrakesoft.com> about this so that this error gets included
in the exception file for rpmlint. With that, rpmlint will ignore
this bug in the future.''',

'setuid-binary',
'''The file is setuid. Usually this is a bug. Otherwise, please contact
<flepied@mandrakesoft.com> about this so that this error gets included
in the exception file for rpmlint. With that, rpmlint will ignore
this bug in the future.''',

'setgid-binary',
'''The file is setgid. Usually this is a bug. Otherwise, please contact
<flepied@mandrakesoft.com> about this so that this error gets included
in the exception file for rpmlint. With that, rpmlint will ignore
this bug in the future.''',

'non-standard-executable-perm',
'''A standard executable should have permission set to 0755. If you get this message,
that means that you have a wrong executable permission in your package.''',

'non-executable-in-bin',
'''A file is being installed in /usr/bin, but is not an executable. Be sure
that the file is an executable or that it has executable permissions.''',

'devel-file-in-non-devel-package',
'''A development file (usually source code) is located in a non-devel
package. If you want to include source code in your package, be sure to
create a development package.''',


'non-standard-dir-perm',
'''A standard directory should have permission set to 0755. If you get this message,
that means that you have a wrong directory permission in your package.''',

'standard-dir-owned-by-package',
'''This package owns a directory that is part of the standard hierarchy and this
can lead to default directory rights, owner or group be changed to something
non standard.''',

'no-dependancy-on',
'''
''',

'dangling-symlink',
'''The symbolik link points nowhere.''',

'symlink-should-be-relative',
'''
''',

'dangling-relative-symlink',
'''The relative symbolik link points nowhere.''',

'symlink-has-too-many-up-segments',
'''
''',

'symlink-should-be-absolute',
'''
''',

'symlink-contains-up-and-down-segments',
'''
''',

'non-readable',
'''The file can't be read by everybody. If this is normal (for security reason), send an
email to flepied@mandrakesoft.com to add it to the list of exceptions in the next release.''',

'incoherent-logrotate-file',
'''Your logrotate file should be named /etc/logrotate.d/<package name>.''',

'non-root-user-log-file',
'''If you need non root log file, just create a subdir in /var/log and put your files inside.''',

'non-root-group-log-file',
'''If you need non root log file, just create a subdir in /var/log and put your files inside.''',

'non-ghost-file',
'''File should be tagged %ghost.''',

'outside-libdir-files',
'''This library package must not contain non library files to allow 64
and 32 bits versions of the package to coexist.''',

'hidden-file-or-dir',
'''The file or directory is hidden. You should see if this is normal, 
and delete it if needed''',
)

# FilesCheck.py ends here
