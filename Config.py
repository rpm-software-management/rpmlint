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
from setuplist import *

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
                "SpecCheck",
                "NamingPolicyCheck",
                "ZipCheck",
                )

info=0
no_exception=0

# handle the list of checks to load
_checks=[]

def addCheck(check):
    global _checks
    
    if not check in _checks:
	_checks.append(check)

def allChecks():
    global _checks
    
    if _checks == []:
	defaultChecks()
    return _checks

def defaultChecks():
    resetChecks()
    _checks.extend(DEFAULT_CHECKS)
    
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
    except:
	return default

# List of filters
_filters=[]
_filters_re=None

def addFilter(s):
    global _filters
    global _filters_re

    _filters.append(s)
    _filters_re=None
    
def isFiltered(s):
    global _filters
    global _filters_re

    if _filters_re == None:
        # no filter
        if len(_filters) == 0:
            return 0
        _filters_re = '(?:' + _filters[0] + ')'
        
        for idx in range(1, len(_filters)):
            _filters_re = _filters_re + '|(?:' + _filters[idx] +')'
        _filters_re = re.compile(_filters_re)
        
    if not no_exception:
        if _filters_re.search(s):
            return 1
    return 0
    
# Standard exceptions:
addFilter('rootfiles non-etc-or-var-file-marked-as-conffile /root/.*')
addFilter('(rootfiles|etcskel) non-standard-dir-perm /(root|etc/skel)/tmp')
addFilter('rootfiles non-standard-dir-perm (/root|/etc/skel)/tmp')
addFilter('man(-[^ ]+)? non-standard-dir-perm /var/(X11R6/)?catman[^ ]+ 0775')
addFilter('man(-[^ ]+)? non-standard-dir-perm /usr/(X11R6/)?man/[^ ]+ 02755')
addFilter('W: filesystem dangling-relative-symlink /usr/lib/X11 ../X11R6/lib/X11')
addFilter('E: filesystem non-standard-dir-perm /usr/share/empty 0555')
addFilter('filesystem non-standard-dir-perm /var/lock/subsys 0775')
addFilter('filesystem non-standard-dir-perm /tmp 01777')
addFilter('filesystem non-standard-dir-perm /var/tmp 01777')
addFilter('filesystem (non-standard-dir-perm|dir-or-file-in-mnt) /mnt/(floppy|disk|cdrom)')
addFilter('filesystem non-standard-dir-perm /var/spool/mail 0775')
addFilter('filesystem non-standard-dir-perm /root 0750')
addFilter('filesystem non-standard-dir-perm /var/lock 0775')
addFilter('filesystem non-standard-dir-perm /proc 0555')
addFilter('filesystem dir-or-file-in-usr-local .*')

addFilter('postgresql-test non-standard-[gu]id [^ ]+ postgres')
addFilter('(binutils|dev86|compat-glibc|alsa|alsa-sourcecompat-libs|gcc|gcc-c\+\+|egcs|egcs-c\+\+|gcc-chill|gcc-f77|egcs-g77|gcc-libgcj|gcc-objc|hackkernel-source|hackkernel-headers|kernel-source.*|kernel-headers|octave|ghc|mercury|ocaml|ocaml-lablgtk|camlp4|gprolog|ruby-extensions|ruby|XFree86-static-libs|libwmf|doxygen|swi-prolog|ghc-prof|perl-(GTK.*|PDL|DBI)) devel-file-in-non-devel-package')
addFilter('menu devel-file-in-non-devel-package /etc/menu-methods/menu.h')
addFilter('[^ ]+ devel-file-in-non-devel-package /usr/doc/.*\.h$')
addFilter('glibc-profile devel-file-in-non-devel-package .*\.a$')
addFilter('menu non-file-in-menu-dir /usr/lib/menu/default')
addFilter('I: menu unable-to-parse-menu-command')
addFilter('menu invalid-menu-section')
addFilter('XFree86-server devel-file-in-non-devel-package /usr/X11R6/lib/modules')
addFilter('icewm-light menu-command-not-in-package icewm')
addFilter('slocate non-standard-dir-perm /var/lib/slocate 0750')
addFilter('ld.so statically-linked-binary /sbin/ldconfig')
addFilter('ocaml statically-linked-binary /sbin/ldconfig')
addFilter('busybox statically-linked-binary /usr/bin/busybox')
addFilter('rpm statically-linked-binary (?:/usr/bin/rpm2cpio|/bin/rpm)')
addFilter('info-install info-dir-file /usr/share/info/dir')
addFilter('sympa non-standard-uid [^\s]+ sympa')
addFilter('sympa non-standard-gid [^\s]+ sympa')
addFilter('rpm dangerous-command-in-%post rpm')
addFilter('menu standard-dir-owned-by-package /usr/lib/menu')

