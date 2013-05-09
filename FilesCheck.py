# -*- coding: utf-8 -*-
#############################################################################
# File          : FilesCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Mon Oct  4 19:32:49 1999
# Purpose       : test various aspects on files: locations, owner, groups,
#                 permission, setuid, setgid...
#############################################################################

from datetime import datetime
import commands
import os
import re
import stat
import string

import rpm

from Filter import addDetails, printError, printWarning
from Pkg import catcmd, is_utf8, is_utf8_str
import AbstractCheck
import Config


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
    '/run',
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

DEFAULT_GAMES_GROUPS = 'Games'

DEFAULT_DANGLING_EXCEPTIONS = (['consolehelper$', 'usermode-consoleonly'],
                               )

# Standard users and groups from LSB Core 4.0.0: 21.2 User & Group Names
DEFAULT_STANDARD_USERS  = ('root', 'bin', 'daemon', 'adm', 'lp', 'sync',
                           'shutdown', 'halt', 'mail', 'news', 'uucp',
                           'operator', 'man', 'nobody',)
DEFAULT_STANDARD_GROUPS = ('root', 'bin', 'daemon', 'adm', 'lp', 'sync',
                           'shutdown', 'halt', 'mail', 'news', 'uucp',
                           'man', 'nobody',)

tmp_regex = re.compile('^(/var|/usr)?/tmp/')
sub_bin_regex = re.compile('^(/usr)?/s?bin/\S+/')
backup_regex = re.compile('(~|\#[^/]+\#|\.orig|\.rej)$')
compr_regex = re.compile('\.(gz|z|Z|zip|bz2|lzma|xz)$')
absolute_regex = re.compile('^/([^/]+)')
absolute2_regex = re.compile('^/?([^/]+)')
points_regex = re.compile('^\.\./(.*)')
doc_regex = re.compile('^/usr(/share|/X11R6)?/(doc|man|info)/')
bin_regex = re.compile('^/(?:usr/(?:s?bin|games)|s?bin)/(.*)')
includefile_regex = re.compile('\.(c|h)(pp|xx)?$', re.IGNORECASE)
develfile_regex = re.compile('\.(a|cmxa?|mli?)$')
buildconfigfile_regex = re.compile('(\.pc|/bin/.+-config)$')
# room for improvement with catching more -R, but also for false positives...
buildconfig_rpath_regex = re.compile('(?:-rpath|Wl,-R)\\b')
sofile_regex = re.compile('/lib(64)?/(.+/)?lib[^/]+\.so$')
devel_regex = re.compile('(.*)-(debug(info)?|devel|headers|source|static)$')
debuginfo_package_regex = re.compile('-debug(info)?$')
lib_regex = re.compile('lib(64)?/lib[^/]*\.so\..*')
ldconfig_regex = re.compile('^[^#]*ldconfig', re.MULTILINE)
depmod_regex = re.compile('^[^#]*depmod', re.MULTILINE)
install_info_regex = re.compile('^[^#]*install-info', re.MULTILINE)
perl_temp_file_regex = re.compile('.*perl.*/(\.packlist|perllocal\.pod)$')
scm_regex = re.compile('/CVS/[^/]+$|/\.(bzr|cvs|git|hg)ignore$|/\.hgtags$|/\.(bzr|git|hg|svn)/|/(\.arch-ids|{arch})/')
games_path_regex = re.compile('^/usr(/lib(64)?)?/games/')
games_group_regex = re.compile(Config.getOption('RpmGamesGroups', DEFAULT_GAMES_GROUPS))
dangling_exceptions = Config.getOption('DanglingSymlinkExceptions', DEFAULT_DANGLING_EXCEPTIONS)
logrotate_regex = re.compile('^/etc/logrotate\.d/(.*)')
module_rpms_ok = Config.getOption('KernelModuleRPMsOK', True)
kernel_modules_regex = re.compile('^/lib/modules/(2\.[23456]\.[0-9]+[^/]*?)/')
kernel_package_regex = re.compile('^kernel(22)?(-)?(smp|enterprise|bigmem|secure|BOOT|i686-up-4GB|p3-smp-64GB)?')
normal_zero_length_regex = re.compile('^/etc/security/console\.apps/|/\.nosearch$|/__init__\.py$')
perl_regex = re.compile('^/usr/lib/perl5/(?:vendor_perl/)?([0-9]+\.[0-9]+)\.([0-9]+)/')
python_regex = re.compile('^/usr/lib(?:64)?/python([.0-9]+)/')
python_bytecode_regex_pep3147 = re.compile('^(.*)/__pycache__/(.*)\.(.*)(\.py[oc])$')
python_bytecode_regex = re.compile('^(.*)(\.py[oc])$')
python_default_version = Config.getOption('PythonDefaultVersion', None)
perl_version_trick = Config.getOption('PerlVersionTrick', True)
log_regex = re.compile('^/var/log/[^/]+$')
lib_path_regex = re.compile('^(/usr(/X11R6)?)?/lib(64)?')
lib_package_regex = re.compile('^(lib|.+-libs)')
hidden_file_regex = re.compile('/\.[^/]*$')
manifest_perl_regex = re.compile('^/usr/share/doc/perl-.*/MANIFEST(\.SKIP)?$')
shebang_regex = re.compile('^#!\s*(\S+)')
interpreter_regex = re.compile('^/(usr/)?(s?bin|games|libexec(/.+)?|(lib(64)?|share)/.+)/[^/]+$')
script_regex = re.compile('^/((usr/)?s?bin|etc/(rc\.d/init\.d|X11/xinit\.d|cron\.(hourly|daily|monthly|weekly)))/')
sourced_script_regex = re.compile('^/etc/(bash_completion\.d|profile\.d)/')
use_utf8 = Config.getOption('UseUTF8', Config.USEUTF8_DEFAULT)
skipdocs_regex = re.compile(Config.getOption('SkipDocsRegexp', '\.(?:rtf|x?html?|svg|ml[ily]?)$'), re.IGNORECASE)
meta_package_regex = re.compile(Config.getOption('MetaPackageRegexp', '^(bundle|task)-'))
filesys_packages = ['filesystem'] # TODO: make configurable?
quotes_regex = re.compile('[\'"]+')
start_certificate_regex = re.compile('^-----BEGIN CERTIFICATE-----$')
start_private_key_regexp = re.compile('^----BEGIN PRIVATE KEY-----$')

