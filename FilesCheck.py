#############################################################################
# File          : FilesCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Mon Oct  4 19:32:49 1999
# Version       : $Id$
# Purpose       : test various aspects on files: locations, owner, groups,
#                 permission, setuid, setgid...
#############################################################################

from Filter import *
import AbstractCheck
from Pkg import is_utf8, is_utf8_str
import rpm
import re
import stat
import string
import os
try:
    from textwrap import fill # python >= 2.3
except ImportError:
    def fill(text, width=70): return text

# must be kept in sync with the filesystem package
STANDARD_DIRS = (
    '/',
    '/bin',
    '/boot',
    '/etc',
    '/etc/X11',
    '/etc/opt',
    '/etc/profile.d',
    '/etc/skel',
    '/etc/xinetd.d',
    '/home',
    '/lib',
    '/lib/modules',
    '/lib64',
    '/media',
    '/mnt',
    '/mnt/cdrom',
    '/mnt/disk',
    '/mnt/floppy',
    '/opt',
    '/proc',
    '/root',
    '/sbin',
    '/selinux',
    '/srv',
    '/sys',
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
    '/usr/lib/X11',
    '/usr/lib/games',
    '/usr/lib/gcc-lib',
    '/usr/lib/menu',
    '/usr/lib64',
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
    '/usr/local/share',
    '/usr/local/share/man',
    '/usr/local/share/man/man1',
    '/usr/local/share/man/man2',
    '/usr/local/share/man/man3',
    '/usr/local/share/man/man4',
    '/usr/local/share/man/man5',
    '/usr/local/share/man/man6',
    '/usr/local/share/man/man7',
    '/usr/local/share/man/man8',
    '/usr/local/share/man/man9',
    '/usr/local/share/man/mann',
    '/usr/local/src',
    '/usr/sbin',
    '/usr/share',
    '/usr/share/dict',
    '/usr/share/doc',
    '/usr/share/icons',
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
    )

DEFAULT_GAMES_GROUPS='Games'

DEFAULT_DANGLING_EXCEPTIONS = (['consolehelper$', 'usermode-consoleonly'],
                               )

# Standard users and groups from LSB 3.1: 21.2 User & Group Names
DEFAULT_STANDARD_USERS  = ('root', 'bin', 'daemon', 'adm', 'lp', 'sync',
                           'shutdown', 'halt', 'mail', 'news', 'uucp',
                           'operator', 'man', 'nobody',)
DEFAULT_STANDARD_GROUPS = ('root', 'bin', 'daemon', 'adm', 'lp', 'sync',
                           'shutdown', 'halt', 'mail', 'news', 'uucp',
                           'man', 'nobody',)