#XFree86
addFilter('XFree86-server unstripped-binary-or-object /usr/X11R6/lib/modules/')
addFilter('XFree86-server statically-linked-binary /usr/X11R6/lib/modules/')
addFilter('XFree86.* postin-without-ghost-file-creation /usr/X11R6/lib/X11/fonts/')
addFilter('XFree86 dangling-relative-symlink /usr/X11R6/lib/X11/xinit ../../../../etc/X11/xinit')
addFilter('XFree86 non-standard-dir-perm /var/lib/xdm 0700')
addFilter('XFree86 dangling-relative-symlink /usr/X11R6/lib/X11/xserver ../../../.././etc/X11/xserver')
addFilter('XFree86 standard-dir-owned-by-package /usr/X11R6/man.*')
addFilter('XFree86 standard-dir-owned-by-package /usr/share/icons')
addFilter('XFree86 standard-dir-owned-by-package /etc/X11')

#db
addFilter('db[1-3]-devel no-provides db-devel')
addFilter('db[12] incoherent-version-in-name')

#emacs
addFilter('emacs-X11 menu-command-not-in-package emacs')

#freetype
addFilter('freetype-devel no-major-in-name freetype-devel')
addFilter('freetype non-versioned-file-in-library-package')
addFilter('freetype incoherent-version-in-name 2')

#freetype2
addFilter('freetype2 incoherent-version-in-name 6')

#openh323
addFilter('openh323_1-devel no-provides openh323_-devel')

#openssh
addFilter('openssh-clients dangling-relative-symlink /usr/bin/ssh-askpass ../..//usr/lib/ssh/ssh-askpass')

#menus
addFilter('bcast version-in-menu-title Broadcast 2000')
addFilter('xawtv version-in-menu-longtitle The X11 Video4Linux Stream Capture Viewer')

#ocaml
addFilter('ocaml unstripped-binary-or-object /usr/bin/(ocamldebug|ocamlbrowser)')

#nfs
addFilter('nfs-utils-clients non-standard-dir-perm /var/lib/nfs/statd 0700')

#initscripts
addFilter('initscripts non-etc-or-var-file-marked-as-conffile /sbin/if(up|down)')
addFilter('initscripts (setuid|setgid)-binary (/usr/sbin/usernetctl|/sbin/netreport) root.*')
addFilter('initscripts non-standard-dir-perm /var/run/netreport 0775')
addFilter('initscripts no-(status|reload)-entry.*mandrake_(consmap|firstime|everytime).*')
addFilter('initscripts subsys-not-used.*mandrake_(consmap|firstime|everytime).*')
addFilter('initscripts subsys-not-used.*/etc/rc.d/init.d/(halt|rawdevices)')
addFilter('initscripts no-status-entry.*/etc/rc.d/init.d/(killall|halt|single).*')
addFilter('initscripts no-(status|reload)-entry.*/etc/rc.d/init.d/(killall|halt|functions|single).*')
addFilter('initscripts conffile-without-noreplace-flag /etc/rc.d/rc.*.d/.*(killall|halt|single|local|reboot)')
addFilter('initscripts non-conffile-in-etc /etc/locale/.*')
addFilter('initscripts (no-chkconfig-line|incoherent-subsys)')
addFilter('initscripts obsolete-not-provided (rhsound|sapinit)')

#wine
addFilter('libwine.*non-versioned-file-in-library-package /usr/lib/wine.*')
addFilter('wine-utils.*dangling-relative-symlink.*wine')
addFilter('wine non-standard-dir-perm.*/var/lib/wine.*')
addFilter('zero-length.*/var/lib/wine/.*')

#hotplug
addFilter('hotplug non-standard-dir-perm /var/run/usb 0700')

#udev
addFilter('udev statically-linked-binary /sbin/udev')

#policycoreutils
addFilter('policycoreutils statically-linked-binary /usr/sbin/load_policy')