for idx in range(0, len(dangling_exceptions)):
    dangling_exceptions[idx][0] = re.compile(dangling_exceptions[idx][0])
del idx

use_relative_symlinks = Config.getOption("UseRelativeSymlinks", True)

standard_groups = Config.getOption('StandardGroups', DEFAULT_STANDARD_GROUPS)
standard_users = Config.getOption('StandardUsers', DEFAULT_STANDARD_USERS)

non_readable_regexs = (re.compile('^/var/log/'),
                       re.compile('^/etc/(g?shadow-?|securetty)$'))

man_base_regex = re.compile(r'^/usr(?:/share)?/man(?:/overrides)?/man[^/]+/(.+)\.[1-9n]')
man_warn_regex = re.compile(r'^([^:]+:)\d+:\s*')
man_nowarn_regex = re.compile(
    # From Lintian: ignore common undefined macros from pod2man << Perl 5.10
    r'\`(Tr|IX)\' not defined|'
    # .so entries won't resolve as we're dealing with stdin
    r'No such file or directory|'
    # TODO, better handling for these (see e.g. Lintian)
    r'(can\'t break|cannot adjust) line')
man_warn_category = Config.getOption('ManWarningCategory', 'mac')

fsf_license_regex = re.compile('(GNU((\s+(Library|Lesser|Affero))?(\s+General)?\s+Public|\s+Free\s+Documentation)\s+Licen[cs]e|(GP|FD)L)', re.IGNORECASE)
fsf_wrong_address_regex = re.compile('(675\s+Mass\s+Ave|59\s+Temple\s+Place|Franklin\s+Steet|02139|02111-1307)', re.IGNORECASE)

scalable_icon_regex = re.compile(r'^/usr(?:/local)?/share/icons/.*/scalable/')

# loosely inspired from Python Cookbook
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/173220
text_characters = "".join(map(chr, range(32, 127)) + list("\n\r\t\b"))
_null_trans = string.maketrans("", "")

def peek(filename, pkg, length=1024):
    """Peek into a file, return a chunk from its beginning and a flag if it
       seems to be a text file."""
    fobj = None
    chunk = None
    try:
        fobj = open(filename, 'rb')
        chunk = fobj.read(length)
        fobj.close()
    except IOError, e: # eg. https://bugzilla.redhat.com/209876
        printWarning(pkg, 'read-error', e)
        if fobj:
            fobj.close()
        return (chunk, False)

    if "\0" in chunk:
        return (chunk, False)

    if not chunk:  # Empty files are considered text
        return (chunk, True)

    fl = filename.lower()

    # PDF's are binary but often detected as text by the algorithm below
    if fl.endswith('.pdf') and chunk.startswith('%PDF-'):
        return (chunk, False)
    # Ditto RDoc RI files
    if fl.endswith('.ri') and '/ri/' in fl:
        return (chunk, False)

    # Get the non-text characters (maps a character to itself then
    # use the 'remove' option to get rid of the text characters.)
    t = chunk.translate(_null_trans, text_characters)

    # If more than 30% non-text characters, then consider it a binary file
    istext = float(len(t))/len(chunk) <= 0.30
    return (chunk, istext)