tmp_regex=re.compile('^/tmp/|^(/var|/usr)/tmp/')
sub_bin_regex=re.compile('^(/usr)?/s?bin/\S+/')
backup_regex=re.compile('~$|\#[^/]+\#$')
compr_regex=re.compile('\.(gz|z|Z|zip|bz2)$')
absolute_regex=re.compile('^/([^/]+)')
absolute2_regex=re.compile('^/?([^/]+)')
points_regex=re.compile('^\.\./(.*)')
doc_regex=re.compile('^/usr(/share|/X11R6)?/(doc|man|info)/')
bin_regex=re.compile('^(/usr)?/s?bin/')
includefile_regex = re.compile('\.(c|h)(pp|xx)?$', re.IGNORECASE)
develfile_regex = re.compile('\.(a|cmxa?|mli?)$')
buildconfigfile_regex=re.compile('(\.pc|/bin/.+-config)$')
sofile_regex=re.compile('/lib(64)?/[^/]+\.so$')
devel_regex=re.compile('(.*)-(debug(info)?|devel|source|static)$')
debuginfo_package_regex=re.compile('-debug(info)?$')
lib_regex=re.compile('lib(64)?/lib[^/]*\.so\..*')
ldconfig_regex=re.compile('^[^#]*ldconfig', re.MULTILINE)
depmod_regex=re.compile('^[^#]*depmod', re.MULTILINE)
install_info_regex=re.compile('^[^#]*install-info', re.MULTILINE)
perl_temp_file=re.compile('.*perl.*/(\.packlist|perllocal\.pod)$')
scm_regex=re.compile('/CVS/[^/]+$|/\.(cvs|git|hg)ignore$|/\.hgtags$|/\.(git|hg|svn)/|/(\.arch-ids|{arch})/')
htaccess_regex=re.compile('\.htaccess$')
games_path_regex=re.compile('^/usr(/lib(64)?)?/games/')
games_group_regex=re.compile(Config.getOption('RpmGamesGroups', DEFAULT_GAMES_GROUPS))
source_regex=re.compile('\.(c|cc|cpp|ui)$')
dangling_exceptions=Config.getOption('DanglingSymlinkExceptions', DEFAULT_DANGLING_EXCEPTIONS)
logrotate_regex=re.compile('^/etc/logrotate\.d/(.*)')
module_rpms_ok=Config.getOption('KernelModuleRPMsOK', 1)
kernel_modules_regex=re.compile('^/lib/modules/(2\.[23456]\.[0-9]+[^/]*?)/')
kernel_package_regex=re.compile('^kernel(22)?(-)?(smp|enterprise|bigmem|secure|BOOT|i686-up-4GB|p3-smp-64GB)?')
normal_zero_length_regex=re.compile('^/etc/security/console\.apps/|/\.nosearch$|/__init__\.py$')
perl_regex=re.compile('^/usr/lib/perl5/(?:vendor_perl/)?([0-9]+\.[0-9]+)\.([0-9]+)/')
python_regex=re.compile('^/usr/lib/python([.0-9]+)/')
perl_version_trick=Config.getOption('PerlVersionTrick', 1)
log_regex=re.compile('^/var/log/[^/]+$')
lib_path_regex=re.compile('^(/usr(/X11R6)?)?/lib(64)?')
lib_package_regex=re.compile('^(lib|.+-libs)')
hidden_file_regex=re.compile('/\.[^/]*$')
mispelled_macro_regex=re.compile('%{.*}')
siteperl_perl_regex=re.compile('/site_perl/')
manifest_perl_regex=re.compile('^/usr/share/doc/perl-.*/MANIFEST(\.SKIP)?$');
shebang_regex=re.compile('^#!\s*(\S*)')
interpreter_regex=re.compile('^/(usr/)?s?bin/[^/]+$')
script_regex=re.compile('^/((usr/)?s?bin|etc/(rc\.d/init\.d|X11/xinit\.d|cron\.(hourly|daily|monthly|weekly)))/')
sourced_script_regex=re.compile('^/etc/(bash_completion\.d|profile\.d)/')
use_utf8=Config.getOption('UseUTF8', Config.USEUTF8_DEFAULT)
meta_package_re=re.compile(Config.getOption('MetaPackageRegexp', '^(bundle|task)-'))
filesys_packages = ['filesystem'] # TODO: make configurable?

for idx in range(0, len(dangling_exceptions)):
    dangling_exceptions[idx][0]=re.compile(dangling_exceptions[idx][0])
del idx

use_relative_symlinks = Config.getOption("UseRelativeSymlinks", 1)

standard_groups = Config.getOption('StandardGroups', DEFAULT_STANDARD_GROUPS)
standard_users = Config.getOption('StandardUsers', DEFAULT_STANDARD_USERS)

# loosely inspired from Python Cookbook
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/173220
text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
_null_trans = string.maketrans("", "")