#Setuid
addFilter('traceroute setuid-binary /usr/sbin/traceroute root 04755')
addFilter('iputils setuid-binary /usr/sbin/(traceroute|ping)6 root 04755')
#addFilter('urpmi setuid-binary /usr/bin/urpmi root 04750')
addFilter('sash statically-linked-binary /sbin/sash')
addFilter('perl-base setuid-binary /usr/bin/sperl5\.\d+\.\d+ root 04711')
addFilter('perl-base setuid-binary /usr/bin/suidperl root 04711')
addFilter('procmail setgid-binary /usr/bin/lockfile mail 02755')
addFilter('procmail setuid-gid-binary /usr/bin/procmail root mail 06755')
addFilter('rsh setuid-binary /usr/bin/rlogin root 04755')
addFilter('rsh setuid-binary /usr/bin/rsh root 04755')
addFilter('rsh setuid-binary /usr/bin/rcp root 04755')
addFilter('man setgid-binary /usr/bin/man man 02755')
addFilter('sudo non-standard-dir-perm /var/run/sudo 0700')
addFilter('sudo setuid-binary /usr/bin/sudo root 04111')
addFilter('slocate setgid-binary /usr/bin/slocate slocate 02755')
addFilter('SysVinit setgid-binary /usr/bin/wall tty 02555')
addFilter('sh-utils setuid-binary /bin/su root 04755')
addFilter('(netkit-base|iputils) setuid-binary /bin/ping root 04755')
addFilter('e2fsprogs statically-linked-binary /sbin/.*fsck.*')
addFilter('mount setuid-binary /bin/(u)?mount root 04755')
addFilter('util-linux setuid-binary /usr/bin/(newgrp|chsh|chfn) root 04711')
addFilter('util-linux setgid-binary /usr/bin/write tty 02755')
#addFilter('X11R6-contrib setgid-binary /usr/X11R6/bin/xman man 02755')
addFilter('dev86-devel no-provides dev8-devel')
addFilter('usermode setuid-binary /usr/sbin/userhelper root 04755')
addFilter('avifile-samples setuid-binary /usr/bin/kv4lsetup root')
addFilter('mailman setgid-binary /usr/lib/mailman/(mail/mailman|cgi-bin/(rmlist|roster|listinfo|admindb|private|create|admin|confirm|subscribe|options|edithtml)) mail 02755')
addFilter('sympa setuid-binary /usr/lib/sympa/bin/aliaswrapper root 04750')
addFilter('sympa setuid-binary /usr/lib/sympa/bin/bouncequeue sympa 04755')
addFilter('sympa setuid-binary /usr/lib/sympa/bin/virtualwrapper root 04750')
addFilter('sympa setuid-gid-binary /var/www/cgi-bin/wwsympa.fcgi root root 06755')
addFilter('sympa setuid-binary /usr/lib/sympa/bin/queue sympa 04755')

#iputilis setuid it safe as they drop it VERY early.
addFilter('iputils setuid-binary /usr/sbin/(traceroute|ping)6 root 04755')

#bash
addFilter('bash info-files-without-install-info-post(u|i)n.*bash.info*')

#dev
addFilter('dev dangling-symlink.*')

#Pam
addFilter('pam devel-file-in-non-devel-package /lib/security/pam_unix_(session|passwd|acct|auth).so')
addFilter('shadow-utils non-standard-dir-perm /etc/default 0750')
addFilter('pam setuid-binary /sbin/(unix|pwdb)_chkpwd root 04(5|7)55')
addFilter('pam subdir-in-bin /sbin/pam_filter/upperLOWER')
addFilter('shadow-utils setuid-binary /usr/bin/(gpasswd|chage) root 04755')

#modutils
addFilter('module-init-tools hardcoded-library-path in .*/lib/modutils/macros')

#Kernel
addFilter('alsa(-source)? incoherent-version-in-changelog.*')
addFilter('kernel-headers dangling-symlink /usr/include/asm ../src/linux/include/asm')
addFilter('kernel-source dangling-symlink .*/linux/config.h ../pcmcia/config.h')
addFilter('reiserfs-utils dangling-symlink /sbin/fsck.reiserfs.*')
addFilter('reiserfsprogs dangling-relative-symlink /sbin/fsck.reiserfs ../bin/true')
addFilter('reiserfs-utils incoherent-version-in-changelog')
addFilter('kernel use-of-RPM_SOURCE_DIR')
addFilter('kernel-source zero-length .*\.stamp$')
addFilter('kernel-source hidden-file-or-dir .*\.depend$')

