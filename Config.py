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
		"SourceCheck",
                "SpecCheck"
                )

info=0

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
addFilter('W: rootfiles non-etc-or-var-file-marked-as-conffile /root/.*')
addFilter('E: (rootfiles|etcskel) non-standard-dir-perm /(root|etc/skel)/tmp')
addFilter('E: rootfiles non-standard-dir-perm (/root|/etc/skel)/tmp')
addFilter('E: man(-[^ ]+)? non-standard-dir-perm /var/(X11R6/)?catman[^ ]+ 0775')
addFilter('E: man(-[^ ]+)? non-standard-dir-perm /usr/(X11R6/)?man/[^ ]+ 02755')
addFilter("W: filesystem dangling-relative-symlink /usr/lib/X11 ../X11R6/lib/X11")
addFilter("E: filesystem non-standard-dir-perm /usr/share/empty 0555")
addFilter('E: filesystem non-standard-dir-perm /var/lock/subsys 0775')
addFilter('E: filesystem non-standard-dir-perm /tmp 01777')
addFilter('E: filesystem non-standard-dir-perm /var/tmp 01777')
addFilter('E: filesystem (non-standard-dir-perm|dir-or-file-in-mnt) /mnt/(floppy|disk|cdrom)')
addFilter('E: filesystem non-standard-dir-perm /var/spool/mail 0775')
addFilter('E: filesystem non-standard-dir-perm /root 0750')
addFilter('E: filesystem non-standard-dir-perm /var/lock 0775')
addFilter('E: filesystem non-standard-dir-perm /proc 0555')
addFilter('E: postgresql-test non-standard-[gu]id [^ ]+ postgres')
addFilter('W: (binutils|dev86|compat-glibc|alsa|alsa-sourcecompat-libs|gcc|egcs|egcs-c\+\+|gcc-chill|gcc-f77|egcs-g77|gcc-libgcj|gcc-objc|hackkernel-source|hackkernel-headers|kernel-source|kernel-headers|octave|ghc|mercury|ocaml|gprolog|ruby-extensions|ruby|XFree86-static-libs|libwmf|doxygen|swi-prolog|ghc-prof|perl-(GTK.*|PDL|DBI)) devel-file-in-non-devel-package')
addFilter('W: menu devel-file-in-non-devel-package /etc/menu-methods/menu.h')
addFilter('W: [^ ]+ devel-file-in-non-devel-package /usr/doc/.*\.h$')
addFilter('W: glibc-profile devel-file-in-non-devel-package .*\.a$')
addFilter('E: menu non-file-in-menu-dir /usr/lib/menu/default')
addFilter('I: menu unable-to-parse-menu-command')
addFilter('W: menu invalid-menu-section')
addFilter('W: XFree86-server devel-file-in-non-devel-package /usr/X11R6/lib/modules')
addFilter('W: icewm-light menu-command-not-in-package icewm')
addFilter('E: slocate non-standard-dir-perm /var/lib/slocate 0750')
addFilter('E: ld.so statically-linked-binary /sbin/ldconfig')
addFilter('E: ocaml statically-linked-binary /sbin/ldconfig')
addFilter('W: shadow-utils dangling-symlink /usr/bin/sg newgrp')
addFilter('E: rpm statically-linked-binary /usr/bin/rpm2cpio|/bin/rpm')
addFilter('E: info-install info-dir-file /usr/share/info/dir')
addFilter('E: sympa non-standard-uid [^\s]+ sympa')
addFilter('E: sympa non-standard-gid [^\s]+ sympa')
addFilter('W: rpm dangerous-command-in-%post rpm')

#XFree86
addFilter('W: XFree86-server unstripped-binary-or-object /usr/X11R6/lib/modules/')
addFilter('E: XFree86-server statically-linked-binary /usr/X11R6/lib/modules/')
addFilter('W: XFree86.* postin-without-ghost-file-creation /usr/X11R6/lib/X11/fonts/')
addFilter('W: XFree86 dangling-relative-symlink /usr/X11R6/lib/X11/xinit ../../../../etc/X11/xinit')
addFilter('E: XFree86 non-standard-dir-perm /var/lib/xdm 0700')
addFilter('W: XFree86 dangling-relative-symlink /usr/X11R6/lib/X11/xserver ../../../.././etc/X11/xserver')

#db
addFilter('W: db[1-3]-devel no-provides db-devel')

#emacs
addFilter('W: emacs-X11 menu-command-not-in-package emacs')

#freetype
addFilter('W: freetype-devel no-major-in-name freetype-devel')

#openh323
addFilter('W: openh323_1-devel no-provides openh323_-devel')

#openssh
addFilter('W: openssh-clients dangling-relative-symlink /usr/bin/ssh-askpass ../..//usr/lib/ssh/ssh-askpass')