def istextfile(filename, pkg):
    fobj = None
    try:
        fobj = open(filename, 'r')
        s = fobj.read(512)
        fobj.close()
    except Exception, e: # eg. https://bugzilla.redhat.com/209876
        printWarning(pkg, 'read-error', e)
        if fobj:
            fobj.close()
        return 0

    if "\0" in s:
        return 0

    if not s:  # Empty files are considered text
        return 1

    # PDF's are binary but often detected as text by the algorithm below
    if filename.lower().endswith('.pdf') and s.startswith('%PDF-'):
        return 0

    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    t = s.translate(_null_trans, text_characters)

    # If more than 30% non-text characters, then
    # this is considered a binary file
    if float(len(t))/len(s) > 0.30:
        return 0
    return 1

class FilesCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'FilesCheck')

    def check(self, pkg):

        files = pkg.files()

        if use_utf8:
            for filename in files:
                if not is_utf8_str(filename):
                    printError(pkg, 'filename-not-utf8', filename)

        # Rest of the checks are for binary packages only
        if pkg.isSource():
            return

        # Check if the package is a development package
        devel_pkg=devel_regex.search(pkg.name)

        config_files=pkg.configFiles()
        ghost_files=pkg.ghostFiles()
        doc_files=pkg.docFiles()
        req_names=pkg.req_names()
        lib_package=lib_package_regex.search(pkg.name)
        is_kernel_package=kernel_package_regex.search(pkg.name)

        # report these errors only once
        perl_dep_error=0
        python_dep_error=0
        lib_file=0
        non_lib_file=0
        log_file=0
        logrotate_file=0

        if not doc_files:
            printWarning(pkg, 'no-documentation')

        if len(files.keys()) and meta_package_re.search(pkg.name):
            printWarning(pkg, 'file-in-meta-package')

        if debuginfo_package_regex.search(pkg.name) and not files:
            printError(pkg, 'empty-debuginfo-package')

        for f in files.keys():
            enreg=files[f]
            mode=enreg[0]
            user=enreg[1]
            group=enreg[2]
            size=enreg[4]
            is_doc = f in doc_files
            nonexec_file = 0

            if mispelled_macro_regex.search(f):
                printWarning(pkg, 'mispelled-macro', f)
            if standard_users and not user in standard_users:
                printError(pkg, 'non-standard-uid', f, user)
            if standard_groups and not group in standard_groups:
                printError(pkg, 'non-standard-gid', f, group)

            if not module_rpms_ok and kernel_modules_regex.search(f) and not is_kernel_package:
                printError(pkg, "kernel-modules-not-in-kernel-packages", f)

            if tmp_regex.search(f):
                printError(pkg, 'dir-or-file-in-tmp', f)
            elif f.startswith('/mnt/'):
                printError(pkg, 'dir-or-file-in-mnt', f)
            elif f.startswith('/opt/'):
                printError(pkg, 'dir-or-file-in-opt', f)
            elif f.startswith('/usr/local/'):
                printError(pkg, 'dir-or-file-in-usr-local', f)
            elif f.startswith('/var/local/'):
                printError(pkg, 'dir-or-file-in-var-local', f)
            elif sub_bin_regex.search(f):
                printError(pkg, 'subdir-in-bin', f)
            elif backup_regex.search(f):
                printError(pkg, 'backup-file-in-package', f)
            elif f.startswith('/home/'):
                printError(pkg, 'dir-or-file-in-home', f)
            elif scm_regex.search(f):
                printError(pkg, 'version-control-internal-file', f)
            elif f.endswith('/.htaccess'):
                printError(pkg, 'htaccess-file', f)
            elif hidden_file_regex.search(f):
                printWarning(pkg, 'hidden-file-or-dir', f)
            elif manifest_perl_regex.search(f):
                printWarning(pkg, 'manifest-in-perl-module', f)
            elif siteperl_perl_regex.search(f):
                printWarning(pkg, 'siteperl-in-perl-module', f)
            elif f == '/usr/info/dir' or f == '/usr/share/info/dir':
                printError(pkg, 'info-dir-file', f)

            res=logrotate_regex.search(f)
            logrotate_file=res or logrotate_file
            if res and res.group(1) != pkg.name:
                printError(pkg, 'incoherent-logrotate-file', f)
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
                    if setuid:
                        printError(pkg, 'setuid-binary', f, setuid, oct(perm))
                    if setgid:
                        if not (group == 'games' and
                                (games_path_regex.search(f) or games_group_regex.search(pkg[rpm.RPMTAG_GROUP]))):
                            printError(pkg, 'setgid-binary', f, setgid, oct(perm))
                    if mode & 0777 != 0755:
                        printError(pkg, 'non-standard-executable-perm', f, oct(perm))

            if log_regex.search(f):
                log_file=f

            # normal file check
            if stat.S_ISREG(mode):

                if not devel_pkg:
                    if lib_path_regex.search(f):
                        lib_file=1
                    elif not is_doc:
                        non_lib_file=f

                if log_regex.search(f):
                    nonexec_file = 1
                    if user != 'root':
                        printError(pkg, 'non-root-user-log-file', f, user)
                    if group != 'root':
                        printError(pkg, 'non-root-group-log-file', f, group)
                    if not f in ghost_files:
                        printError(pkg, 'non-ghost-file', f)

                if doc_regex.search(f):
                    nonexec_file = 1
                    if not is_doc:
                        printError(pkg, 'not-listed-as-documentation', f)

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

                # check depmod call in %post and %postun
                res=not is_kernel_package and kernel_modules_regex.search(f)
                if res:
                    kernel_version=res.group(1)
                    kernel_version_regex=re.compile('depmod -a.*F /boot/System.map-' + kernel_version + '.*' + kernel_version, re.MULTILINE | re.DOTALL)
                    postin=pkg[rpm.RPMTAG_POSTIN] or pkg[rpm.RPMTAG_POSTINPROG]
                    if not postin or not depmod_regex.search(postin):
                        printError(pkg, 'module-without-depmod-postin', f)
                    # check that we run depmod on the right kernel
                    else:
                        if not kernel_version_regex.search(postin):
                            printError(pkg, 'postin-with-wrong-depmod', f)

                    postun=pkg[rpm.RPMTAG_POSTUN] or pkg[rpm.RPMTAG_POSTUNPROG]
                    if not postun or not depmod_regex.search(postun):
                        printError(pkg, 'module-without-depmod-postun', f)
                    # check that we run depmod on the right kernel
                    else:
                        if not kernel_version_regex.search(postun):
                            printError(pkg, 'postun-with-wrong-depmod', f)

                # check install-info call in %post and %postun
                if f.startswith('/usr/share/info/'):
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
                if not devel_pkg and not is_doc and \
                       (includefile_regex.search(f) or \
                        develfile_regex.search(f) or \
                        buildconfigfile_regex.search(f)):
                    printWarning(pkg, 'devel-file-in-non-devel-package', f)
                if mode & 0444 != 0444 and perm & 07000 == 0 and f[0:len('/var/log')] != '/var/log':
                    printError(pkg, 'non-readable', f, oct(perm))
                if size == 0 and not normal_zero_length_regex.search(f) and f not in ghost_files:
                    printError(pkg, 'zero-length', f)

                if mode & 0002 != 0:
                    printError(pkg, 'world-writable', f, oct(perm))

                if not perl_dep_error:
                    res=perl_regex.search(f)
                    if res:
                        if perl_version_trick:
                            vers = res.group(1) + '.' + res.group(2)
                        else:
                            vers = res.group(1) + res.group(2)
                        if not (pkg.check_versioned_dep('perl-base', vers) or
                                pkg.check_versioned_dep('perl', vers)):
                            printError(pkg, 'no-dependency-on', 'perl-base', vers)
                            perl_dep_error=1

                if not python_dep_error:
                    res=python_regex.search(f)
                    if res:
                        if not (pkg.check_versioned_dep('python-base', res.group(1)) or
                                pkg.check_versioned_dep('python', res.group(1))):
                            printError(pkg, 'no-dependency-on', 'python-base', res.group(1))
                            python_dep_error=1

                # normal executable check
                if mode & stat.S_IXUSR and perm != 0755:
                    printError(pkg, 'non-standard-executable-perm', f, oct(perm))

                if mode & 0111 != 0:
                    if f in config_files:
                        printError(pkg, 'executable-marked-as-config-file', f)
                    if not nonexec_file:
                        # doc_regex and log_regex checked earlier, no match,
                        # check rest of usual cases here.  Sourced scripts have
                        # their own check, so disregard them here.
                        nonexec_file = f.endswith('.pc') or \
                                       compr_regex.search(f) or \
                                       includefile_regex.search(f) or \
                                       develfile_regex.search(f) or \
                                       logrotate_regex.search(f)
                    if nonexec_file:
                        printWarning(pkg, 'spurious-executable-perm', f)
                elif f.startswith('/etc/'):
                    if not f in config_files and not f in ghost_files:
                        printWarning(pkg, 'non-conffile-in-etc', f)

                if pkg.arch == 'noarch' and f.startswith('/usr/lib64/python'):
                    printError(pkg, 'noarch-python-in-64bit-path', f)

            # normal dir check
            elif stat.S_ISDIR(mode):
                if mode & 01002 == 2: # world writable without sticky bit
                    printError(pkg, 'world-writable', f, oct(perm))
                if perm != 0755:
                    printError(pkg, 'non-standard-dir-perm', f, oct(perm))
                if pkg.name not in filesys_packages:
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
                    if (not is_so) and link not in files.keys() and link not in req_names:
                        is_exception=0
                        for e in dangling_exceptions:
                            if e[0].search(link):
                                is_exception=e[1]
                                break
                        if is_exception:
                            if is_exception not in req_names:
                                printWarning(pkg, 'no-dependency-on', is_exception)
                        else:
                            printWarning(pkg, 'dangling-symlink', f, link)
                    linktop=r.group(1)
                    r=absolute_regex.search(f)
                    if r:
                        filetop=r.group(1)
                        if filetop == linktop or use_relative_symlinks:
                            printWarning(pkg ,'symlink-should-be-relative', f, link)
                # relative link
                else:
                    if not is_so:
                        extractedfile = '%s%s/%s' % (pkg.dirName(), os.path.dirname(f), link)
                        extractedfile = os.path.normpath(extractedfile)
                        pkgfile = '%s/%s' % (os.path.dirname(f), link)
                        pkgfile = os.path.normpath(pkgfile)
                        if not (files.has_key(pkgfile) or os.path.exists(extractedfile) or pkgfile in req_names):
                            is_exception=0
                            for e in dangling_exceptions:
                                if e[0].search(link):
                                    is_exception=e[1]
                                    break
                            if is_exception:
                                if not is_exception in req_names:
                                    printWarning(pkg, 'no-dependency-on', is_exception)
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
                            if linktop != lastpop and not use_relative_symlinks:
                                # relative link into other toplevel directory
                                printWarning(pkg, 'symlink-should-be-absolute', f, link)
                        # check additional segments for mistakes like `foo/../bar/'
                        for linksegment in string.split(mylink, '/'):
                            if linksegment == '..':
                                printError(pkg, 'symlink-contains-up-and-down-segments', f, link)

            # check text file
            if stat.S_ISREG(mode):
                path=pkg.dirName() + '/' + f
                if os.access(path, os.R_OK):
                    if istextfile(path, pkg):
                        fobj = open(path, 'r')
                        try:
                            line = fobj.readline()
                        finally:
                            fobj.close()
                        res=None
                        # ignore perl module shebang -- TODO: disputed...
                        if not f.endswith('.pm'):
                            res=shebang_regex.search(line)
                        # sourced scripts should not be executable
                        if sourced_script_regex.search(f):
                            if res:
                                printError(pkg, 'sourced-script-with-shebang', f)
                            if mode & 0111 != 0:
                                printError(pkg, 'executable-sourced-script', f, oct(perm))
                        # ...but executed ones should
                        elif res or mode & 0111 != 0 or script_regex.search(f):
                            if res:
                                if not interpreter_regex.search(res.group(1)):
                                    printError(pkg, 'wrong-script-interpreter', f, '"' + res.group(1) + '"')
                            elif not nonexec_file and not (lib_path_regex.search(f) and f.endswith('.la')):
                                printError(pkg, 'script-without-shebang', f)

                            if mode & 0111 == 0 and not is_doc:
                                printError(pkg, 'non-executable-script', f, oct(perm))
                            if line.endswith('\r\n'):
                                printError(pkg, 'wrong-script-end-of-line-encoding', f)
                        elif is_doc:
                            fl = f.lower()
                            if fl.endswith('.rtf'): # TODO: others, eg. HTML?
                                pass
                            elif line.endswith('\r\n'):
                                printWarning(pkg, 'wrong-file-end-of-line-encoding', f)
                            # We check only doc text files for UTF-8-ness;
                            # checking everything may be slow and can generate
                            # lots of unwanted noise.
                            if use_utf8 and not is_utf8(path):
                                printWarning(pkg, 'file-not-utf8', f)

                    elif is_doc and compr_regex.search(f):
                        # compressed docs, eg. info and man files etc
                        if use_utf8 and not is_utf8(path):
                            printWarning(pkg, 'file-not-utf8', f)


            if f.startswith('/etc/cron.d/'):
                if stat.S_ISLNK(mode):
                    printError(pkg, 'symlink-crontab-file', f)

                if mode & 0111:
                    printError(pkg, 'executable-crontab-file', f)

                if stat.S_IWGRP & mode or stat.S_IWOTH & mode:
                    printError(pkg, 'non-owner-writeable-only-crontab-file', f)

        if log_file and not logrotate_file:
            printWarning(pkg, 'log-files-without-logrotate', log_file)

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
'''A file in this package is owned by a non standard user.
Standard users are:
%s''' % fill(", ".join(standard_users)),