#Glibc
addFilter('glibc shared-lib-without-dependency-information /lib/ld-.*so')
addFilter('glibc library-not-linked-against-libc /lib/libc-.*so')
addFilter('glibc statically-linked-binary /sbin/sln')
addFilter('glibc setuid-binary /usr/libexec/pt_chown root 04755')
addFilter('glibc invalid-soname /lib/libmemusage.so libmemusage.so')
addFilter('glibc invalid-soname /lib/libpcprofile.so libpcprofile.so')
addFilter('ldconfig statically-linked-binary /sbin/ldconfig')

#Transparent-xpm
addFilter('mathplot non-transparent-xpm ')

# InitScriptCheck exceptions
addFilter('squid incoherent-subsys /etc/rc.d/init.d/squid $SQUID')
addFilter('heartbeat incoherent-subsys /etc/rc.d/init.d/heartbeat $SUBSYS')

# non-conffile-in-etc
addFilter('mandrake-release non-conffile-in-etc /etc/mandrake-release')

# vixie-cron
addFilter('vixie-cron non-standard-dir-perm /var/spool/cron 0700')
addFilter('vixie-cron setuid-binary /usr/bin/crontab root 04755')

#openssh
addFilter('openssh-clients dangling-symlink /usr/bin/ssh-askpass')
addFilter('openssh-clients setuid-binary /usr/bin/ssh root 04711')

#XFree86
addFilter('XFree86 setuid-binary /usr/X11R6/bin/Xwrapper root 04711')
addFilter('XFree86 incoherent-logrotate-file /etc/logrotate.d/xdm')
addFilter('XFree86-devel no-dependency-on XFree86')
addFilter('XFree86-devel no-provides XFree-devel')

#emacs
addFilter('emacs setgid-binary /usr/lib/emacs/.*/movemail mail 02755')

#xemacs
addFilter('xemacs setgid-binary /usr/lib/xemacs-.*/movemail mail 02755')

#imwheel
addFilter('imwheel setuid-binary /usr/bin/imwheel-solo root 04755')

#ghostscript-fonts
# link points to a file in the ghostscript package which is in requires
addFilter('ghostscript-fonts dangling-symlink /usr/share/fonts/default/ghostscript/Fontmap ../../../ghostscript/5.50/Fontmap.GS')

#lpr
addFilter('lpr setgid-binary /usr/sbin/lpc-lpd lp 02755')
addFilter('lpr setuid-gid-binary /usr/bin/lpq-lpd root lp 06555')
addFilter('lpr setuid-gid-binary /usr/bin/lpr-lpd root lp 06555')
addFilter('lpr non-standard-dir-perm /var/spool/lpd 0775')
addFilter('lpr setuid-gid-binary /usr/bin/lprm-lpd root lp 06555')

#Mesa
# this is needed to not conflict with XFree86-libs
addFilter('.* no-ldconfig-symlink /usr/X11R6/lib/libGL.so.')
addFilter('.* no-ldconfig-symlink /usr/X11R6/lib/libGL.so.')
addFilter('.* no-ldconfig-symlink /usr/X11R6/lib/libGLwrapper.so.')

#False reports on locales
addFilter('(?:libclanlib0-gl|clanlib-gl|xscreensaver-gl|prboom-gl) no-dependency-on locales-gl')
addFilter('(?:emacs.*-el|xemacs.*-el) no-dependency-on locales-el')
addFilter('(hack)?(kernel-)?pcmcia-cs no-dependency-on locales-cs')
addFilter('php-gd no-dependency-on locales-gd')

#dev
addFilter('dev dangling-relative-symlink /dev/stdin ../proc/self/fd/0')
addFilter('dev dangling-relative-symlink /dev/fd ../proc/self/fd')
addFilter('dev dangling-relative-symlink /dev/stderr ../proc/self/fd/2')
addFilter('dev dangling-relative-symlink /dev/snd ../proc/asound/dev')
addFilter('dev dangling-relative-symlink /dev/core ../proc/kcore')
addFilter('dev dangling-relative-symlink /dev/stdout ../proc/self/fd/1')