# See Python sources for a full list of the values here.
# http://hg.python.org/cpython/file/tip/Lib/importlib/_bootstrap.py
# http://hg.python.org/cpython/file/2.7/Python/import.c
_python_magic_values = {
    '2.2': 60717,
    '2.3': 62011,
    '2.4': 62061,
    '2.5': 62131,
    '2.6': 62161,
    '2.7': 62211,
    '3.0': 3130,
    '3.1': 3150,
    '3.2': 3180,
    '3.3': 3230,
    '3.4': 3260,
    }

def get_expected_pyc_magic(path):
    """.pyc/.pyo files embed a 4-byte magic value identifying which version of
    the python bytecode ABI they are for. Given a path to a .pyc/.pyo file,
    return a (magic ABI value, python version) tuple.  For example,
    '/usr/lib/python3.1/foo.pyc' should return (3151, '3.1').
    The first value will be None if the python version was not resolved
    from the given pathname and the PythonDefaultVersion configuration
    variable is not set, or if we don't know the magic ABI value for the
    python version (no matter from which source the version came from).
    The second value will be None if a python version could not be resolved
    from the given pathname."""

    ver_from_path = None
    m = python_regex.search(path)
    if m:
        ver_from_path = m.group(1)

    expected_version = ver_from_path or python_default_version
    expected_magic_value = _python_magic_values.get(expected_version)

    if not expected_magic_value:
        return (None, ver_from_path)

    # In Python 2, if Py_UnicodeFlag is set, Python's import code uses a value
    # one higher, but this is off by default. In Python 3.0 and 3.1 (but no
    # longer in 3.2), it always uses the value one higher:
    if expected_version[:3] in ('3.0', '3.1'):
        expected_magic_value += 1

    return (expected_magic_value, ver_from_path)

def py_demarshal_long(b):
    """Counterpart to Python's PyMarshal_ReadLongFromFile, operating on the
    bytes in a string."""
    return (ord(b[0])
            + (ord(b[1]) << 8)
            + (ord(b[2]) << 16)
            + (ord(b[3]) << 24))