'non-standard-gid',
'''A file in this package is owned by a non standard group.
Standard groups are:
%s''' % fill(", ".join(standard_groups)),

'library-without-ldconfig-postin',
'''This package contains a library and provides no %post scriptlet containing
a call to ldconfig.''',

'postin-without-ldconfig',
'''This package contains a library and its %post scriptlet doesn't call ldconfig.''',

'library-without-ldconfig-postun',
'''This package contains a library and provides no %postun scriptlet containing
a call to ldconfig.''',

'postun-without-ldconfig',
'''This package contains a library and its %postun doesn't call ldconfig.''',

'info-files-without-install-info-postin',
'''This package contains info files and provides no %post scriptlet containing
a call to install-info.''',

'postin-without-install-info',
'''This package contains info files and its %post doesn't call install-info.''',

'info-files-without-install-info-postun',
'''This package contains info files and provides no %postun scriptlet containing
a call to install-info.''',

'postun-without-install-info',
'''This package contains info files and its %postun doesn't call install-info.''',

'perl-temp-file',
'''You have a perl temporary file in your package. Usually, this
file is beginning with a dot (.) and contain "perl" in its name.''',

'dir-or-file-in-tmp',
'''A file in the package is located in /tmp. It's not permitted
for packages to install files in this directory.''',