#autoconf
addFilter('autoconf devel-file-in-non-devel-package /usr/share/autoconf/acconfig.h')

#portsentry
addFilter('portsentry non-readable /etc/portsentry/portsentry.ignore 0600')
addFilter('portsentry non-readable /etc/portsentry/portsentry.conf 0600')
addFilter('portsentry non-standard-dir-perm /var/portsentry 0700')

# shadow-utils
addFilter('shadow-utils dangling-relative-symlink /usr/bin/sg newgrp')
addFilter('shadow-utils non-readable /etc/default/useradd 0600')

#ipsec
addFilter('freeswan non-readable /etc/freeswan/ipsec.secrets 0600')

#library policy exceptions
addFilter('(?:rpm|glibc|anonftp|pam|popt|egcs-c\+\+) .*in-library-package')

#mkinitrd
addFilter('mkinitrd statically-linked-binary /sbin/insmod-DIET')
addFilter('mkinitrd statically-linked-binary /sbin/nash')

#automake
addFilter('automake devel-file-in-non-devel-package /usr/share/automake/ansi2knr.c')

#gettext
addFilter('gettext-devel no-major-in-name gettext-devel')

#chromium
addFilter('chromium-setup .*-icon-not-in-package chromium.xpm')

#setup
addFilter('setup zero-length (/etc/motd|/var/log/lastlog|/etc/exports)')

#webmin
addFilter('webmin dangerous-command-in-%postun rm')

#methane
addFilter('methane dangerous-command-in-%post chown')

#icon from menu can be used in other packages
addFilter('icon-not-in-package .*_section.png')

#apache
addFilter('apache-suexec setuid-binary /usr/sbin/suexec root 04710')

#hylafax
addFilter('hylafax-server non-readable /var/spool/fax/etc/hosts.hfaxd 0600')
addFilter('hylafax-server non-standard-dir-perm /var/spool/fax/(sendq|tmp|doneq|docq|pollq|archive) 0700')
addFilter('hylafax-server incoherent-logrotate-file /etc/logrotate.d/hylafax')

#ctcs
addFilter('ctcs statically-linked-binary /root/ctcs/runin/bin/')

#nss_db
addFilter('nss_db non-versioned-file-in-library-package')
addFilter('nss_db executable-in-library-package')

#pwiki
addFilter('pwiki non-standard-dir-perm /var/www/pwiki/.* 0750')

#fetchmail
addFilter('fetchmail-daemon non-readable /etc/fetchmailrc 0600')

#iptable
addFilter('iptables shared-lib-without-dependency-information /lib/iptables/')

#Starting from Mandrakelinux 8.1 we let standard menu files in the packages
addFilter('old-menu-entry')

#zapping
addFilter('zapping devel-file-in-non-devel-package /usr/lib/zapping/plugins/.*\.a$')

#sane
addFilter('libsane1 non-versioned-file-in-library-package /usr/lib/sane')

#mgetty
addFilter('mgetty-sendfax non-standard-dir-perm /var/spool/fax/outgoing 01777')        
addFilter('mgetty-sendfax non-standard-dir-perm /var/spool/fax/outgoing/locks 0777')
addFilter('mgetty-sendfax incoherent-logrotate-file /etc/logrotate.d/sendfax')

#kdebase
addFilter('kdebase standard-dir-owned-by-package /usr/share/icons')

#basesystem
addFilter('basesystem no-%clean-section')

#fetchmail
addFilter('fetchmail-daemon incoherent-init-script-name fetchmail')

#python
addFilter('python(-base)? no-depend[ae]ncy(-on)? python')

#perl
addFilter('perl(-base)? no-depend[ae]ncy(-on)? perl')

#nut
addFilter('nut-server non-readable /etc/ups/upsd.(users|conf) 0600')
addFilter('nut non-readable /etc/ups/upsmon.conf 0600')

#shorewall
addFilter('shorewall non-readable /etc/shorewall/.* 0600')
addFilter('shorewall non-standard-dir-perm /etc/shorewall 0700')

#DansGuardian
addFilter('DansGuardian non-readable /etc/dansguardian/.* 0600')

#rpm
addFilter('rpm postin-without-ghost-file-creation')
addFilter('rpm standard-dir-owned-by-package /var/lib/rpm')

