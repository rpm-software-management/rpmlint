#############################################################################
# File		: Config.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Fri Oct 15 20:04:25 1999
# Version	: $Id$
# Purpose	: handle configuration options. To be used from config files.
#############################################################################

import os.path
import re

DEFAULT_CHECKS=("DistributionCheck",
		"TagsCheck",
		"BinariesCheck",
		"ConfigCheck",
		"FilesCheck",
		"FHSCheck",
		"SignatureCheck",
		"I18NCheck",
                "MenuCheck",
                "PostCheck",
                "InitScriptCheck",
		"SourceCheck")

# handle the list of checks to load
_checks=[]

def addCheck(check):
    global _checks
    
    if not check in _checks:
	_checks.append(check)

def allChecks():
    global _checks
    
    if _checks == []:
	_checks=DEFAULT_CHECKS
    return _checks

def defaultChecks():
    global _checks

    _checks=DEFAULT_CHECKS
    
def resetChecks():
    global _checks

    _checks=[]
    
# handle the list of directories to look for checks

_dirs=["/usr/share/rpmlint"]

def addCheckDir(dir):
    global _dirs

    dir=os.path.expanduser(dir)
    
    if not dir in _dirs:
	_dirs.insert(0, dir)

def checkDirs():
    global _dirs

    return _dirs

# handle options

_options={}

def setOption(name, value):
    global _options

    _options[name]=value

def getOption(name, default):
    global _options
    
    try:
	return _options[name]
    except KeyError:
	return default

# List of filters
_filters=[]

def addFilter(s):
    global _filters

    _filters.append(re.compile(s))

def isFiltered(s):
    global _filters

    for f in _filters:
	if f.search(s):
	    return 1
    return 0
    
# Standard exceptions:
addFilter("W: rootfiles non-etc-or-var-file-marked-as-conffile /root/.*")
addFilter("E: (rootfiles|etcskel) non-standard-dir-perm /(root|etc/skel)/tmp")
addFilter("E: rootfiles non-standard-dir-perm (/root|/etc/skel)/tmp")
addFilter("E: man(-[^ ]+)? non-standard-dir-perm /var/(X11R6/)?catman[^ ]+ 0775")
addFilter("E: man(-[^ ]+)? non-standard-dir-perm /usr/(X11R6/)?man/[^ ]+ 02755")
addFilter("E: filesystem non-standard-dir-perm /var/lock/subsys 0775")
addFilter("E: filesystem non-standard-dir-perm /tmp 01777")
addFilter("E: filesystem non-standard-dir-perm /var/tmp 01777")
addFilter("E: filesystem (non-standard-dir-perm|dir-or-file-in-mnt) /mnt/(floppy|disk|cdrom)")
addFilter("E: filesystem non-standard-dir-perm /var/spool/mail 0775")
addFilter("E: filesystem non-standard-dir-perm /root 0750")
addFilter("E: filesystem non-standard-dir-perm /var/lock 0775")
addFilter("E: filesystem non-standard-dir-perm /proc 0555")
addFilter("E: postgresql-test non-standard-[gu]id [^ ]+ postgres")
addFilter("E: sympa non-standard-[gu]id /home/sympa/[^ ]+ sympa")
addFilter("W: (dev86|compat-glibc|alsa|alsa-sourcecompat-libs|gcc|egcs|egcs-c\+\+|gcc-chill|gcc-f77|egcs-g77|gcc-libgcj|gcc-objc|hackkernel-source|hackkernel-headers|kernel-source|kernel-headers|octave|ghc|mercury|ocaml|gprolog|ruby-extensions|ruby|XFree86-static-libs) devel-file-in-non-devel-package")
addFilter("W: menu devel-file-in-non-devel-package /etc/menu-methods/menu.h")
addFilter("W: [^ ]+ devel-file-in-non-devel-package /usr/doc/.*\.h$")
addFilter("W: glibc-profile devel-file-in-non-devel-package .*\.a$")
addFilter("E: anonftp dir-or-file-in-home /home/ftp/")
addFilter("E: [^ ]+ dir-or-file-in-home /home/httpd/")
addFilter("E: sympa dir-or-file-in-home /home/sympa/")
addFilter("E: menu non-file-in-menu-dir /usr/lib/menu/default")
addFilter("I: menu unable-to-parse-menu-command")
addFilter("W: menu invalid-menu-section")
addFilter("W: XFree86-server devel-file-in-non-devel-package /usr/X11R6/lib/modules")
addFilter("W: icewm-light menu-command-not-in-package icewm")
addFilter("E: slocate non-standard-dir-perm /var/lib/slocate 0750")
addFilter("E: ld.so statically-linked-binary /sbin/ldconfig")
addFilter("W: shadow-utils dangling-symlink /usr/bin/sg newgrp")
addFilter("E: rpm statically-linked-binary /bin/rpm")