'dir-or-file-in-mnt',
'''A file in the package is located in /mnt. It's not permitted
for packages to install files in this directory.''',

'dir-or-file-in-opt',
'''A file in the package is located in /opt. It's not permitted
for packages to install files in this directory.''',

'dir-or-file-in-usr-local',
'''A file in the package is located in /usr/local. It's not permitted
for packages to install files in this directory.''',

'dir-or-file-in-var-local',
'''A file in the package is located in /var/local. It's not permitted
for packages to install files in this directory.''',

'subdir-in-bin',
'''The package contains a subdirectory in /usr/bin. It's not permitted to
create a subdir there. Create it in /usr/lib/ instead.''',

'backup-file-in-package',
'''You have a backup file in your package. The files are usually
beginning with ~ (vi) or #file# (emacs). Please remove it and rebuild
your package.''',

'dir-or-file-in-home',
'''A file in the package is located in /home. It's not permitted
for packages to install files in this directory.''',

'version-control-internal-file',
'''You have included file(s) internally used by a version control system
in the package. Move these files out of the package and rebuild it.''',

'htaccess-file',
'''You have individual apache configuration .htaccess file(s) in your package.
Replace them by a central configuration file in /etc/, according to the web 
application packaging policy for your distribution.''',

'info-dir-file',
'''You have /usr/info/dir or /usr/share/info/dir in your package. It will cause
conflicts with other packages and thus is not allowed. Please remove it and
rebuild your package.''',