# packages without binary but built with other binary packages
addFilter('(Mesa|hylafax|openldap|xclass|gtk\+mdk) no-binary')

#extipl
addFilter('extipl only-non-binary-in-usr-lib')

#ocamltk
addFilter('ocamltk devel-file-in-non-devel-package')

#drakconf
addFilter('drakconf invalid-menu-section Configuration /usr/lib/menu/drakconf')

#wvdial
addFilter('wvdial non-readable /etc/ppp/peers/wvdial(-pipe)? 0600')

#tpctl
addFilter('tpctl incoherent-init-script-name apmiser')

#gconf schemas
addFilter('non-conffile-in-etc /etc/gconf/schemas/')

# hidden-file-or-dir
# apache .htaccess
addFilter('.* hidden-file-or-dir /var/www/.*/.htaccess')

# Rox .DirIcon
addFilter('rox(-.*)? hidden-file-or-dir /usr/lib/apps/.*/.DirIcon' )

# some kde packages use a .hidden directory.
addFilter('(kdebase|kdemultimedia|kdenetwork|kdepim|lisa) hidden-file-or-dir /usr/share/.*/.hidden' )

# Kde .directory, also used by nautilus and OpenOffice.
addFilter('.* hidden-file-or-dir .*/.directory' )

# gnumeric templates
addFilter('gnumeric hidden-file-or-dir /usr/share/gnumeric/.*/autoformat-templates/.category')

# if it is at root, it should be important
addFilter('am-utils hidden-file-or-dir /.automount')

# kernel hidden file.
addFilter('(hack)?kernel.*source hidden-file-or-dir /usr/share/linux.*/(\.config|\.need_mrproper|\.version|\.depend)')

# /etc/skel standard file
addFilter('bash hidden-file-or-dir /etc/skel/.bash(rc|_profile|_logout)')
addFilter('etcskel hidden-file-or-dir /etc/skel/.mailcap')

# koffice 
addFilter('koffice hidden-file-or-dir /usr/share/apps/.*(.autoforms|.icon|.source)')

# root preferences
addFilter('rootfiles hidden-file-or-dir /root/.*')

# scilab
addFilter('scilab hidden-file-or-dir /usr/lib/scilab-.*/.pvmd.conf')

# pvm
addFilter('pvm hidden-file-or-dir /usr/share/pvm3/.bash(_profile|rc)')

addFilter('apache2-devel apache2-naming-policy-not-applied')
addFilter('apache2-modules apache2-naming-policy-not-applied')

addFilter('apache2-mod_ruby ruby-naming-policy-not-applied')
addFilter('ruby ruby-naming-policy-not-applied')
addFilter('python python-naming-policy-not-applied')
addFilter('xmms xmms-naming-policy-not-applied')

# rpm 4.2's debuginfo packages
addFilter('-debug(info)? no-documentation')
addFilter('-debug(info)? devel-file-in-non-devel-package')
addFilter('-debug(info)? unstripped-binary-or-object')

# ppp
addFilter('ppp non-readable /etc/ppp/chap-secrets 0600')
addFilter('ppp setuid-binary /usr/sbin/pppd root 05755')
addFilter('ppp non-readable /etc/ppp/pap-secrets 0600')

# postfix
addFilter('postfix(-[^ ]+)? non-standard-dir-perm /var/spool/postfix/(corrupt|trace|defer|deferred|flush|private|incoming|hold|bounce|active) 0700')
addFilter('postfix(-[^ ]+)? non-standard-dir-perm /var/spool/postfix/maildrop 0730')
addFilter('postfix(-[^ ]+)? non-standard-dir-perm /var/spool/postfix/public 0710')
addFilter('postfix(-[^ ]+)? non-standard-executable-perm /usr/sbin/post(drop|queue) 02755')
addFilter('postfix(-[^ ]+)? non-standard-gid /usr/sbin/post(drop|queue) postdrop')
addFilter('postfix(-[^ ]+)? non-standard-gid /var/spool/postfix/(public|maildrop) postdrop')
addFilter('postfix(-[^ ]+)? non-standard-uid /var/spool/postfix/([^ ]+) postfix')
addFilter('postfix(-[^ ]+)? setgid-binary /usr/sbin/post(drop|queue) postdrop 02755')

# xinetd
addFilter('xinetd standard-dir-owned-by-package /etc/xinetd.d')

