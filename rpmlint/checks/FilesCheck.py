#############################################################################
# File          : FilesCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Mon Oct  4 19:32:49 1999
# Purpose       : test various aspects on files: locations, owner, groups,
#                 permission, setuid, setgid...
#############################################################################

from datetime import datetime
import os
from pathlib import Path
import re
import stat

import rpm
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import byte_to_string
from rpmlint.pkg import is_utf8, is_utf8_bytestr

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
    '/var/log',
    '/var/mail',
    '/var/nis',
    '/var/opt',
    '/var/preserve',
    '/var/spool',
    '/var/spool/mail',
    '/var/tmp',
)

compressions = r'\.(gz|z|Z|zip|bz2|lzma|xz|zst)'
sub_bin_regex = re.compile(r'^(/usr)?/s?bin/\S+/')
backup_regex = re.compile(r'(~|\#[^/]+\#|((\.orig|\.rej)(' + compressions + ')?))$')
compr_regex = re.compile(compressions + r'$')
absolute_regex = re.compile(r'^/([^/]+)')
absolute2_regex = re.compile(r'^/?([^/]+)')
points_regex = re.compile(r'^\.\./(.*)')
doc_regex = re.compile(r'^/usr(/share|/X11R6)?/(doc|man|info)/|^/usr/share/gnome/help')
bin_regex = re.compile(r'^/(?:usr/(?:s?bin|games)|s?bin)/(.*)')
includefile_regex = re.compile(r'\.(c|h)(pp|xx)?$', re.IGNORECASE)
develfile_regex = re.compile(r'\.(a|cmxa?|mli?|gir)$')
buildconfigfile_regex = re.compile(r'(\.pc|/bin/.+-config)$')
# room for improvement with catching more -R, but also for false positives...
buildconfig_rpath_regex = re.compile(r'(?:-rpath|Wl,-R)\b')
sofile_regex = re.compile(r'/lib(64)?/(.+/)?lib[^/]+\.so$')
devel_regex = re.compile(r'(.*)-(debug(info|source)?|devel|headers|source|static)$')
debuginfo_package_regex = re.compile(r'-debug(info)?$')
debugsource_package_regex = re.compile(r'-debugsource$')
lib_regex = re.compile(r'/lib(?:64)?/lib[^/]+(?:\.so\.[\d\.]+|-[\d\.]+\.so)$')
ldconfig_regex = re.compile(r'^[^#]*ldconfig', re.MULTILINE)
depmod_regex = re.compile(r'^[^#]*depmod', re.MULTILINE)
install_info_regex = re.compile(r'^[^#]*install-info', re.MULTILINE)
perl_temp_file_regex = re.compile(r'.*perl.*/(\.packlist|perllocal\.pod)$')
scm_regex = re.compile(
    r'/(?:RCS|CVS)/[^/]+$|/\.(?:bzr|cvs|git|hg|svn)ignore$|'
    r',v$|/\.hgtags$|/\.(?:bzr|git|hg|svn)/|/(?:\.arch-ids|{arch})/')
games_path_regex = re.compile(r'^/usr(/lib(64)?)?/games/')
logrotate_regex = re.compile(r'^/etc/logrotate\.d/(.*)')
kernel_modules_regex = re.compile(r'^(?:/usr)/lib/modules/([0-9]+\.[0-9]+\.[0-9]+[^/]*?)/')
kernel_package_regex = re.compile(r'^kernel(22)?(-)?(smp|enterprise|bigmem|secure|BOOT|i686-up-4GB|p3-smp-64GB)?')
normal_zero_length_regex = re.compile(r'^/etc/security/console\.apps/'
                                      r'|/\.nosearch$'
                                      r'|/__init__\.py$'
                                      r'|/py\.typed$'  # https://www.python.org/dev/peps/pep-0561/#packaging-type-information
                                      r'|\.dist-info/REQUESTED$'  # https://www.python.org/dev/peps/pep-0376/#requested
                                      r'|/gem\.build_complete$')
perl_regex = re.compile(r'^/usr/lib/perl5/(?:vendor_perl/)?([0-9]+\.[0-9]+)\.([0-9]+)/')
python_regex = re.compile(r'^/usr/lib(?:64)?/python([.0-9]+)/')
python_bytecode_regex_pep3147 = re.compile(r'^(.*)/__pycache__/(.*?)\.([^.]+)(\.opt-[12])?\.py[oc]$')
python_bytecode_regex = re.compile(r'^(.*)(\.py[oc])$')
log_regex = re.compile(r'^/var/log/[^/]+$')
lib_path_regex = re.compile(r'^(/usr(/X11R6)?)?/lib(64)?')
lib_package_regex = re.compile(r'^(lib|.+-libs)')
hidden_file_regex = re.compile(r'/\.[^/]*$')
manifest_perl_regex = re.compile(r'^/usr/share/doc/perl-.*/MANIFEST(\.SKIP)?$')
shebang_regex = re.compile(br'^#!\s*(\S+)(.*?)$', re.M)
interpreter_regex = re.compile(r'^/(?:usr/)?(?:s?bin|games|libexec(?:/.+)?|(?:lib(?:64)?|share)/.+)/([^/]+)$')
script_regex = re.compile(r'^/((usr/)?s?bin|etc/(rc\.d/init\.d|X11/xinit\.d|cron\.(hourly|daily|monthly|weekly)))/')
sourced_script_regex = re.compile(r'^/etc/(bash_completion\.d|profile\.d)/')
filesys_packages = ['filesystem']  # TODO: make configurable?
quotes_regex = re.compile(r'[\'"]+')
start_certificate_regex = re.compile(r'^-----BEGIN CERTIFICATE-----$')
start_private_key_regex = re.compile(r'^----BEGIN PRIVATE KEY-----$')
non_readable_regexs = (re.compile(r'^/var/log/'),
                       re.compile(r'^/etc/(g?shadow-?|securetty)$'))