def python_bytecode_to_script(path):
    """Given a python bytecode path, give the path of the .py file
    (or None if not python bytecode)."""

    res = python_bytecode_regex_pep3147.search(path)
    if res:
        return res.group(1) + '/' + res.group(2) + '.py'

    res = python_bytecode_regex.search(path)
    if res:
        return res.group(1) + '.py'

    return None

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
        devel_pkg = devel_regex.search(pkg.name)

        config_files = pkg.configFiles()
        ghost_files = pkg.ghostFiles()
        doc_files = pkg.docFiles()
        req_names = pkg.req_names()
        lib_package = lib_package_regex.search(pkg.name)
        is_kernel_package = kernel_package_regex.search(pkg.name)
        debuginfo_package = debuginfo_package_regex.search(pkg.name)

        # report these errors only once
        perl_dep_error = False
        python_dep_error = False
        lib_file = False
        non_lib_file = None
        log_file = None
        logrotate_file = False
        debuginfo_srcs = False
        debuginfo_debugs = False

        if not doc_files:
            printWarning(pkg, 'no-documentation')

        if files:
            if meta_package_regex.search(pkg.name):
                printWarning(pkg, 'file-in-meta-package')
        elif debuginfo_package:
            printError(pkg, 'empty-debuginfo-package')

        # Unique (rdev, inode) combinations
        hardlinks = {}

        # All executable files from standard bin dirs (basename => [paths])
        # Hack: basenames with empty paths links are symlinks (not subject
        # to duplicate binary check, but yes for man page existence check)
        bindir_exes = {}

        # All man page "base" names (without section etc extensions)
        man_basenames = set()

        for f, pkgfile in files.items():
            mode = pkgfile.mode
            user = pkgfile.user
            group = pkgfile.group
            link = pkgfile.linkto
            size = pkgfile.size
            rdev = pkgfile.rdev
            inode = pkgfile.inode
            is_doc = f in doc_files
            nonexec_file = False

            for match in AbstractCheck.macro_regex.findall(f):
                printWarning(pkg, 'unexpanded-macro', f, match)
            if standard_users and user not in standard_users:
                printWarning(pkg, 'non-standard-uid', f, user)
            if standard_groups and group not in standard_groups:
                printWarning(pkg, 'non-standard-gid', f, group)

            if not module_rpms_ok and kernel_modules_regex.search(f) and not \
                    is_kernel_package:
                printError(pkg, "kernel-modules-not-in-kernel-packages", f)

            for i in ['mnt','opt','usr-local','var-local','home']:
                if f.startswith('/%s/' % i.replace('-','/')):
                    printError(pkg, 'dir-or-file-in-%s' % i, f)

            if tmp_regex.search(f):
                printError(pkg, 'dir-or-file-in-tmp', f)

            elif f.startswith('/var/run/'):
                if f not in ghost_files:
                    printWarning(pkg, 'non-ghost-in-var-run', f)
            elif f.startswith('/var/lock/'):
                if f not in ghost_files:
                    printWarning(pkg, 'non-ghost-in-var-lock', f)
            elif sub_bin_regex.search(f):
                printError(pkg, 'subdir-in-bin', f)
            elif '/site_perl/' in f:
                printWarning(pkg, 'siteperl-in-perl-module', f)

            if backup_regex.search(f):
                printError(pkg, 'backup-file-in-package', f)
            elif scm_regex.search(f):
                printError(pkg, 'version-control-internal-file', f)
            elif f.endswith('/.htaccess'):
                printError(pkg, 'htaccess-file', f)
            elif hidden_file_regex.search(f) and not f.startswith("/etc/skel/"):
                printWarning(pkg, 'hidden-file-or-dir', f)
            elif manifest_perl_regex.search(f):
                printWarning(pkg, 'manifest-in-perl-module', f)
            elif f == '/usr/info/dir' or f == '/usr/share/info/dir':
                printError(pkg, 'info-dir-file', f)

            res = logrotate_regex.search(f)
            if res:
                logrotate_file = True
                if res.group(1) != pkg.name:
                    printError(pkg, 'incoherent-logrotate-file', f)

            if link != '':
                ext = compr_regex.search(link)
                if ext:
                    if not re.compile('\.' + ext.group(1) + '$').search(f):
                        printError(pkg, 'compressed-symlink-with-wrong-ext',
                                   f, link)

            perm = mode & 07777

            if log_regex.search(f):
                log_file = f

            # Hardlink check
            hardlink = hardlinks.get((rdev, inode))
            if hardlink and os.path.dirname(hardlink) != os.path.dirname(f):
                printWarning(pkg, 'cross-directory-hard-link', f, hardlink)
            hardlinks[(rdev, inode)] = f

            # normal file check
            if stat.S_ISREG(mode):

                # set[ug]id bit check
                if stat.S_ISGID & mode or stat.S_ISUID & mode:
                    if stat.S_ISUID & mode:
                        printError(pkg, 'setuid-binary', f, user, oct(perm))
                    if stat.S_ISGID & mode:
                        if not (group == 'games' and
                                (games_path_regex.search(f) or
                                 games_group_regex.search(
                                    pkg[rpm.RPMTAG_GROUP]))):
                            printError(pkg, 'setgid-binary', f, group,
                                       oct(perm))
                    if mode & 0777 != 0755:
                        printError(pkg, 'non-standard-executable-perm', f,
                                   oct(perm))

                # Prefetch scriptlets, strip quotes from them (#169)
                postin = pkg[rpm.RPMTAG_POSTIN] or \
                    pkg.scriptprog(rpm.RPMTAG_POSTINPROG)
                if postin:
                    postin = quotes_regex.sub('', postin)
                postun = pkg[rpm.RPMTAG_POSTUN] or \
                    pkg.scriptprog(rpm.RPMTAG_POSTUNPROG)
                if postun:
                    postun = quotes_regex.sub('', postun)

                if not devel_pkg:
                    if lib_path_regex.search(f):
                        lib_file = True
                    elif not is_doc:
                        non_lib_file = f

                if log_regex.search(f):
                    nonexec_file = True
                    if user != 'root':
                        printError(pkg, 'non-root-user-log-file', f, user)
                    if group != 'root':
                        printError(pkg, 'non-root-group-log-file', f, group)
                    if f not in ghost_files:
                        printError(pkg, 'non-ghost-file', f)

                chunk = None
                istext = False
                if os.access(pkgfile.path, os.R_OK):
                    (chunk, istext) = peek(pkgfile.path, pkg)

                interpreter = None
                if chunk:
                    res = shebang_regex.search(chunk)
                    if res:
                        interpreter = res.group(1)

                if doc_regex.search(f):
                    if not interpreter:
                        nonexec_file = True
                    if not is_doc:
                        printError(pkg, 'not-listed-as-documentation', f)

                # check ldconfig call in %post and %postun
                if lib_regex.search(f):
                    if not postin:
                        printError(pkg, 'library-without-ldconfig-postin', f)
                    else:
                        if not ldconfig_regex.search(postin):
                            printError(pkg, 'postin-without-ldconfig', f)

                    if not postun:
                        printError(pkg, 'library-without-ldconfig-postun', f)
                    else:
                        if not ldconfig_regex.search(postun):
                            printError(pkg, 'postun-without-ldconfig', f)

                # check depmod call in %post and %postun
                res = not is_kernel_package and kernel_modules_regex.search(f)
                if res:
                    kernel_version = res.group(1)
                    kernel_version_regex = re.compile(
                        '\\bdepmod\s+-a.*F\s+/boot/System\.map-' +
                        re.escape(kernel_version) + '\\b.*\\b' +
                        re.escape(kernel_version) + '\\b',
                        re.MULTILINE | re.DOTALL)

                    if not postin or not depmod_regex.search(postin):
                        printError(pkg, 'module-without-depmod-postin', f)
                    # check that we run depmod on the right kernel
                    elif not kernel_version_regex.search(postin):
                        printError(pkg, 'postin-with-wrong-depmod', f)

                    if not postun or not depmod_regex.search(postun):
                        printError(pkg, 'module-without-depmod-postun', f)
                    # check that we run depmod on the right kernel
                    elif not kernel_version_regex.search(postun):
                        printError(pkg, 'postun-with-wrong-depmod', f)

                # check install-info call in %post and %postun
                if f.startswith('/usr/share/info/'):
                    if not postin:
                        printError(pkg,
                                   'info-files-without-install-info-postin', f)
                    elif not install_info_regex.search(postin):
                        printError(pkg, 'postin-without-install-info', f)

                    preun = pkg[rpm.RPMTAG_PREUN] or \
                        pkg.scriptprog(rpm.RPMTAG_PREUNPROG)
                    if not postun and not preun:
                        printError(pkg,
                                   'info-files-without-install-info-postun', f)
                    elif (not postun or
                          not install_info_regex.search(postun)) and \
                          (not preun or not install_info_regex.search(preun)):
                        printError(pkg, 'postin-without-install-info', f)

                # check perl temp file
                if perl_temp_file_regex.search(f):
                    printWarning(pkg, 'perl-temp-file', f)

                is_buildconfig = buildconfigfile_regex.search(f) and True

                # check rpaths in buildconfig files
                if is_buildconfig:
                    ln = pkg.grep(buildconfig_rpath_regex, f)
                    if ln:
                        printError(pkg, 'rpath-in-buildconfig', f, 'lines', ln)

                res = bin_regex.search(f)
                if res:
                    if mode & 0111 == 0:
                        printWarning(pkg, 'non-executable-in-bin', f, oct(perm))
                    else:
                        exe = res.group(1)
                        if "/" not in exe:
                            bindir_exes.setdefault(exe, []).append(f)

                if not devel_pkg and not is_doc and \
                       (includefile_regex.search(f) or \
                        develfile_regex.search(f) or is_buildconfig):
                    printWarning(pkg, 'devel-file-in-non-devel-package', f)
                if mode & 0444 != 0444 and perm & 07000 == 0:
                    ok_nonreadable = False
                    for regex in non_readable_regexs:
                        if regex.search(f):
                            ok_nonreadable = True
                            break
                    if not ok_nonreadable:
                        printError(pkg, 'non-readable', f, oct(perm))
                if size == 0 and not normal_zero_length_regex.search(f) and \
                        f not in ghost_files:
                    printError(pkg, 'zero-length', f)

                if mode & 0002 != 0:
                    printError(pkg, 'world-writable', f, oct(perm))

                if not perl_dep_error:
                    res = perl_regex.search(f)
                    if res:
                        if perl_version_trick:
                            vers = res.group(1) + '.' + res.group(2)
                        else:
                            vers = res.group(1) + res.group(2)
                        if not (pkg.check_versioned_dep('perl-base', vers) or
                                pkg.check_versioned_dep('perl', vers)):
                            printError(pkg, 'no-dependency-on',
                                       'perl-base', vers)
                            perl_dep_error = True

                if not python_dep_error:
                    res = python_regex.search(f)
                    if res and not (pkg.check_versioned_dep('python-base',
                                                            res.group(1)) or
                                    pkg.check_versioned_dep('python',
                                                            res.group(1))):
                        printError(pkg, 'no-dependency-on', 'python-base',
                                   res.group(1))
                        python_dep_error = True

                source_file = python_bytecode_to_script(f)
                if source_file:
                    if source_file in files:
                        if chunk:
                            # Verify that the magic ABI value embedded in the
                            # .pyc header is correct
                            found_magic = py_demarshal_long(chunk[:4]) & 0xffff
                            exp_magic, exp_version = get_expected_pyc_magic(f)
                            if exp_magic and found_magic != exp_magic:
                                found_version = 'unknown'
                                for (pv, pm) in _python_magic_values.items():
                                    if pm == found_magic:
                                        found_version = pv
                                        break
                                # If expected version was from the file path,
                                # issue # an error, otherwise a warning.
                                msg = (pkg, 'python-bytecode-wrong-magic-value',
                                       f, "expected %d (%s), found %d (%s)" %
                                       (exp_magic,
                                        exp_version or python_default_version,
                                        found_magic, found_version))
                                if exp_version is not None:
                                    printError(*msg)
                                else:
                                    printWarning(*msg)

                            # Verify that the timestamp embedded in the .pyc
                            # header matches the mtime of the .py file:
                            pyc_timestamp = py_demarshal_long(chunk[4:8])
                            # If it's a symlink, check target file mtime.
                            srcfile = pkg.readlink(files[source_file])
                            if not srcfile:
                                printWarning(
                                    pkg, 'python-bytecode-without-source', f)
                            elif pyc_timestamp != srcfile.mtime:
                                cts = datetime.fromtimestamp(
                                    pyc_timestamp).isoformat()
                                sts = datetime.fromtimestamp(
                                    srcfile.mtime).isoformat()
                                printError(pkg,
                                           'python-bytecode-inconsistent-mtime',
                                           f, cts, srcfile.name, sts)
                    else:
                        printWarning(pkg, 'python-bytecode-without-source', f)

                # normal executable check
                if mode & stat.S_IXUSR and perm != 0755:
                    printError(pkg, 'non-standard-executable-perm',
                               f, oct(perm))
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
                elif f.startswith('/etc/') and f not in config_files and \
                        f not in ghost_files:
                    printWarning(pkg, 'non-conffile-in-etc', f)

                if pkg.arch == 'noarch' and f.startswith('/usr/lib64/python'):
                    printError(pkg, 'noarch-python-in-64bit-path', f)

                if debuginfo_package:
                    if f.endswith('.debug'):
                        debuginfo_debugs = True
                    else:
                        debuginfo_srcs = True

                res = man_base_regex.search(f)
                if res:
                    man_basenames.add(res.group(1))
                    if use_utf8 and chunk:
                        # TODO: better shell escaping or seq based invocation
                        cmd = commands.getstatusoutput(
                            'env LC_ALL=C %s "%s" | gtbl | '
                            'env LC_ALL=en_US.UTF-8 groff -mtty-char -Tutf8 '
                            '-P-c -mandoc -w%s >/dev/null' %
                            (catcmd(f), pkgfile.path, man_warn_category))
                        for line in cmd[1].split("\n"):
                            res = man_warn_regex.search(line)
                            if not res or man_nowarn_regex.search(line):
                                continue
                            printWarning(pkg, "manual-page-warning", f,
                                         line[res.end(1):])

                if f.endswith(".svgz") and f[0:-1] not in files \
                        and scalable_icon_regex.search(f):
                    printWarning(pkg, "gzipped-svg-icon", f)

                if f.endswith('.pem'):
                    if f not in ghost_files:
                        if pkg.grep(start_certificate_regex, f):
                            printWarning(pkg, 'pem-certificate', f)
                        if pkg.grep(start_private_key_regexp, f):
                            printError(pkg, 'pem-private-key', f)

                # text file checks
                if istext:
                    # ignore perl module shebang -- TODO: disputed...
                    if f.endswith('.pm'):
                        interpreter = None
                    # sourced scripts should not be executable
                    if sourced_script_regex.search(f):
                        if interpreter:
                            printError(pkg,
                                       'sourced-script-with-shebang', f,
                                       interpreter)
                        if mode & 0111 != 0:
                            printError(pkg, 'executable-sourced-script',
                                       f, oct(perm))
                    # ...but executed ones should
                    elif interpreter or mode & 0111 != 0 or \
                            script_regex.search(f):
                        if interpreter:
                            if not interpreter_regex.search(interpreter):
                                printError(pkg, 'wrong-script-interpreter',
                                           f, interpreter)
                        elif not nonexec_file and not \
                                (lib_path_regex.search(f) and
                                 f.endswith('.la')):
                            printError(pkg, 'script-without-shebang', f)

                        if mode & 0111 == 0 and not is_doc:
                            printError(pkg, 'non-executable-script', f,
                                       oct(perm), interpreter)
                        if '\r' in chunk:
                            printError(
                                pkg, 'wrong-script-end-of-line-encoding', f)
                    elif is_doc and not skipdocs_regex.search(f):
                        if '\r' in chunk:
                            printWarning(
                                pkg, 'wrong-file-end-of-line-encoding', f)
                        # We check only doc text files for UTF-8-ness;
                        # checking everything may be slow and can generate
                        # lots of unwanted noise.
                        if use_utf8 and not is_utf8(pkgfile.path):
                            printWarning(pkg, 'file-not-utf8', f)
                    if fsf_license_regex.search(chunk) and \
                            fsf_wrong_address_regex.search(chunk):
                        printError(pkg, 'incorrect-fsf-address', f)

                elif is_doc and chunk and compr_regex.search(f):
                    ff = compr_regex.sub('', f)
                    if not skipdocs_regex.search(ff):
                        # compressed docs, eg. info and man files etc
                        if use_utf8 and not is_utf8(pkgfile.path):
                            printWarning(pkg, 'file-not-utf8', f)

            # normal dir check
            elif stat.S_ISDIR(mode):
                if mode & 01002 == 2: # world writable without sticky bit
                    printError(pkg, 'world-writable', f, oct(perm))
                if perm != 0755:
                    printError(pkg, 'non-standard-dir-perm', f, oct(perm))
                if pkg.name not in filesys_packages and f in STANDARD_DIRS:
                    printError(pkg, 'standard-dir-owned-by-package', f)
                if hidden_file_regex.search(f):
                    printWarning(pkg, 'hidden-file-or-dir', f)


            # symbolic link check
            elif stat.S_ISLNK(mode):

                is_so = sofile_regex.search(f)
                if not devel_pkg and is_so and not link.endswith('.so'):
                    printWarning(pkg, 'devel-file-in-non-devel-package', f)

                res = man_base_regex.search(f)
                if res:
                    man_basenames.add(res.group(1))
                else:
                    res = bin_regex.search(f)
                    if res:
                        exe = res.group(1)
                        if "/" not in exe:
                            bindir_exes.setdefault(exe, [])

                # absolute link
                r = absolute_regex.search(link)
                if r:
                    if not is_so and link not in files and \
                            link not in req_names:
                        is_exception = False
                        for e in dangling_exceptions:
                            if e[0].search(link):
                                is_exception = e[1]
                                break
                        if is_exception:
                            if is_exception not in req_names:
                                printWarning(pkg, 'no-dependency-on',
                                             is_exception)
                        else:
                            printWarning(pkg, 'dangling-symlink', f, link)
                    linktop = r.group(1)
                    r = absolute_regex.search(f)
                    if r:
                        filetop = r.group(1)
                        if filetop == linktop or use_relative_symlinks:
                            printWarning(pkg, 'symlink-should-be-relative',
                                         f, link)
                # relative link
                else:
                    if not is_so:
                        abslink = '%s/%s' % (os.path.dirname(f), link)
                        abslink = os.path.normpath(abslink)
                        if abslink not in files and abslink not in req_names:
                            is_exception = False
                            for e in dangling_exceptions:
                                if e[0].search(link):
                                    is_exception = e[1]
                                    break
                            if is_exception:
                                if is_exception not in req_names:
                                    printWarning(pkg, 'no-dependency-on',
                                                 is_exception)
                            else:
                                printWarning(pkg, 'dangling-relative-symlink',
                                             f, link)
                    pathcomponents = f.split('/')[1:]
                    r = points_regex.search(link)
                    lastpop = None
                    mylink = None

                    while r:
                        mylink = r.group(1)
                        if len(pathcomponents) == 0:
                            printError(pkg, 'symlink-has-too-many-up-segments',
                                       f, link)
                            break
                        else:
                            lastpop = pathcomponents[0]
                            pathcomponents = pathcomponents[1:]
                            r = points_regex.search(mylink)

                    if mylink and lastpop:
                        r = absolute2_regex.search(mylink)
                        linktop = r.group(1)

                        # does the link go up and then down into the same
                        # directory?
                        #if linktop == lastpop:
                        #    printWarning(pkg, 'lengthy-symlink', f, link)

                        # have we reached the root directory?
                        if len(pathcomponents) == 0 and linktop != lastpop \
                                and not use_relative_symlinks:
                            # relative link into other toplevel directory
                            printWarning(pkg, 'symlink-should-be-absolute', f,
                                         link)
                        # check additional segments for mistakes like
                        # `foo/../bar/'
                        for linksegment in mylink.split('/'):
                            if linksegment == '..':
                                printError(
                                    pkg,
                                    'symlink-contains-up-and-down-segments',
                                    f, link)

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

        if debuginfo_package and debuginfo_debugs and not debuginfo_srcs:
            printError(pkg, 'debuginfo-without-sources')

        for exe, paths in bindir_exes.items():
            if len(paths) > 1:
                printWarning(pkg, "duplicate-executable", exe, paths)
            if exe not in man_basenames:
                printWarning(pkg, "no-manual-page-for-binary", exe)