'non-conffile-in-etc',
'''A non-executable file in your package is being installed in /etc, but is not
a configuration file. All non-executable files in /etc should be configuration
files. Mark the file as %config in the spec file.''',

'compressed-symlink-with-wrong-ext',
'''The symlink points to a compressed file but doesn't use the same extension.''',

'setuid-binary',
'''The file is setuid, this may be dangerous, especially if this 
file is setuid root.''',

'setgid-binary',
'''The file is setgid. Usually this is a packaging bug. If this is a game, 
then, you should use the proper rpm group, or location.''',

'non-standard-executable-perm',
'''A standard executable should have permission set to 0755. If you get this
message, it means that you have a wrong executable permissions in some files
included in your package.''',

'non-executable-in-bin',
'''A file is being installed in /usr/bin, but is not an executable. Be sure
that the file is an executable or that it has executable permissions.''',

'devel-file-in-non-devel-package',
'''A development file (usually source code) is located in a non-devel
package. If you want to include source code in your package, be sure to
create a development package.''',

'non-standard-dir-perm',
'''A standard directory should have permission set to 0755. If you get this
message, it means that you have wrong directory permissions in some dirs
included in your package.''',

'spurious-executable-perm',
'''The file is installed with executable permissions, but was identified as one
that probably should not be executable.  Verify if the executable bits are
desired, and remove if not.''',