man_base_regex = re.compile(r'^/usr(?:/share)?/man(?:/overrides)?/man[^/]+/(.+)\.[1-9n]')

fsf_license_regex = re.compile(br'(GNU((\s+(Library|Lesser|Affero))?(\s+General)?\s+Public|\s+Free\s+Documentation)\s+Licen[cs]e|(GP|FD)L)', re.IGNORECASE)
fsf_wrong_address_regex = re.compile(br'(675\s+Mass\s+Ave|59\s+Temple\s+Place|Franklin\s+Steet|02139|02111-1307)', re.IGNORECASE)

scalable_icon_regex = re.compile(r'^/usr(?:/local)?/share/icons/.*/scalable/')
tcl_regex = re.compile(r'^/usr/lib(64)?/([^/]+/)?pkgIndex\.tcl')

printable_extended_ascii = b'\n\r\t\f\b'
printable_extended_ascii += bytes(range(32, 256))


# See Python sources for a full list of the values here.
# https://github.com/python/cpython/blob/master/Lib/importlib/_bootstrap_external.py
# https://github.com/python/cpython/blob/2.7/Python/import.c
# https://github.com/python/cpython/commit/93602e3af70d3b9f98ae2da654b16b3382b68d50
_python_magic_values = {
    '2.2': [60717],
    '2.3': [62011],
    '2.4': [62061],
    '2.5': [62131],
    '2.6': [62161],
    '2.7': [62211],
    '3.0': [3130],
    '3.1': [3150],
    '3.2': [3180],
    '3.3': [3230],
    '3.4': [3310],
    '3.5': [3350, 3351],  # 3350 for < 3.5.2
    '3.6': [3379],
    '3.7': [3390, 3391, 3392, 3393, 3394],
}


def get_expected_pyc_magic(path, python_default_version):
    """
    .pyc/.pyo files embed a 4-byte magic value identifying which version of
    the python bytecode ABI they are for. Given a path to a .pyc/.pyo file,
    return a (magic ABI values, python version) tuple.  For example,
    '/usr/lib/python3.1/foo.pyc' should return (3151, '3.1').
    The first value will be None if the python version was not resolved
    from the given pathname and the PythonDefaultVersion configuration
    variable is not set, or if we don't know the magic ABI values for the
    python version (no matter from which source the version came from).
    The second value will be None if a python version could not be resolved
    from the given pathname.
    """

    ver_from_path = None
    m = python_regex.search(path)
    if m:
        ver_from_path = m.group(1)

    expected_version = ver_from_path or python_default_version
    expected_magic_values = _python_magic_values.get(expected_version)

    if not expected_magic_values:
        return (None, ver_from_path)

    # In Python 2, if Py_UnicodeFlag is set, Python's import code uses a value
    # one higher, but this is off by default. In Python 3.0 and 3.1 (but no
    # longer in 3.2), it always uses the value one higher:
    if expected_version[:3] in ('3.0', '3.1'):
        expected_magic_values = [x + 1 for x in expected_magic_values]

    return (expected_magic_values, ver_from_path)


def py_demarshal_long(b):
    """
    Counterpart to Python's PyMarshal_ReadLongFromFile, operating on the
    bytes in a string.
    """
    if isinstance(b, str):
        b = map(ord, b)
    return (b[0] + (b[1] << 8) + (b[2] << 16) + (b[3] << 24))


def pyc_magic_from_chunk(chunk):
    """From given chunk (beginning of the file), return Python magic number"""
    return py_demarshal_long(chunk[:4]) & 0xffff


def pyc_mtime_from_chunk(chunk):
    """From given chunk (beginning of the file), return mtime or None

    From Python 3.7, mtime is not always present.

    See https://www.python.org/dev/peps/pep-0552/#specification
    """
    magic = pyc_magic_from_chunk(chunk)
    second = py_demarshal_long(chunk[4:8])
    if magic >= _python_magic_values['3.7'][0]:
        if second == 0:
            return py_demarshal_long(chunk[8:12])
        return None  # No mtime saved, TODO check hashes instead
    return second