#initscripts
addFilter("W: initscripts non-etc-or-var-file-marked-as-conffile /sbin/if(up|down)")
addFilter("E: initscripts (setuid|setgid)-binary (/usr/sbin/usernetctl|/sbin/netreport) root.*")
addFilter("E: initscripts non-standard-dir-perm /var/run/netreport 0775")


#Setuid
addFilter("E: traceroute setuid-binary /usr/sbin/traceroute root 04755")
addFilter("E: urpmi setuid-binary /usr/bin/urpmi root 04750")
addFilter("E: sash statically-linked-binary /sbin/sash")
addFilter("E: perl-base setuid-binary /usr/bin/sperl5.6.0 root 04711")
addFilter("E: perl-base setuid-binary /usr/bin/suidperl root 04711")
addFilter("E: procmail setgid-binary /usr/bin/lockfile mail 02755")
addFilter("E: procmail setuid-gid-binary /usr/bin/procmail root mail 06755")
addFilter("E: rsh setuid-binary /usr/bin/rlogin root 04755")
addFilter("E: rsh setuid-binary /usr/bin/rsh root 04755")
addFilter("E: rsh setuid-binary /usr/bin/rcp root 04755")
addFilter("E: man setgid-binary /usr/bin/man man 02755")
addFilter("E: sudo non-standard-dir-perm /var/run/sudo 0700")
addFilter("E: sudo setuid-binary /usr/bin/sudo root 04111")
addFilter("E: slocate setgid-binary /usr/bin/slocate slocate 02755")
addFilter("E: SysVinit setgid-binary /usr/bin/wall tty 02555")
addFilter("E: sh-utils setuid-binary /bin/su root 04755")
addFilter("E: netkit-base setuid-binary /bin/ping root 04755")
addFilter("E: e2fsprogs statically-linked-binary /sbin/.*fsck.*")
addFilter("E: mount setuid-binary /bin/(u)?mount root 04755")
addFilter("E: util-linux setuid-binary /usr/bin/(newgrp|chsh|chfn) root 04711")
addFilter("E: util-linux setgid-binary /usr/bin/write tty 02755")

#Pam
addFilter("W: pam devel-file-in-non-devel-package /lib/security/pam_unix_(session|passwd|acct|auth).so")
addFilter("E: pam setuid-binary /sbin/(unix|pwdb)_chkpwd root 04(5|7)55")
addFilter("E: pam subdir-in-bin /sbin/pam_filter/upperLOWER")

#Kernel
addFilter("W: alsa(-source)? incoherent-version-in-changelog.*")
addFilter("W: kernel-headers dangling-symlink /usr/include/asm ../src/linux/include/asm")
addFilter("W: kernel-source dangling-symlink .*/linux/config.h ../pcmcia/config.h")
addFilter("W: reiserfs-utils dangling-symlink /sbin/fsck.reiserfs.*")
addFilter("W: reiserfs-utils incoherent-version-in-changelog")

#Glibc
addFilter("W: glibc shared-lib-without-dependency-information /lib/ld-2.1.3.so")
addFilter("W: glibc library-not-linked-against-libc /lib/libc-2.1.3.so")
addFilter("E: glibc statically-linked-binary /sbin/sln")
addFilter("E: glibc setuid-binary /usr/libexec/pt_chown root 04755")

#Transparent-xpm
addFilter("W: mathplot non-transparent-xpm ")

# InitScriptCheck exceptions
addFilter("E: initscripts (no-chkconfig-line|incoherent-subsys)")
addFilter("E: squid incoherent-subsys /etc/rc.d/init.d/squid $SQUID")
addFilter("E: heartbeat incoherent-subsys /etc/rc.d/init.d/heartbeat $SUBSYS")

# non-conffile-in-etc
addFilter("W: mandrake-release non-conffile-in-etc /etc/mandrake-release")

# Config.py ends here