'world-writable',
'''A file or directory in the package is installed with world writable
permissions, which is most likely a security issue.''',

'standard-dir-owned-by-package',
'''This package owns a directory that is part of the standard hierarchy, which
can lead to default directory permissions or ownerships being changed to
something non-standard.''',

'no-dependency-on',
'''
''',

'dangling-symlink',
'''The symbolic link points nowhere.''',

'symlink-should-be-relative',
'''Absolute symlinks are problematic eg. when working with chroot environments.''',

'dangling-relative-symlink',
'''The relative symbolic link points nowhere.''',

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
'''The file can't be read by everybody. If this is expected (for security
reasons), contact your rpmlint distributor to get it added to the list of
exceptions for your distro (or add it to your local configuration if you
installed rpmlint from the source tarball).''',

'incoherent-logrotate-file',
'''Your logrotate file should be named /etc/logrotate.d/<package name>.''',

'non-root-user-log-file',
'''If you need log files owned by a non-root user, just create a subdir in
/var/log and put your log files in it.''',

'non-root-group-log-file',
'''If you need log files owned by a non-root group, just create a subdir in
/var/log and put your log files in it.''',

'non-ghost-file',
'''File should be tagged %ghost.''',

'outside-libdir-files',
'''This library package must not contain non library files to allow 64
and 32 bits versions of the package to coexist.''',