#tkinter
addFilter('E: tkinter normal-icon-not-in-package development_section.xpm /usr/lib/menu/tkinter')
addFilter('E: tkinter mini-icon-not-in-package development_section.xpm /usr/lib/menu/tkinter')
addFilter('E: tkinter large-icon-not-in-package development_section.xpm /usr/lib/menu/tkinter')
addFilter('E: tkinter normal-icon-not-in-package development_section.xpm /usr/lib/menu/tkinter')
addFilter('E: tkinter mini-icon-not-in-package development_section.xpm /usr/lib/menu/tkinter')
addFilter('E: tkinter large-icon-not-in-package development_section.xpm /usr/lib/menu/tkinter')

#menus
addFilter('W: bcast version-in-menu-title Broadcast 2000')
addFilter('W: xawtv version-in-menu-longtitle The X11 Video4Linux Stream Capture Viewer')

#ocaml
addFilter('W: ocaml unstripped-binary-or-object /usr/bin/(ocamldebug|ocamlbrowser)')

#initscripts
addFilter('W: initscripts non-etc-or-var-file-marked-as-conffile /sbin/if(up|down)')
addFilter('E: initscripts (setuid|setgid)-binary (/usr/sbin/usernetctl|/sbin/netreport) root.*')
addFilter('E: initscripts non-standard-dir-perm /var/run/netreport 0775')
addFilter("E:.*initscripts no-status-entry.*mandrake_(firstime|everytime).*")
addFilter("W:.*initscripts no-reload-entry.*mandrake_(firstime|everytime).*")
addFilter("E:.*initscripts subsys-not-used.*mandrake_(firstime|everytime).*")
addFilter("E:.*initscripts subsys-not-used.*/etc/rc.d/init.d/(halt|rawdevices)")
addFilter("E:.*initscripts no-status-entry.*/etc/rc.d/init.d/(killall|halt|single).*")
addFilter("W:.*initscripts no-(status|reload)-entry.*/etc/rc.d/init.d/(killall|halt|functions|single).*")
addFilter("W: initscripts conffile-without-noreplace-flag /etc/rc.d/rc.*.d/.*(killall|halt|single|local|reboot)")
addFilter("W: initscripts non-conffile-in-etc /etc/locale/.*")
addFilter('E: initscripts (no-chkconfig-line|incoherent-subsys)')

#hotplug
addFilter('E: hotplug non-standard-dir-perm /var/run/usb 0700')

#Setuid
addFilter('E: traceroute setuid-binary /usr/sbin/traceroute root 04755')
addFilter('E: urpmi setuid-binary /usr/bin/urpmi root 04750')
addFilter('E: sash statically-linked-binary /sbin/sash')
addFilter('E: perl-base setuid-binary /usr/bin/sperl5.6.0 root 04711')
addFilter('E: perl-base setuid-binary /usr/bin/suidperl root 04711')
addFilter('E: procmail setgid-binary /usr/bin/lockfile mail 02755')
addFilter('E: procmail setuid-gid-binary /usr/bin/procmail root mail 06755')
addFilter('E: rsh setuid-binary /usr/bin/rlogin root 04755')
addFilter('E: rsh setuid-binary /usr/bin/rsh root 04755')
addFilter('E: rsh setuid-binary /usr/bin/rcp root 04755')
addFilter('E: man setgid-binary /usr/bin/man man 02755')
addFilter('E: sudo non-standard-dir-perm /var/run/sudo 0700')
addFilter('E: sudo setuid-binary /usr/bin/sudo root 04111')
addFilter('E: slocate setgid-binary /usr/bin/slocate slocate 02755')
addFilter('E: SysVinit setgid-binary /usr/bin/wall tty 02555')
addFilter('E: sh-utils setuid-binary /bin/su root 04755')
addFilter('E: (netkit-base|iputils) setuid-binary /bin/ping root 04755')
addFilter('E: e2fsprogs statically-linked-binary /sbin/.*fsck.*')
addFilter('E: mount setuid-binary /bin/(u)?mount root 04755')
addFilter('E: util-linux setuid-binary /usr/bin/(newgrp|chsh|chfn) root 04711')
addFilter('E: util-linux setgid-binary /usr/bin/write tty 02755')
addFilter('E: X11R6-contrib setgid-binary /usr/X11R6/bin/xman man 02755')
addFilter('W: dev86-devel no-provides dev8-devel')

#bash
addFilter("E: bash info-files-without-install-info-post(u|i)n.*bash.info*")

#dev
addFilter("W: dev dangling-symlink.*")

#Pam
addFilter('W: pam devel-file-in-non-devel-package /lib/security/pam_unix_(session|passwd|acct|auth).so')
addFilter('E: shadow-utils non-standard-dir-perm /etc/default 0750')
addFilter('E: pam setuid-binary /sbin/(unix|pwdb)_chkpwd root 04(5|7)55')
addFilter('E: pam subdir-in-bin /sbin/pam_filter/upperLOWER')
addFilter('E: shadow-utils setuid-binary /usr/bin/(gpasswd|chage) root 04755')