# Create an object to enable the auto registration of the test
check = FilesCheck()

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
%s.''' % ", ".join(standard_users),

'non-standard-gid',
'''A file in this package is owned by a non standard group.
Standard groups are:
%s.''' % ", ".join(standard_groups),

'library-without-ldconfig-postin',
'''This package contains a library and provides no %post scriptlet containing
a call to ldconfig.''',

'postin-without-ldconfig',
'''This package contains a library and its %post scriptlet doesn't call
ldconfig.''',

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
'''This package contains info files and its %postun doesn't call
install-info.''',

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

'non-ghost-in-var-run',
'''A file or directory in the package is located in /var/run. Files installed
in this directory should be marked as %ghost and created at runtime to work
properly in tmpfs /var/run setups.''',

'non-ghost-in-var-lock',
'''A file or directory in the package is located in /var/lock. Files installed
in this directory should be marked as %ghost and created at runtime to work
properly in tmpfs /var/lock setups.''',

'subdir-in-bin',
'''The package contains a subdirectory in /usr/bin. It's not permitted to
create a subdir there. Create it in /usr/lib/ instead.''',

'backup-file-in-package',
'''You have a file whose name looks like one for backup files, usually created
by an editor or resulting from applying unclean (fuzzy, or ones with line
offsets) patches.''',

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
'''The symlink points to a compressed file but doesn't use the same
extension.''',

'setuid-binary',
'''The file is setuid; this may be dangerous, especially if this
file is setuid root. Sometimes file capabilities can be used instead of
setuid bits.''',

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

'cross-directory-hard-link',
'''File is hard linked across directories.  This can cause problems in
installations where the directories are located on different devices.''',

'dangling-symlink',
'''The target of the symbolic link does not exist within this package or its
file based dependencies.  Verify spelling of the link target and that the
target is included in a package in this package's dependency chain.''',