def python_bytecode_to_script(path):
    """
    Given a python bytecode path, give the path of the .py file
    (or None if not python bytecode).
    """

    res = python_bytecode_regex_pep3147.search(path)
    if res:
        return res.group(1) + '/' + res.group(2) + '.py'

    res = python_bytecode_regex.search(path)
    if res:
        return res.group(1) + '.py'

    return None


def script_interpreter(chunk):
    res = shebang_regex.search(chunk) if chunk else None
    return (byte_to_string(res.group(1)), byte_to_string(res.group(2)).strip()) \
        if res and res.start() == 0 else (None, '')


class FilesCheck(AbstractCheck):

    man_regex = re.compile(r'/man(?:\d[px]?|n)/')
    info_regex = re.compile(r'(/usr/share|/usr)/info/')

    def __init__(self, config, output):
        super().__init__(config, output)
        self.use_debugsource = self.config.configuration['UseDebugSource']
        self.games_group_regex = re.compile(self.config.configuration['RpmGamesGroup'])
        self.dangling_exceptions = self.config.configuration['DanglingSymlinkExceptions']
        for item in self.dangling_exceptions.values():
            item['path'] = re.compile(item['path'])
        self.module_rpms_ok = self.config.configuration['KernelModuleRPMsOK']
        self.python_default_version = self.config.configuration['PythonDefaultVersion']
        self.perl_version_trick = self.config.configuration['PerlVersionTrick']
        self.skipdocs_regex = re.compile(self.config.configuration['SkipDocsRegexp'], re.IGNORECASE)
        self.meta_package_regex = re.compile(self.config.configuration['MetaPackageRegexp'])
        self.use_relative_symlinks = self.config.configuration['UseRelativeSymlinks']
        self.standard_groups = self.config.configuration['StandardGroups']
        self.standard_users = self.config.configuration['StandardUsers']
        self.disallowed_dirs = self.config.configuration['DisallowedDirs']
        self.compress_ext = self.config.configuration['CompressExtension']
        self.output.error_details.update({
            'non-standard-uid':
            """A file in this package is owned by a non standard user.
            Standard users are:
            %s.""" % ', '.join(self.standard_users),

            'non-standard-gid':
            """A file in this package is owned by a non standard group.
            Standard groups are:
            %s.""" % ', '.join(self.standard_groups),

            'manpage-not-compressed':
                """This manual page is not compressed with the %s compression method
                (does not have the %s extension). If the compression does not happen
                automatically when the package is rebuilt, make sure that you have the
                appropriate rpm helper and/or config packages for your target distribution
                installed and try rebuilding again; if it still does not happen automatically,
                you can compress this file in the %%install section of the spec file."""
                % (self.compress_ext, self.compress_ext),

            'infopage-not-compressed':
                """This info page is not compressed with the %s compression method
                (does not have the %s extension). If the compression does not happen
                automatically when the package is rebuilt, make sure that you have the
                appropriate rpm helper and/or config packages for your target distribution
                installed and try rebuilding again; if it still does not happen automatically,
                you can compress this file in the %%install section of the spec file."""
                % (self.compress_ext, self.compress_ext),
        })
        for i in self.disallowed_dirs:
            self.output.error_details.update({'dir-or-file-in-%s' % '-'.join(i.split('/')[1:]):
                                             """A file in the package is located in %s. It's not permitted
        for packages to install files in this directory.""" % i})

    def peek(self, filename, pkg, length=1024):
        """
        Peek into a file, return a chunk from its beginning and a flag if it
        seems to be a text file.
        """
        chunk = None
        try:
            with open(filename, 'rb') as fobj:
                chunk = fobj.read(length)
        except IOError as e:  # eg. https://bugzilla.redhat.com/209876
            self.output.add_info('W', pkg, 'read-error', e)
            return (chunk, False)

        if b'\0' in chunk:
            return (chunk, False)

        if not chunk:  # Empty files are considered text
            return (chunk, True)

        fl = filename.lower()

        # PDF's are binary but often detected as text by the algorithm below
        if fl.endswith('.pdf') and chunk.startswith(b'%PDF-'):
            return (chunk, False)
        # Ditto RDoc RI files
        if fl.endswith('.ri') and '/ri/' in fl:
            return (chunk, False)
        # And Sphinx inventory files
        if fl.endswith('.inv') and chunk.startswith(b'# Sphinx inventory'):
            return (chunk, False)

        # Binary if control chars are > 30% of the string
        control_chars = chunk.translate(None, printable_extended_ascii)
        nontext_ratio = float(len(control_chars)) / float(len(chunk))
        istext = nontext_ratio <= 0.30

        return (chunk, istext)

    def check(self, pkg):

        for filename in pkg.header[rpm.RPMTAG_FILENAMES] or ():
            if not is_utf8_bytestr(filename):
                self.output.add_info('E', pkg, 'filename-not-utf8', byte_to_string(filename))

        # Rest of the checks are for binary packages only
        if pkg.is_source:
            return

        files = pkg.files

        # Check if the package is a development package
        devel_pkg = devel_regex.search(pkg.name)

        if not devel_pkg:
            for p in pkg.provides:
                if devel_regex.search(p[0]):
                    devel_pkg = True
                    break

        config_files = pkg.config_files
        ghost_files = pkg.ghost_files
        req_names = pkg.req_names
        lib_package = lib_package_regex.search(pkg.name)
        is_kernel_package = kernel_package_regex.search(pkg.name)
        debuginfo_package = debuginfo_package_regex.search(pkg.name)
        debugsource_package = debugsource_package_regex.search(pkg.name)

        # report these errors only once
        perl_dep_error = False
        python_dep_error = False
        lib_file = False
        non_lib_file = None
        log_files = []
        logrotate_file = False
        debuginfo_srcs = False
        debuginfo_debugs = False

        if not lib_package and not pkg.doc_files:
            self.output.add_info('W', pkg, 'no-documentation')

        if files:
            if self.meta_package_regex.search(pkg.name):
                self.output.add_info('W', pkg, 'file-in-meta-package')
        elif debuginfo_package or debugsource_package:
            self.output.add_info('E', pkg, 'empty-debuginfo-package')

        # Prefetch scriptlets, strip quotes from them (#169)
        postin = pkg[rpm.RPMTAG_POSTIN] or \
            pkg.scriptprog(rpm.RPMTAG_POSTINPROG)
        if postin:
            postin = quotes_regex.sub('', postin)
        postun = pkg[rpm.RPMTAG_POSTUN] or \
            pkg.scriptprog(rpm.RPMTAG_POSTUNPROG)
        if postun:
            postun = quotes_regex.sub('', postun)

        # Unique (rdev, inode) combinations
        hardlinks = {}

        # All executable files from standard bin dirs (basename => [paths])
        # Hack: basenames with empty paths links are symlinks (not subject
        # to duplicate binary check, but yes for man page existence check)
        bindir_exes = {}

        # All man page 'base' names (without section etc extensions)
        man_basenames = set()

        for f, pkgfile in files.items():
            fpath = Path(f)
            mode = pkgfile.mode
            user = pkgfile.user
            group = pkgfile.group
            link = pkgfile.linkto
            size = pkgfile.size
            rdev = pkgfile.rdev
            inode = pkgfile.inode
            is_doc = f in pkg.doc_files
            nonexec_file = False

            self._check_manpage_compressed(pkg, f)
            self._check_infopage_compressed(pkg, f)

            for match in self.macro_regex.findall(f):
                self.output.add_info('W', pkg, 'unexpanded-macro', f, match)
            if user not in self.standard_users:
                self.output.add_info('W', pkg, 'non-standard-uid', f, user)
            if group not in self.standard_groups:
                self.output.add_info('W', pkg, 'non-standard-gid', f, group)

            if not self.module_rpms_ok and kernel_modules_regex.search(f) and not \
                    is_kernel_package:
                self.output.add_info('E', pkg, 'kernel-modules-not-in-kernel-packages', f)

            for i in self.disallowed_dirs:
                if f.startswith(i):
                    self.output.add_info('E', pkg, 'dir-or-file-in-%s' %
                                         '-'.join(i.split('/')[1:]), f)

            if f.startswith('/run/'):
                if f not in ghost_files:
                    self.output.add_info('W', pkg, 'non-ghost-in-run', f)
            elif f.startswith('/etc/systemd/system/'):
                self.output.add_info('W', pkg, 'systemd-unit-in-etc', f)
            elif f.startswith('/etc/udev/rules.d/'):
                self.output.add_info('W', pkg, 'udev-rule-in-etc', f)
            elif f.startswith('/etc/tmpfiles.d/'):
                self.output.add_info('W', pkg, 'tmpfiles-conf-in-etc', f)
            elif sub_bin_regex.search(f):
                self.output.add_info('E', pkg, 'subdir-in-bin', f)
            elif '/site_perl/' in f:
                self.output.add_info('W', pkg, 'siteperl-in-perl-module', f)

            if backup_regex.search(f):
                self.output.add_info('E', pkg, 'backup-file-in-package', f)
            elif scm_regex.search(f):
                self.output.add_info('E', pkg, 'version-control-internal-file', f)
            elif f.endswith('/.htaccess'):
                self.output.add_info('E', pkg, 'htaccess-file', f)
            elif hidden_file_regex.search(f) and not f.startswith('/etc/skel/') and not f.endswith('/.build-id'):
                self.output.add_info('W', pkg, 'hidden-file-or-dir', f)
            elif manifest_perl_regex.search(f):
                self.output.add_info('W', pkg, 'manifest-in-perl-module', f)
            elif f == '/usr/info/dir' or f == '/usr/share/info/dir':
                self.output.add_info('E', pkg, 'info-dir-file', f)
            if fpath.name == 'Makefile.am' and str(fpath.with_suffix('.in')) in files and is_doc:
                self.output.add_info('W', pkg, 'makefile-junk', f)

            res = logrotate_regex.search(f)
            if res:
                logrotate_file = True
                if res.group(1) != pkg.name:
                    self.output.add_info('E', pkg, 'incoherent-logrotate-file', f)

            deps = [x[0] for x in pkg.requires + pkg.recommends + pkg.suggests]
            if res and not ('logrotate' in deps) and pkg.name != 'logrotate':
                self.output.add_info('E', pkg, 'missing-dependency-to-logrotate', 'for logrotate script', f)
            if f.startswith('/etc/cron.') \
               and not ('crontabs' in deps) and pkg.name != 'crontabs':
                self.output.add_info('E', pkg, 'missing-dependency-to-crontabs', 'for cron script', f)
            if f.startswith('/etc/xinet.d/') \
               and not ('xinetd' in deps) and pkg.name != 'xinetd':
                self.output.add_info('E', pkg, 'missing-dependency-to-xinetd', 'for xinet.d script', f)

            if link != '':
                ext = compr_regex.search(link)
                if ext:
                    if not re.compile(r'\.%s$' % ext.group(1)).search(f):
                        self.output.add_info('E', pkg, 'compressed-symlink-with-wrong-ext',
                                             f, link)

            perm = mode & 0o7777
            mode_is_exec = mode & 0o111

            if log_regex.search(f):
                log_files.append(f)

            # Hardlink check
            for hardlink in hardlinks.get((rdev, inode), ()):
                if Path(hardlink).parent != Path(f).parent:
                    self.output.add_info('W', pkg, 'cross-directory-hard-link', f, hardlink)
            hardlinks.setdefault((rdev, inode), []).append(f)

            # normal file check
            if stat.S_ISREG(mode):

                # set[ug]id bit check
                if stat.S_ISGID & mode or stat.S_ISUID & mode:
                    if stat.S_ISUID & mode:
                        self.output.add_info('E', pkg, 'setuid-binary', f, user, '%o' % perm)
                    if stat.S_ISGID & mode:
                        if not (group == 'games' and
                                (games_path_regex.search(f) or
                                 self.games_group_regex.search(
                                    pkg[rpm.RPMTAG_GROUP]))):
                            self.output.add_info('E', pkg, 'setgid-binary', f, group,
                                                 '%o' % perm)
                    if mode & 0o777 != 0o755:
                        self.output.add_info('E', pkg, 'non-standard-executable-perm', f,
                                             '%o' % perm)

                if not devel_pkg:
                    if lib_path_regex.search(f):
                        lib_file = True
                    elif not is_doc:
                        non_lib_file = f

                if log_regex.search(f):
                    nonexec_file = True
                    if user != 'root':
                        self.output.add_info('E', pkg, 'non-root-user-log-file', f, user)
                    if group != 'root':
                        self.output.add_info('E', pkg, 'non-root-group-log-file', f, group)
                    if f not in ghost_files:
                        self.output.add_info('E', pkg, 'non-ghost-file', f)

                chunk = None
                istext = False
                res = None
                try:
                    res = os.access(pkgfile.path, os.R_OK)
                except UnicodeError as e:  # e.g. non-ASCII, C locale, python 3
                    self.output.add_info('W', pkg, 'inaccessible-filename', f, e)
                else:
                    if res:
                        (chunk, istext) = self.peek(pkgfile.path, pkg)

                (interpreter, interpreter_args) = script_interpreter(chunk)

                if doc_regex.search(f):
                    if not interpreter:
                        nonexec_file = True
                    if not is_doc:
                        self.output.add_info('E', pkg, 'not-listed-as-documentation', f)

                if devel_pkg and f.endswith('.typelib'):
                    self.output.add_info('E', pkg, 'non-devel-file-in-devel-package', f)

                # check ldconfig call in %post and %postun
                if lib_regex.search(f):
                    if devel_pkg and not (sofile_regex.search(f) and stat.S_ISLNK(mode)):
                        self.output.add_info('E', pkg, 'non-devel-file-in-devel-package', f)
                    if not postin:
                        self.output.add_info('E', pkg, 'library-without-ldconfig-postin', f)
                    else:
                        if not ldconfig_regex.search(postin):
                            self.output.add_info('E', pkg, 'postin-without-ldconfig', f)

                    if not postun:
                        self.output.add_info('E', pkg, 'library-without-ldconfig-postun', f)
                    else:
                        if not ldconfig_regex.search(postun):
                            self.output.add_info('E', pkg, 'postun-without-ldconfig', f)

                # check depmod call in %post and %postun
                res = not is_kernel_package and kernel_modules_regex.search(f)
                if res:
                    kernel_version = res.group(1)
                    kernel_version_regex = re.compile(
                        r'\bdepmod\s+-a.*F\s+/boot/System\.map-' +
                        re.escape(kernel_version) + r'\b.*\b' +
                        re.escape(kernel_version) + r'\b',
                        re.MULTILINE | re.DOTALL)

                    if not postin or not depmod_regex.search(postin):
                        self.output.add_info('E', pkg, 'module-without-depmod-postin', f)
                    # check that we run depmod on the right kernel
                    elif not kernel_version_regex.search(postin):
                        self.output.add_info('E', pkg, 'postin-with-wrong-depmod', f)

                    if not postun or not depmod_regex.search(postun):
                        self.output.add_info('E', pkg, 'module-without-depmod-postun', f)
                    # check that we run depmod on the right kernel
                    elif not kernel_version_regex.search(postun):
                        self.output.add_info('E', pkg, 'postun-with-wrong-depmod', f)

                # check install-info call in %post and %postun
                if f.startswith('/usr/share/info/'):
                    if not postin:
                        self.output.add_info('E', pkg,
                                             'info-files-without-install-info-postin', f)
                    elif not install_info_regex.search(postin):
                        self.output.add_info('E', pkg, 'postin-without-install-info', f)

                    preun = pkg[rpm.RPMTAG_PREUN] or \
                        pkg.scriptprog(rpm.RPMTAG_PREUNPROG)
                    if not postun and not preun:
                        self.output.add_info('E', pkg,
                                             'info-files-without-install-info-postun', f)
                    elif not ((postun and install_info_regex.search(postun)) or
                              (preun and install_info_regex.search(preun))):
                        self.output.add_info('E', pkg, 'postin-without-install-info', f)

                # check perl temp file
                if perl_temp_file_regex.search(f):
                    self.output.add_info('W', pkg, 'perl-temp-file', f)

                is_buildconfig = istext and buildconfigfile_regex.search(f)

                # check rpaths in buildconfig files
                if is_buildconfig:
                    ln = pkg.grep(buildconfig_rpath_regex, f)
                    if ln:
                        self.output.add_info('E', pkg, 'rpath-in-buildconfig', f, 'lines', ln)

                res = bin_regex.search(f)
                if res:
                    if not mode_is_exec:
                        self.output.add_info('W', pkg, 'non-executable-in-bin', f,
                                             '%o' % perm)
                    else:
                        exe = res.group(1)
                        if '/' not in exe:
                            bindir_exes.setdefault(exe, []).append(f)

                if (not devel_pkg and not is_doc and
                    (is_buildconfig or includefile_regex.search(f) or
                     develfile_regex.search(f))):
                    self.output.add_info('W', pkg, 'devel-file-in-non-devel-package', f)
                if mode & 0o444 != 0o444 and perm & 0o7000 == 0:
                    ok_nonreadable = False
                    for regex in non_readable_regexs:
                        if regex.search(f):
                            ok_nonreadable = True
                            break
                    if not ok_nonreadable:
                        self.output.add_info('E', pkg, 'non-readable', f, '%o' % perm)
                if size == 0 and not normal_zero_length_regex.search(f) and \
                        f not in ghost_files:
                    self.output.add_info('E', pkg, 'zero-length', f)

                if mode & stat.S_IWOTH:
                    self.output.add_info('E', pkg, 'world-writable', f, '%o' % perm)

                if not perl_dep_error:
                    res = perl_regex.search(f)
                    if res:
                        if self.perl_version_trick:
                            vers = res.group(1) + '.' + res.group(2)
                        else:
                            vers = res.group(1) + res.group(2)
                        if not (pkg.check_versioned_dep('perl-base', vers) or
                                pkg.check_versioned_dep('perl', vers)):
                            self.output.add_info('E', pkg, 'no-dependency-on',
                                                 'perl-base', vers)
                            perl_dep_error = True

                if not python_dep_error:
                    res = python_regex.search(f)
                    if (res and not
                            any((pkg.check_versioned_dep(dep, res.group(1))
                                for dep in (
                                    'python', 'python-base', 'python(abi)')))):
                        self.output.add_info('E', pkg, 'no-dependency-on', 'python-base',
                                             res.group(1))
                        python_dep_error = True

                source_file = python_bytecode_to_script(f)
                if source_file:
                    if source_file in files:
                        if chunk:
                            # Verify that the magic ABI value embedded in the
                            # .pyc header is correct
                            found_magic = pyc_magic_from_chunk(chunk)
                            exp_magic, exp_version = get_expected_pyc_magic(f, self.python_default_version)
                            if exp_magic and found_magic not in exp_magic:
                                found_version = 'unknown'
                                for (pv, pm) in _python_magic_values.items():
                                    if found_magic in pm:
                                        found_version = pv
                                        break
                                # If expected version was from the file path,
                                # issue # an error, otherwise a warning.
                                msg = (pkg,
                                       'python-bytecode-wrong-magic-value',
                                       f, 'expected %s (%s), found %d (%s)' %
                                       (' or '.join(map(str, exp_magic)),
                                        exp_version or self.python_default_version,
                                        found_magic, found_version))
                                if exp_version is not None:
                                    self.output.add_info('E', *msg)
                                else:
                                    self.output.add_info('W', *msg)

                            # Verify that the timestamp embedded in the .pyc
                            # header matches the mtime of the .py file:
                            pyc_timestamp = pyc_mtime_from_chunk(chunk)
                            # If it's a symlink, check target file mtime.
                            srcfile = pkg.readlink(files[source_file])
                            if not srcfile:
                                self.output.add_info('W', pkg, 'python-bytecode-without-source', f)
                            elif (pyc_timestamp is not None and
                                  pyc_timestamp != srcfile.mtime):
                                cts = datetime.fromtimestamp(
                                    pyc_timestamp).isoformat()
                                sts = datetime.fromtimestamp(
                                    srcfile.mtime).isoformat()
                                self.output.add_info('E',
                                                     pkg, 'python-bytecode-inconsistent-mtime',
                                                     f, cts, srcfile.name, sts)
                    else:
                        self.output.add_info('W', pkg, 'python-bytecode-without-source', f)

                # normal executable check
                if mode & stat.S_IXUSR and perm != 0o755:
                    self.output.add_info('E', pkg, 'non-standard-executable-perm',
                                         f, '%o' % perm)
                if mode_is_exec:
                    if f in config_files:
                        self.output.add_info('E', pkg, 'executable-marked-as-config-file', f)
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
                        self.output.add_info('W', pkg, 'spurious-executable-perm', f)
                elif f.startswith('/etc/') and f not in config_files and \
                        f not in ghost_files:
                    self.output.add_info('W', pkg, 'non-conffile-in-etc', f)

                if pkg.arch == 'noarch' and f.startswith('/usr/lib64/python'):
                    self.output.add_info('E', pkg, 'noarch-python-in-64bit-path', f)

                if debuginfo_package:
                    if f.endswith('.debug'):
                        debuginfo_debugs = True
                    else:
                        debuginfo_srcs = True

                if f.endswith('.svgz') and f[0:-1] not in files \
                        and scalable_icon_regex.search(f):
                    self.output.add_info('W', pkg, 'gzipped-svg-icon', f)

                if f.endswith('.pem') and f not in ghost_files:
                    if pkg.grep(start_certificate_regex, f):
                        self.output.add_info('W', pkg, 'pem-certificate', f)
                    if pkg.grep(start_private_key_regex, f):
                        self.output.add_info('E', pkg, 'pem-private-key', f)

                if tcl_regex.search(f):
                    self.output.add_info('E', pkg, 'tcl-extension-file', f)

                # text file checks
                if istext:
                    # ignore perl module shebang -- TODO: disputed...
                    if f.endswith('.pm'):
                        interpreter = None
                    # sourced scripts should not be executable
                    if sourced_script_regex.search(f):
                        if interpreter:
                            self.output.add_info('E', pkg,
                                                 'sourced-script-with-shebang', f,
                                                 interpreter, interpreter_args)
                        if mode_is_exec:
                            self.output.add_info('E', pkg, 'executable-sourced-script',
                                                 f, '%o' % perm)
                    # ...but executed ones should
                    elif interpreter or mode_is_exec or script_regex.search(f):
                        if interpreter:
                            res = interpreter_regex.search(interpreter)
                            if (mode_is_exec or script_regex.search(f)):
                                if res and res.group(1) == 'env':
                                    self.output.add_info('E', pkg, 'env-script-interpreter',
                                                         f, interpreter,
                                                         interpreter_args)
                                elif not res:
                                    self.output.add_info('E', pkg, 'wrong-script-interpreter',
                                                         f, interpreter,
                                                         interpreter_args)
                        elif not nonexec_file and not \
                                (lib_path_regex.search(f) and
                                 f.endswith('.la')):
                            self.output.add_info('E', pkg, 'script-without-shebang', f)

                        if not mode_is_exec and not is_doc and \
                                interpreter and interpreter.startswith('/'):
                            self.output.add_info('E', pkg, 'non-executable-script', f,
                                                 '%o' % perm, interpreter,
                                                 interpreter_args)
                        if b'\r' in chunk:
                            self.output.add_info('E', pkg, 'wrong-script-end-of-line-encoding', f)
                    elif is_doc and not self.skipdocs_regex.search(f):
                        if b'\r' in chunk:
                            self.output.add_info('W', pkg, 'wrong-file-end-of-line-encoding', f)
                        # We check only doc text files for UTF-8-ness;
                        # checking everything may be slow and can generate
                        # lots of unwanted noise.
                        if not is_utf8(pkgfile.path):
                            self.output.add_info('W', pkg, 'file-not-utf8', f)
                    if fsf_license_regex.search(chunk) and \
                            fsf_wrong_address_regex.search(chunk):
                        self.output.add_info('E', pkg, 'incorrect-fsf-address', f)

                elif is_doc and chunk and compr_regex.search(f):
                    ff = compr_regex.sub('', f)
                    if not self.skipdocs_regex.search(ff):
                        # compressed docs, eg. info and man files etc
                        if not is_utf8(pkgfile.path):
                            self.output.add_info('W', pkg, 'file-not-utf8', f)

            # normal dir check
            elif stat.S_ISDIR(mode):
                if mode & 0o1002 == 2:  # world writable w/o sticky bit
                    self.output.add_info('E', pkg, 'world-writable', f, '%o' % perm)
                if perm != 0o755:
                    self.output.add_info('E', pkg, 'non-standard-dir-perm', f, '%o' % perm)
                if pkg.name not in filesys_packages and f in STANDARD_DIRS:
                    self.output.add_info('E', pkg, 'standard-dir-owned-by-package', f)
                if hidden_file_regex.search(f) and not f.endswith('/.build-id'):
                    self.output.add_info('W', pkg, 'hidden-file-or-dir', f)

            # symbolic link check
            elif stat.S_ISLNK(mode):

                is_so = sofile_regex.search(f)
                if not devel_pkg and is_so and not link.endswith('.so'):
                    self.output.add_info('W', pkg, 'devel-file-in-non-devel-package', f)

                res = man_base_regex.search(f)
                if res:
                    man_basenames.add(res.group(1))
                else:
                    res = bin_regex.search(f)
                    if res:
                        exe = res.group(1)
                        if '/' not in exe:
                            bindir_exes.setdefault(exe, [])

                # absolute link
                r = absolute_regex.search(link)
                if r:
                    if not is_so and link not in files and \
                            link not in req_names:
                        is_exception = False
                        for e in self.dangling_exceptions.values():
                            if e['path'].search(link):
                                is_exception = e['name']
                                break
                        if is_exception:
                            if is_exception not in req_names:
                                self.output.add_info('W', pkg, 'no-dependency-on',
                                                     is_exception)
                        else:
                            self.output.add_info('W', pkg, 'dangling-symlink', f, link)
                    linktop = r.group(1)
                    r = absolute_regex.search(f)
                    if r:
                        filetop = r.group(1)
                        if filetop == linktop or self.use_relative_symlinks:
                            self.output.add_info('W', pkg, 'symlink-should-be-relative',
                                                 f, link)
                # relative link
                else:
                    if not is_so:
                        abslink = '%s/%s' % (Path(f).parent, link)
                        abslink = os.path.normpath(abslink)
                        if abslink not in files and abslink not in req_names:
                            is_exception = False
                            for e in self.dangling_exceptions.values():
                                if e['path'].search(link):
                                    is_exception = e['name']
                                    break
                            if is_exception:
                                if is_exception not in req_names:
                                    self.output.add_info('W', pkg, 'no-dependency-on',
                                                         is_exception)
                            else:
                                self.output.add_info('W', pkg, 'dangling-relative-symlink',
                                                     f, link)
                    pathcomponents = f.split('/')[1:]
                    r = points_regex.search(link)
                    lastpop = None
                    mylink = None

                    while r:
                        mylink = r.group(1)
                        if len(pathcomponents) == 0:
                            self.output.add_info('E', pkg, 'symlink-has-too-many-up-segments',
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
                        # if linktop == lastpop:
                        #    self.output.add_info('W', pkg, 'lengthy-symlink', f, link)

                        # have we reached the root directory?
                        if len(pathcomponents) == 0 and linktop != lastpop \
                                and not self.use_relative_symlinks:
                            # relative link into other toplevel directory
                            self.output.add_info('W', pkg, 'symlink-should-be-absolute', f,
                                                 link)
                        # check additional segments for mistakes like
                        # `foo/../bar/'
                        for linksegment in mylink.split('/'):
                            if linksegment == '..':
                                self.output.add_info('E',
                                                     pkg,
                                                     'symlink-contains-up-and-down-segments',
                                                     f, link)

            if f.startswith('/etc/cron.d/'):
                if stat.S_ISLNK(mode):
                    self.output.add_info('E', pkg, 'symlink-crontab-file', f)

                if mode_is_exec:
                    self.output.add_info('E', pkg, 'executable-crontab-file', f)

                if stat.S_IWGRP & mode or stat.S_IWOTH & mode:
                    self.output.add_info('E', pkg, 'non-owner-writeable-only-crontab-file', f)

        if len(log_files) and not logrotate_file:
            self.output.add_info('W', pkg, 'log-files-without-logrotate', sorted(log_files))

        if lib_package and lib_file and non_lib_file:
            self.output.add_info('E', pkg, 'outside-libdir-files', non_lib_file)

        if not self.use_debugsource and debuginfo_package and debuginfo_debugs and not debuginfo_srcs:
            self.output.add_info('E', pkg, 'debuginfo-without-sources')

        for exe, paths in bindir_exes.items():
            if len(paths) > 1:
                self.output.add_info('W', pkg, 'duplicate-executable', exe, paths)
            if exe not in man_basenames:
                self.output.add_info('W', pkg, 'no-manual-page-for-binary', exe)

    def _check_manpage_compressed(self, pkg, fname):
        """
        Check if the the manual page is compressed with the compression method
        stated in the rpmlint configuration (CompressExtension option).

        Print a warning if it's not compressed.
        """
        if self.compress_ext and self.man_regex.search(fname):
            if not fname.endswith(self.compress_ext):
                self.output.add_info('W', pkg, 'manpage-not-compressed',
                                     self.compress_ext, fname)

    def _check_infopage_compressed(self, pkg, fname):
        """
        Check if the the info page is compressed with the compression method
        stated in the rpmlint configuration (CompressExtension option).

        Print a warning if it's not compressed.
        """
        if self.compress_ext and self.info_regex.search(fname) and \
                not fname.endswith('/info/dir'):
            if not fname.endswith(self.compress_ext):
                self.output.add_info('W', pkg, 'infopage-not-compressed',
                                     self.compress_ext, fname)