'hidden-file-or-dir',
'''The file or directory is hidden. You should see if this is normal,
and delete it from the package if not.''',

'module-without-depmod-postin',
'''This package contains a kernel module but provides no call to depmod in the
%post scriptlet.''',

'postin-with-wrong-depmod',
'''This package contains a kernel module but its %post scriptlet calls depmod
for the wrong kernel.''',

'module-without-depmod-postun',
'''This package contains a kernel module but provides no call to depmod in the
%postun scriptlet.''',

'postun-with-wrong-depmod',
'''This package contains a kernel module but its %postun scriptlet calls depmod
for the wrong kernel.''',

'log-files-without-logrotate',
'''This package contains files in /var/log/ without adding logrotate
configuration for them.''',

'mispelled-macro',
'''This package contains a file which matches %{.*}; this is often the sign
of a misspelled macro. Please check your spec file.''',

'manifest-in-perl-module',
'''This perl module package contains a MANIFEST or a MANIFEST.SKIP file
in the documentation directory.''',

'siteperl-in-perl-module',
'''This perl module package installs files under the subdirectory site_perl,
while they must appear under vendor_perl.''',

'executable-marked-as-config-file',
'''Executables must not be marked as config files because that may
prevent upgrades from working correctly. If you need to be able to
customize an executable, make it for example read a config file in
/etc/sysconfig.''',

'sourced-script-with-shebang',
'''This text file contains a shebang, but is meant to be sourced, not executed.''',

'executable-sourced-script',
'''This text file has executable bit set, but is meant to be sourced, not
executed.''',

'wrong-script-interpreter',
'''This script uses an incorrect interpreter.''',

'non-executable-script',
'''This text file contains a shebang or is located in a path dedicated for
executables, but lacks the executable bits and cannot thus be executed.  If
the file is meant to be an executable script, add the executable bits,
otherwise remove the shebang or move the file elsewhere.''',

'script-without-shebang',
'''This text file has executable bits set or is located in a path dedicated
for executables, but lacks a shebang and cannot thus be executed.  If the file
is meant to be an executable script, add the shebang, otherwise remove the
executable bits or move the file elsewhere.''',

'wrong-script-end-of-line-encoding',
'''This script has wrong end-of-line encoding, usually caused by creation or
modification on a non-Unix system. It will prevent its execution.''',

'wrong-file-end-of-line-encoding',
'''This file has wrong end-of-line encoding, usually caused by creation or
modification on a non-Unix system. It could prevent it from being displayed
correctly in some circumstances.''',

'file-not-utf8',
'''The character encoding of this file is not UTF-8.  Consider converting it
in the specfile for example using iconv(1).''',

'filename-not-utf8',
'''The character encoding of the name of this file is not UTF-8.  Rename it.''',

'file-in-meta-package',
'''This package seems to be a meta-package (an empty package used to require
other packages), but it is not empty. You should remove or rename it, see the
option MetaPackageRegexp.''',

'empty-debuginfo-package',
'''This debuginfo package contains no files.  This is often a sign of binaries
being unexpectedly stripped too early during the build, rpmbuild not being able
to strip the binaries, the package actually being a noarch one but erratically
packaged as arch dependent, or something else.  Verify what the case is, and
if there's no way to produce useful debuginfo out of it, disable creation of
the debuginfo package.''',

'read-error',
'''This file could not be read.  A reason for this could be that the info about
it in the rpm header indicates that it is supposed to be a readable normal file
but it actually is not in the filesystem.  Because of this, some checks will
be skipped.''',

'executable-crontab-file',
'''This crontab file has executable bit set, which is refused by newer version 
of cron''',

'non-owner-writeable-only-crontab-file',
'''This crontab file is writeable by other users as its owner, which is refused 
by newer version of cron and insecure''',

'symlink-crontab-file',
'''This crontab file is a symbolic link, which is insecure and refused by newer 
version of cron''',
)

# FilesCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