'symlink-should-be-relative',
'''Absolute symlinks are problematic eg. when working with chroot environments.
symlinks(8) is a tool that can be useful for creating/dealing with relative
symlinks at package build time.''',

'dangling-relative-symlink',
'''The target of the symbolic link does not exist within this package or its
file based dependencies.  Verify spelling of the link target and that the
target is included in a package in this package's dependency chain.''',

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

'unexpanded-macro',
'''This package contains a file whose path contains something that looks like
an unexpanded macro; this is often the sign of a misspelling. Please check your
specfile.''',

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
'''This text file contains a shebang, but is meant to be sourced, not
executed.''',

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
in the specfile's %prep section for example using iconv(1).''',

'filename-not-utf8',
'''The character encoding of the name of this file is not UTF-8.
Rename it.''',

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

'debuginfo-without-sources',
'''This debuginfo package appears to contain debug symbols but no source files.
This is often a sign of binaries being unexpectedly stripped too early during
the build, or being compiled without compiler debug flags (which again often
is a sign of distro's default compiler flags ignored which might have security
consequences), or other compiler flags which result in rpmbuild's debuginfo
extraction not working as expected.  Verify that the binaries are not
unexpectedly stripped and that the intended compiler flags are used.''',

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

'rpath-in-buildconfig',
'''This build configuration file contains rpaths which will be introduced into
dependent packages.''',