# lsb
addFilter('lsb standard-dir-owned-by-package /etc/opt')

# devel-dependency wrong warnings
addFilter('gcc devel-dependency glibc-devel')
addFilter('gcc-c\+\+ devel-dependency libstdc\+\+5-devel')
addFilter('gcc-java devel-dependency libgcj4-devel')
addFilter('gcc2.96 devel-dependency glibc-devel')
addFilter('gcc2.96-c\+\+ devel-dependency glibc-devel')
addFilter('gcj-tools devel-dependency libgcj4-devel')
addFilter('glade devel-dependency gnome-libs-devel')
addFilter('glademm devel-dependency libgtkmm-devel')
addFilter('kdevelop devel-dependency libpng3-devel')
addFilter('kernel-source devel-dependency glibc-devel')
addFilter('libsigc\+\+-examples devel-dependency libsigc\+\+-devel')
addFilter('libsigc\+\+1\.0-examples devel-dependency libsigc\+\+1\.0-devel')

# devel-file-in-non-devel-package
addFilter('dyalog devel-file-in-non-devel-package /usr/lib/DyALog')
addFilter('perl devel-file-in-non-devel-package /usr/lib/perl.*\.h')

# invalid-build-requires
addFilter('invalid-build-requires libgnomeui2-devel|libGConf2-devel|libglade2.0-devel|libgnomecanvas2-devel|libgtkhtml2-devel|libORBit2-devel|libglib2.0-devel|libgtk\+2-devel|libgtk\+2.0-devel|libxml2-devel|libIDL2-devel|libglib2-devel|libgal2.0-devel|libgtkhtml-3.0-devel|libgtop2.0-devel|libpanel-applet-2-devel|libatk1.0-devel|libgnome-vfs2-devel|libglib2.0-devel|libgnome2-devel|libXft2-devel|libgnet2-devel|libgdk_pixbuf2.0-devel|libdxr3-devel|libbzip2-devel|libhdf5-devel|libieee1284-devel')

# explicit-lib-dependency
addFilter('explicit-lib-dependency libxslt-proc|libimlib2_1-loaders')

# don't report errors on debug packages
addFilter('^.+-debug(info)? [^ ]+ /usr/lib/debug/')

################################################################################
# policy decisions. The idea is to be able to run rpmlint as an old version.
################################################################################

DEFAULT_LAUNCHERS_OLD = (['(?:/usr/bin/)?kdesu', ('/usr/bin/kdesu', 'kdesu')],
                         ['(?:/usr/bin/)?launch_x11_clanapp', ('/usr/bin/launch_x11_clanapp', 'clanlib', 'libclanlib0')],
                         ['(?:/usr/bin/)?soundwrapper', None],
                         ['NO_XALF', None],
                         )
DEFAULT_LAUNCHERS_90 = (['(?:/usr/bin/)?kdesu', ('/usr/bin/kdesu', 'kdesu')],
                        ['(?:/usr/bin/)?launch_x11_clanapp', ('/usr/bin/launch_x11_clanapp', 'clanlib', 'libclanlib0')],
                        ['(?:/usr/bin/)?soundwrapper', None],
                        )

DEFAULT_LAUNCHERS = DEFAULT_LAUNCHERS_90

STANDARD_GROUPS = STANDARD_GROUPS_NEW
STANDARD_USERS = STANDARD_USERS_NEW

def load_policy(policy):
    if policy != 'mdk9.2':
        addFilter('no-epoch-tag|unreasonable-epoch|no-epoch-in-obsoletes|no-epoch-in-conflicts|no-epoch-in-provides|no-epoch-in-dependency|devel-dependency|invalid-build-requires')
        if policy != 'mdk9.1':
            addFilter('lib-package-without-%mklibname|outside-libdir-files')
            if policy != 'mdk9.0':
                addFilter('no-prereq-on|non-root-user-log-file|non-root-group-log-file|non-ghost-file|hardcoded-library-path|configure-without-libdir-spec|no-binary|only-non-binary-in-usr-lib')
                DEFAULT_LAUNCHERS = DEFAULT_LAUNCHERS_OLD
                STANDARD_GROUPS = STANDARD_GROUPS_OLD
                STANDARD_USERS = STANDARD_USERS_OLD
        
# Config.py ends here