#Kernel
addFilter('W: alsa(-source)? incoherent-version-in-changelog.*')
addFilter('W: kernel-headers dangling-symlink /usr/include/asm ../src/linux/include/asm')
addFilter('W: kernel-source dangling-symlink .*/linux/config.h ../pcmcia/config.h')
addFilter('W: reiserfs-utils dangling-symlink /sbin/fsck.reiserfs.*')
addFilter('W: reiserfs-utils incoherent-version-in-changelog')

#Glibc
addFilter('W: glibc shared-lib-without-dependency-information /lib/ld-.*so')
addFilter('W: glibc library-not-linked-against-libc /lib/libc-.*so')
addFilter('E: glibc statically-linked-binary /sbin/sln')
addFilter('E: glibc setuid-binary /usr/libexec/pt_chown root 04755')
addFilter('E: glibc invalid-soname /lib/libmemusage.so libmemusage.so')
addFilter('E: glibc invalid-soname /lib/libpcprofile.so libpcprofile.so')
addFilter('E: ldconfig statically-linked-binary /sbin/ldconfig')

#Transparent-xpm
addFilter('W: mathplot non-transparent-xpm ')

# InitScriptCheck exceptions
addFilter('E: squid incoherent-subsys /etc/rc.d/init.d/squid $SQUID')
addFilter('E: heartbeat incoherent-subsys /etc/rc.d/init.d/heartbeat $SUBSYS')


# non-conffile-in-etc
addFilter('W: mandrake-release non-conffile-in-etc /etc/mandrake-release')

# vixie-cron
addFilter('E: vixie-cron non-standard-dir-perm /var/spool/cron 0700')
addFilter('E: vixie-cron setuid-binary /usr/bin/crontab root 04755')

#openssh
addFilter('W: openssh-clients dangling-symlink /usr/bin/ssh-askpass')
addFilter('E: openssh-clients setuid-binary /usr/bin/ssh root 04711')

#XFree86
addFilter('E: XFree86 setuid-binary /usr/X11R6/bin/Xwrapper root 04711')

#emacs
addFilter('E: emacs setgid-binary /usr/lib/emacs/.*/movemail mail 02755')

#xemacs
addFilter('E: xemacs setgid-binary /usr/lib/xemacs-.*/movemail mail 02755')

#imwheel
addFilter('E: imwheel setuid-binary /usr/bin/imwheel-solo root 04755')

#ghostscript-fonts
# link points to a file in the ghostscript package which is in requires
addFilter('W: ghostscript-fonts dangling-symlink /usr/share/fonts/default/ghostscript/Fontmap ../../../ghostscript/5.50/Fontmap.GS')

#lpr
addFilter('E: lpr setgid-binary /usr/sbin/lpc-lpd lp 02755')
addFilter('E: lpr setuid-gid-binary /usr/bin/lpq-lpd root lp 06555')
addFilter('E: lpr setuid-gid-binary /usr/bin/lpr-lpd root lp 06555')
addFilter('E: lpr non-standard-dir-perm /var/spool/lpd 0775')
addFilter('E: lpr setuid-gid-binary /usr/bin/lprm-lpd root lp 06555')

#Mesa
# this is needed to not conflict with XFree86-libs
addFilter('E: Mesa no-ldconfig-symlink /usr/X11R6/lib/libGL.so.')
addFilter('E: Mesa no-ldconfig-symlink /usr/X11R6/lib/libGL.so.')
addFilter('E: Mesa no-ldconfig-symlink /usr/X11R6/lib/libGLwrapper.so.')

#False reports on locales
addFilter('E: libclanlib0-gl|clanlib-gl|xscreensaver-gl no-dependency-on locales-gl')
addFilter('E: emacs-el|xemacs-el no-dependency-on locales-el')
addFilter('E: (hack)?kernel-pcmcia-cs no-dependency-on locales-cs')
addFilter('E: php-gd no-dependency-on locales-gd')

#dev
addFilter('W: dev dangling-relative-symlink /dev/stdin ../proc/self/fd/0')
addFilter('W: dev dangling-relative-symlink /dev/fd ../proc/self/fd')
addFilter('W: dev dangling-relative-symlink /dev/stderr ../proc/self/fd/2')
addFilter('W: dev dangling-relative-symlink /dev/snd ../proc/asound/dev')
addFilter('W: dev dangling-relative-symlink /dev/core ../proc/kcore')
addFilter('W: dev dangling-relative-symlink /dev/stdout ../proc/self/fd/1')

#autoconf
addFilter('W: autoconf devel-file-in-non-devel-package /usr/share/autoconf/acconfig.h')

#library policy exceptions
addFilter('rpm|glibc|anonftp|pam|popt .*in-library-package')

# Config.py ends here