'python-bytecode-wrong-magic-value',
'''The "magic" ABI version embedded in this python bytecode file isn't equal
to that of the corresponding runtime, which will force the interpreter to
recompile the .py source every time, ignoring the saved bytecode.''',

'python-bytecode-inconsistent-mtime',
'''The timestamp embedded in this python bytecode file isn't equal to the mtime
of the original source file, which will force the interpreter to recompile the
.py source every time, ignoring the saved bytecode.''',

'python-bytecode-without-source',
'''This python bytecode file (.pyo/.pyc) is not accompanied by its original
source file (.py)''',

'duplicate-executable',
'''This executable file exists in more than one standard binary directories.
It can cause problems when dirs in $PATH are reordered.''',

'no-manual-page-for-binary',
'''Each executable in standard binary directories should have a man page.''',

'manual-page-warning',
'''This man page may contain problems that can cause it not to be formatted
as intended.''',

'incorrect-fsf-address',
'''The Free Software Foundation address in this file seems to be outdated or
misspelled.  Ask upstream to update the address, or if this is a license file,
possibly the entire file with a new copy available from the FSF.''',

'gzipped-svg-icon',
'''Not all desktop environments that support SVG icons support them gzipped
(.svgz).  Install the icon as plain uncompressed SVG.''',

'pem-certificate',
'''Shipping a PEM certificate is likely wrong. If used for the default
configuration, this is insecure ( since the certificate is public ). If this
is used for validation, ie a CA certificate store, then this must be kept up
to date due to CA compromise. The only valid reason is for testing purpose,
so ignore this warning if this is the case.''',

'pem-private-key',
'''Private key in a .pem file should not be shipped in a rpm, unless
this is for testing purpose ( ie, run by the test suite ). Shipping it
as part of the example documentation mean that someone will sooner or later
use it and setup a insecure configuration.'''
)

# FilesCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
