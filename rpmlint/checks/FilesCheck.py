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
devel_regex = re.compile(r'(.*)-(debug(info|source)?|devel|headers|source|static|prof)$')
debuginfo_package_regex = re.compile(r'-debug(info)?$')
debugsource_package_regex = re.compile(r'-debugsource$')
lib_regex = re.compile(r'/lib(?:64)?/lib[A-Za-z0-9](?:(?:|[\w\-\.]*[A-Za-z0-9])\.so\.[\w+\.]+|\w*-\d(?:|[\w\-\.]*[A-Za-z0-9])\.so)$')  # see commit log for detail
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

man_base_regex = re.compile(r'^/usr(?:/share)?/man(?:/overrides)?/man(?P<category>[^/]+)/(?P<filename>((?P<binary>[^.]+)\..+))')

fsf_license_regex = re.compile(br'(GNU((\s+(Library|Lesser|Affero))?(\s+General)?\s+Public|\s+Free\s+Documentation)\s+Licen[cs]e|(GP|FD)L)', re.IGNORECASE)
fsf_wrong_address_regex = re.compile(br'(675\s+Mass\s+Ave|59\s+Temple\s+Place|02139)', re.IGNORECASE)

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


def find_perm_in_tmpfiles(pkg, fname):
    """
    Look for file path in all tmpdfiles.d file declared in this pkg and return
    the permission column.
    """

    tmpd = []
    perms = '0644'
    user = 'root'
    group = 'root'
    fname = os.path.realpath(fname)

    for k, v in pkg.files.items():
        if 'tmpfiles.d' not in k:
            continue
        if not os.path.exists(v.path):
            continue
        with open(v.path) as f:
            tmpd += f.readlines()

    for line in tmpd:
        if f' {fname} ' not in line:
            continue
        try:
            _t, _p, perms, user, group, *_rest = line.split()
        except IndexError:
            continue

    return perms, user, group


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
        except OSError as e:  # eg. https://bugzilla.redhat.com/209876
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
        self._check_utf8(pkg)

        # Rest of the checks are for binary packages only
        if pkg.is_source:
            return

        self.devel_pkg = False
        self.deps = pkg.requires + pkg.prereq
        self.config_files = pkg.config_files
        self.ghost_files = pkg.ghost_files
        self.req_names = pkg.req_names
        self.lib_package = lib_package_regex.search(pkg.name)
        self.is_kernel_package = kernel_package_regex.search(pkg.name)
        self.debuginfo_package = debuginfo_package_regex.search(pkg.name)
        self.debugsource_package = debugsource_package_regex.search(pkg.name)

        # report these errors only once
        self.perl_dep_error = False
        self.python_dep_error = False
        self.lib_file = False
        self.non_lib_file = None
        self.log_files = []
        self.logrotate_file = False
        self.debuginfo_srcs = False
        self.debuginfo_debugs = False

        # Prefetch scriptlets, strip quotes from them (#169)
        self.postin = pkg[rpm.RPMTAG_POSTIN] or \
            pkg.scriptprog(rpm.RPMTAG_POSTINPROG)
        if self.postin:
            self.postin = quotes_regex.sub('', self.postin)
        self.postun = pkg[rpm.RPMTAG_POSTUN] or \
            pkg.scriptprog(rpm.RPMTAG_POSTUNPROG)
        if self.postun:
            self.postun = quotes_regex.sub('', self.postun)

        # Unique (rdev, inode) combinations
        self.hardlinks = {}

        # All executable files from standard bin dirs (basename => [paths])
        # Hack: basenames with empty paths links are symlinks (not subject
        # to duplicate binary check, but yes for man page existence check)
        self.bindir_exes = {}

        # All man page 'base' names (without section etc extensions)
        self.man_basenames = set()

        self._check_devel(pkg)
        self._check_nodoc(pkg)
        self._check_meta_package(pkg)
        self._check_empty_debuginfo(pkg)

        # Iterate over all pkg.files
        self._check_files(pkg)

        self._check_log_files_without_logrotate(pkg)
        self._check_outside_libdir_files(pkg)
        self._check_debuginfo_without_sources(pkg)
        self._check_bindir_exes(pkg)

    def _check_utf8(self, pkg):
        for filename in pkg.header[rpm.RPMTAG_FILENAMES] or ():
            if not is_utf8_bytestr(filename):
                self.output.add_info('E', pkg, 'filename-not-utf8', byte_to_string(filename))

    def _check_devel(self, pkg):
        # Check if the package is a development package
        self.devel_pkg = devel_regex.search(pkg.name)

        if not self.devel_pkg:
            for p in pkg.provides:
                if devel_regex.search(p[0]):
                    self.devel_pkg = True
                    break

    def _check_nodoc(self, pkg):
        if not self.lib_package and not pkg.doc_files:
            self.output.add_info('W', pkg, 'no-documentation')

    def _check_meta_package(self, pkg):
        if pkg.files and self.meta_package_regex.search(pkg.name):
            self.output.add_info('W', pkg, 'file-in-meta-package')

    def _check_empty_debuginfo(self, pkg):
        debuginfo = self.debuginfo_package or self.debugsource_package
        if not pkg.files and debuginfo:
            self.output.add_info('E', pkg, 'empty-debuginfo-package')

    def _check_log_files_without_logrotate(self, pkg):
        if len(self.log_files) and not self.logrotate_file:
            self.output.add_info('W', pkg, 'log-files-without-logrotate', sorted(self.log_files))

    def _check_outside_libdir_files(self, pkg):
        if self.lib_package and self.lib_file and self.non_lib_file:
            self.output.add_info('E', pkg, 'outside-libdir-files', self.non_lib_file)

    def _check_debuginfo_without_sources(self, pkg):
        if not self.use_debugsource and self.debuginfo_package and self.debuginfo_debugs and not self.debuginfo_srcs:
            self.output.add_info('E', pkg, 'debuginfo-without-sources')

    def _check_bindir_exes(self, pkg):
        for exe, paths in self.bindir_exes.items():
            if len(paths) > 1:
                self.output.add_info('W', pkg, 'duplicate-executable', exe, paths)
            if exe not in self.man_basenames:
                self.output.add_info('W', pkg, 'no-manual-page-for-binary', exe)

    def _check_files(self, pkg):
        for f, pkgfile in pkg.files.items():
            self._check_file(pkg, f, pkgfile)

    def _check_file(self, pkg, fname, pkgfile):
        if log_regex.search(fname):
            self.log_files.append(fname)

        self._check_file_manpage(pkg, fname)
        self._check_file_infopage_compressed(pkg, fname)
        self._check_file_unexpandaed_macro(pkg, fname)
        self._check_file_non_standard_uid(pkg, fname, pkgfile)
        self._check_file_non_standard_gid(pkg, fname, pkgfile)
        self._check_file_kernel_modules(pkg, fname)
        self._check_file_dir_or_file(pkg, fname)
        self._check_file_non_ghost_in_run(pkg, fname)
        self._check_file_systemd_unit_in_etc(pkg, fname)
        self._check_file_udev_rule_in_etc(pkg, fname)
        self._check_file_tmpfiles_conf_in_etc(pkg, fname)
        self._check_file_subdir_in_bin(pkg, fname)
        self._check_file_siteperl_in_perl_module(pkg, fname)
        self._check_file_backup_file_in_package(pkg, fname)
        self._check_file_version_control_internal_file(pkg, fname)
        self._check_file_htaccess_file(pkg, fname)
        self._check_file_hidden_file_or_dir(pkg, fname)
        self._check_file_manifest_in_perl_module(pkg, fname)
        self._check_file_info_dir_file(pkg, fname)
        self._check_file_makefile_junk(pkg, fname)
        self._check_file_logrotate(pkg, fname)
        self._check_file_crontab(pkg, fname)
        self._check_file_xinetd(pkg, fname)
        self._check_file_compressed_symlink(pkg, fname, pkgfile)
        self._check_file_hardlink(pkg, fname, pkgfile)

        # normal file check
        self._check_file_normal_file(pkg, fname, pkgfile)
        # normal dir check
        self._check_file_dir(pkg, fname, pkgfile)
        # symbolic link check
        self._check_file_link(pkg, fname, pkgfile)

        self._check_file_crond(pkg, fname, pkgfile)

        # files with all permissions bits as zero
        # https://github.com/rpm-software-management/rpmlint/issues/878
        self._check_file_zero_perms(pkg, fname, pkgfile)

    def _check_file_manpage(self, pkg, fname):
        """
        Check if the the manual page is compressed with the compression method
        stated in the rpmlint configuration (CompressExtension option).
        Check also for a correct manual page location and if not included in a subfolder.

        Print a warning if it's not compressed.
        """
        if stat.S_ISDIR(pkg.files[fname].mode):
            return

        res = man_base_regex.fullmatch(fname)
        if not res:
            return

        category = res.group('category')
        filename = Path(res.group('filename'))
        suffixes = filename.suffixes

        if self.compress_ext:
            if self.compress_ext != suffixes[-1][1:]:
                self.output.add_info('W', pkg, 'manpage-not-compressed',
                                     self.compress_ext, fname)
            suffixes = suffixes[:-1]

        if suffixes:
            file_category = suffixes[-1][1:]
            if not file_category.startswith(category):
                self.output.add_info('E', pkg, 'bad-manual-page-folder', fname, f'expected folder: man{file_category}')
            if str(filename.parent) != '.':
                self.output.add_info('E', pkg, 'manual-page-in-subfolder', fname)

    def _check_file_infopage_compressed(self, pkg, fname):
        """
        Check if the the info page is compressed with the compression method
        stated in the rpmlint configuration (CompressExtension option).

        Print a warning if it's not compressed.
        """
        if self.compress_ext and self.info_regex.search(fname) and \
                not fname.endswith('/info/dir') and not fname.endswith(self.compress_ext):
            self.output.add_info('W', pkg, 'infopage-not-compressed',
                                 self.compress_ext, fname)

    def _check_file_crond(self, pkg, fname, pkgfile):
        if not fname.startswith('/etc/cron.d/'):
            return

        mode = pkgfile.mode
        mode_is_exec = mode & 0o111
        if stat.S_ISLNK(mode):
            self.output.add_info('E', pkg, 'symlink-crontab-file', fname)

        if mode_is_exec:
            self.output.add_info('E', pkg, 'executable-crontab-file', fname)

        if stat.S_IWGRP & mode or stat.S_IWOTH & mode:
            self.output.add_info('E', pkg, 'non-owner-writeable-only-crontab-file', fname)

    def _check_file_zero_perms(self, pkg, fname, pkgfile):
        mode = pkgfile.mode
        perm = mode & 0o7777
        if not perm:
            if pkgfile.is_ghost:
                perms, user, group = find_perm_in_tmpfiles(pkg, pkgfile.name)
                suggestion = f'Suggestion: "%ghost %attr({perms},{user},{group}) {pkgfile.name}"'
                # Suggest the attrs if there's a tmpfiles.d
                self.output.add_info('W', pkg, 'zero-perms-ghost', suggestion)
            else:
                self.output.add_info('W', pkg, 'zero-perms', fname, '%o' % perm)

    def _check_file_unexpandaed_macro(self, pkg, fname):
        for match in self.macro_regex.findall(fname):
            self.output.add_info('W', pkg, 'unexpanded-macro', fname, match)

    def _check_file_non_standard_uid(self, pkg, fname, pkgfile):
        if pkgfile.user not in self.standard_users:
            self.output.add_info('W', pkg, 'non-standard-uid', fname, pkgfile.user)

    def _check_file_non_standard_gid(self, pkg, fname, pkgfile):
        if pkgfile.group not in self.standard_groups:
            self.output.add_info('W', pkg, 'non-standard-gid', fname, pkgfile.group)

    def _check_file_kernel_modules(self, pkg, fname):
        if not self.module_rpms_ok and kernel_modules_regex.search(fname) and not \
                self.is_kernel_package:
            self.output.add_info('E', pkg, 'kernel-modules-not-in-kernel-packages', fname)

    def _check_file_dir_or_file(self, pkg, fname):
        for i in self.disallowed_dirs:
            if fname.startswith(i):
                self.output.add_info('E', pkg, 'dir-or-file-in-%s' %
                                     '-'.join(i.split('/')[1:]), fname)

    def _check_file_non_ghost_in_run(self, pkg, fname):
        if fname.startswith('/run/'):
            if fname not in self.ghost_files:
                self.output.add_info('W', pkg, 'non-ghost-in-run', fname)

    def _check_file_systemd_unit_in_etc(self, pkg, fname):
        if fname.startswith('/etc/systemd/system/'):
            self.output.add_info('W', pkg, 'systemd-unit-in-etc', fname)

    def _check_file_udev_rule_in_etc(self, pkg, fname):
        if fname.startswith('/etc/udev/rules.d/'):
            self.output.add_info('W', pkg, 'udev-rule-in-etc', fname)

    def _check_file_tmpfiles_conf_in_etc(self, pkg, fname):
        if fname.startswith('/etc/tmpfiles.d/'):
            self.output.add_info('W', pkg, 'tmpfiles-conf-in-etc', fname)

    def _check_file_subdir_in_bin(self, pkg, fname):
        if sub_bin_regex.search(fname):
            self.output.add_info('E', pkg, 'subdir-in-bin', fname)

    def _check_file_siteperl_in_perl_module(self, pkg, fname):
        if '/site_perl/' in fname:
            self.output.add_info('W', pkg, 'siteperl-in-perl-module', fname)

    def _check_file_backup_file_in_package(self, pkg, fname):
        if backup_regex.search(fname):
            self.output.add_info('E', pkg, 'backup-file-in-package', fname)

    def _check_file_version_control_internal_file(self, pkg, fname):
        if scm_regex.search(fname):
            self.output.add_info('E', pkg, 'version-control-internal-file', fname)

    def _check_file_htaccess_file(self, pkg, fname):
        if fname.endswith('/.htaccess'):
            self.output.add_info('E', pkg, 'htaccess-file', fname)

    def _check_file_hidden_file_or_dir(self, pkg, fname):
        if (hidden_file_regex.search(fname) and
                not fname.startswith('/etc/skel/') and
                not fname.endswith('/.build-id') and
                not fname.endswith('/.cargo-checksum.json')):
            self.output.add_info('W', pkg, 'hidden-file-or-dir', fname)

    def _check_file_manifest_in_perl_module(self, pkg, fname):
        if manifest_perl_regex.search(fname):
            self.output.add_info('W', pkg, 'manifest-in-perl-module', fname)

    def _check_file_info_dir_file(self, pkg, fname):
        if fname == '/usr/info/dir' or fname == '/usr/share/info/dir':
            self.output.add_info('E', pkg, 'info-dir-file', fname)

    def _check_file_makefile_junk(self, pkg, fname):
        fpath = Path(fname)
        is_doc = fname in pkg.doc_files
        if fpath.name == 'Makefile.am' and str(fpath.with_suffix('.in')) in pkg.files and is_doc:
            self.output.add_info('W', pkg, 'makefile-junk', fname)

    def _check_file_logrotate(self, pkg, fname):
        res = logrotate_regex.search(fname)
        if res:
            self.logrotate_file = True
            if res.group(1) != pkg.name:
                self.output.add_info('E', pkg, 'incoherent-logrotate-file', fname)

        deps = [x[0] for x in pkg.requires + pkg.recommends + pkg.suggests]
        if res and 'logrotate' not in deps and pkg.name != 'logrotate':
            self.output.add_info('E', pkg, 'missing-dependency-to-logrotate', 'for logrotate script', fname)

    def _check_file_crontab(self, pkg, fname):
        deps = [x[0] for x in pkg.requires + pkg.recommends + pkg.suggests]
        if fname.startswith('/etc/cron.') and 'crontabs' not in deps and pkg.name != 'crontabs':
            self.output.add_info('E', pkg, 'missing-dependency-to-crontabs', 'for cron script', fname)

    def _check_file_xinetd(self, pkg, fname):
        deps = [x[0] for x in pkg.requires + pkg.recommends + pkg.suggests]
        if fname.startswith('/etc/xinet.d/') and 'xinetd' not in deps and pkg.name != 'xinetd':
            self.output.add_info('E', pkg, 'missing-dependency-to-xinetd', 'for xinet.d script', fname)

    def _check_file_compressed_symlink(self, pkg, fname, pkgfile):
        link = pkgfile.linkto
        if link != '':
            ext = compr_regex.search(link)
            if ext and not re.compile(r'\.%s$' % ext.group(1)).search(fname):
                self.output.add_info('E', pkg, 'compressed-symlink-with-wrong-ext',
                                     fname, link)

    def _check_file_hardlink(self, pkg, fname, pkgfile):
        rdev = pkgfile.rdev
        inode = pkgfile.inode

        # Hardlink check
        for hardlink in self.hardlinks.get((rdev, inode), ()):
            if Path(hardlink).parent != Path(fname).parent:
                self.output.add_info('W', pkg, 'cross-directory-hard-link', fname, hardlink)
        self.hardlinks.setdefault((rdev, inode), []).append(fname)

    def _check_file_link_devel(self, pkg, fname, pkgfile):
        is_so = sofile_regex.search(fname)
        if not self.devel_pkg and is_so and not pkgfile.linkto.endswith('.so'):
            self.output.add_info('W', pkg, 'devel-file-in-non-devel-package', fname)

    def _check_file_link_man(self, pkg, fname):
        res = man_base_regex.fullmatch(fname)
        if res:
            self.man_basenames.add(res.group('binary'))

    def _check_file_link_bindir_exes(self, pkg, fname):
        res = bin_regex.search(fname)
        if res:
            exe = res.group(1)
            if '/' not in exe:
                self.bindir_exes.setdefault(exe, [])

    def _check_file_link_absolute(self, pkg, fname, pkgfile):
        link = pkgfile.linkto

        # absolute link
        r = absolute_regex.search(link)
        if not r:
            return

        is_so = sofile_regex.search(fname)
        if not is_so and link not in pkg.files and \
                link not in self.req_names:
            is_exception = False
            for e in self.dangling_exceptions.values():
                if e['path'].search(link):
                    is_exception = e['name']
                    break
            if is_exception:
                if is_exception not in self.req_names:
                    self.output.add_info('W', pkg, 'no-dependency-on',
                                         is_exception)
            else:
                self.output.add_info('W', pkg, 'dangling-symlink', fname, link)
        linktop = r.group(1)

        r = absolute_regex.search(fname)
        if r:
            filetop = r.group(1)
            if filetop == linktop or self.use_relative_symlinks:
                self.output.add_info('W', pkg, 'symlink-should-be-relative',
                                     fname, link)

    def _check_file_link_relative(self, pkg, fname, pkgfile):
        link = pkgfile.linkto

        # relative link
        r = absolute_regex.search(link)
        if r:
            return

        is_so = sofile_regex.search(fname)
        if not is_so:
            abslink = f'{Path(fname).parent}/{link}'
            abslink = os.path.normpath(abslink)
            if abslink not in pkg.files and abslink not in self.req_names:
                is_exception = False
                for e in self.dangling_exceptions.values():
                    if e['path'].search(link):
                        is_exception = e['name']
                        break
                if is_exception:
                    if is_exception not in self.req_names:
                        self.output.add_info('W', pkg, 'no-dependency-on',
                                             is_exception)
                else:
                    self.output.add_info('W', pkg, 'dangling-relative-symlink',
                                         fname, link)
        pathcomponents = fname.split('/')[1:]
        r = points_regex.search(link)
        lastpop = None
        mylink = None

        while r:
            mylink = r.group(1)
            if len(pathcomponents) == 0:
                self.output.add_info('E', pkg, 'symlink-has-too-many-up-segments',
                                     fname, link)
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
                self.output.add_info('W', pkg, 'symlink-should-be-absolute', fname,
                                     link)
            # check additional segments for mistakes like
            # `foo/../bar/'
            for linksegment in mylink.split('/'):
                if linksegment == '..':
                    self.output.add_info('E',
                                         pkg,
                                         'symlink-contains-up-and-down-segments',
                                         fname, link)

    def _check_file_link_bindir_shebang(self, pkg, fname, pkgfile):
        basedir = Path(fname).parent
        linkto = str((basedir / Path(pkgfile.linkto)).resolve())
        # Link to a file not in the package, so ignore
        if linkto not in pkg.files:
            return

        realbin = pkg.files[linkto]
        # Link to something in bindir is okay
        if bin_regex.search(realbin.name):
            return
        if not stat.S_ISREG(realbin.mode):
            return

        file_chunk, file_istext = self.peek(realbin.path, pkg)
        file_interpreter, _file_interpreter_args = script_interpreter(file_chunk)
        # Not a script with shebang, so ignore
        if not file_interpreter:
            return

        # If the shebang interpreter is a dependency, it's okay
        deps = [x[0] for x in pkg.requires]
        if file_interpreter in deps:
            return

        self.output.add_info('W', pkg, 'symlink-to-binary-with-shebang', fname,
                             f'is a link to a script ({realbin.name}) but missing'
                             f' requires for {file_interpreter}')

    def _check_file_link(self, pkg, fname, pkgfile):
        if not stat.S_ISLNK(pkgfile.mode):
            return

        self._check_file_link_devel(pkg, fname, pkgfile)
        self._check_file_link_man(pkg, fname)
        self._check_file_link_bindir_exes(pkg, fname)
        self._check_file_link_absolute(pkg, fname, pkgfile)
        self._check_file_link_relative(pkg, fname, pkgfile)
        self._check_file_link_bindir_shebang(pkg, fname, pkgfile)

    def _check_file_dir(self, pkg, fname, pkgfile):
        if not stat.S_ISDIR(pkgfile.mode):
            return

        mode = pkgfile.mode
        perm = mode & 0o7777
        if mode & 0o1002 == 2:  # world writable w/o sticky bit
            self.output.add_info('E', pkg, 'world-writable', fname, '%o' % perm)
        if perm != 0o755:
            self.output.add_info('E', pkg, 'non-standard-dir-perm', fname, '%o' % perm)
        if pkg.name not in filesys_packages and fname in STANDARD_DIRS:
            self.output.add_info('E', pkg, 'standard-dir-owned-by-package', fname)
        if hidden_file_regex.search(fname) and not fname.endswith('/.build-id'):
            self.output.add_info('W', pkg, 'hidden-file-or-dir', fname)

    def _check_file_normal_file(self, pkg, fname, pkgfile):
        if not stat.S_ISREG(pkgfile.mode):
            return

        self._file_nonexec_file = False
        self._file_chunk = None
        self._file_istext = False
        self._file_interpreter = None
        self._file_interpreter_args = None
        self._file_is_buildconfig = False

        # set[ug]id bit check
        self._check_file_normal_file_setuid_bit(pkg, fname, pkgfile)
        self._check_file_normal_file_libfile(pkg, fname)
        self._check_file_normal_file_logfile(pkg, fname, pkgfile)
        # Fill class attributes, chunk, istext, interpreter, is_buildconfig
        self._check_file_normal_file_getdata(pkg, fname, pkgfile)
        self._check_file_normal_file_doc(pkg, fname)
        self._check_file_normal_file_non_devel(pkg, fname)
        self._check_file_normal_file_lib(pkg, fname, pkgfile)
        self._check_file_normal_file_depmod_call(pkg, fname)
        self._check_file_normal_file_install_info(pkg, fname)
        self._check_file_normal_file_perl_temp(pkg, fname)
        self._check_file_normal_file_rpaths_in_buildconfig(pkg, fname)
        # look for man pages
        self._check_file_normal_file_look_for_man(pkg, fname)
        self._check_file_normal_file_bin(pkg, fname, pkgfile)
        self._check_file_normal_file_devel(pkg, fname, pkgfile)
        self._check_file_normal_file_non_readable(pkg, fname, pkgfile)
        self._check_file_normal_file_zero_length(pkg, fname, pkgfile)
        self._check_file_normal_file_world_w(pkg, fname, pkgfile)
        self._check_file_normal_file_perl_dep(pkg, fname)
        self._check_file_normal_file_python_dep(pkg, fname)
        self._check_file_normal_file_python_source(pkg, fname)
        # normal executable check
        self._check_file_normal_file_exec(pkg, fname, pkgfile)
        self._check_file_normal_file_non_conf_in_etc(pkg, fname)
        self._check_file_normal_file_python_noarch(pkg, fname)
        self._check_file_normal_file_debuginfo(pkg, fname)
        self._check_file_normal_file_gzipped_svg(pkg, fname)
        self._check_file_normal_file_pem(pkg, fname)
        self._check_file_normal_file_tcl(pkg, fname)
        # text file checks
        self._check_file_normal_file_text(pkg, fname, pkgfile)
        self._check_file_normal_file_not_utf8(pkg, fname, pkgfile)

    def _check_file_normal_file_setuid_bit(self, pkg, fname, pkgfile):
        user = pkgfile.user
        group = pkgfile.group
        mode = pkgfile.mode
        perm = mode & 0o7777
        if stat.S_ISGID & mode or stat.S_ISUID & mode:
            if stat.S_ISUID & mode:
                self.output.add_info('E', pkg, 'setuid-binary', fname, user, '%o' % perm)
            if (stat.S_ISGID & mode and
                    not (group == 'games' and
                         (games_path_regex.search(fname) or
                          self.games_group_regex.search(pkg[rpm.RPMTAG_GROUP])))):
                self.output.add_info('E', pkg, 'setgid-binary', fname, group,
                                     '%o' % perm)
            if mode & 0o777 != 0o755:
                self.output.add_info('E', pkg, 'non-standard-executable-perm', fname,
                                     '%o' % perm)

    def _check_file_normal_file_libfile(self, pkg, fname):
        is_doc = fname in pkg.doc_files

        if not self.devel_pkg:
            if lib_path_regex.search(fname):
                self.lib_file = True
            elif not is_doc:
                self.non_lib_file = fname

    def _check_file_normal_file_logfile(self, pkg, fname, pkgfile):
        user = pkgfile.user
        group = pkgfile.group

        if log_regex.search(fname):
            self._file_nonexec_file = True
            if user != 'root':
                self.output.add_info('E', pkg, 'non-root-user-log-file', fname, user)
            if group != 'root':
                self.output.add_info('E', pkg, 'non-root-group-log-file', fname, group)
            if fname not in self.ghost_files:
                self.output.add_info('E', pkg, 'non-ghost-file', fname)

    def _check_file_normal_file_getdata(self, pkg, fname, pkgfile):
        res = None
        try:
            res = os.access(pkgfile.path, os.R_OK)
        except UnicodeError as e:  # e.g. non-ASCII, C locale, python 3
            self.output.add_info('W', pkg, 'inaccessible-filename', fname, e)
        else:
            if res:
                (self._file_chunk, self._file_istext) = self.peek(pkgfile.path, pkg)

        (self._file_interpreter, self._file_interpreter_args) = script_interpreter(self._file_chunk)
        self._file_is_buildconfig = self._file_istext and buildconfigfile_regex.search(fname)

    def _check_file_normal_file_doc(self, pkg, fname):
        is_doc = fname in pkg.doc_files
        if doc_regex.search(fname):
            if not self._file_interpreter:
                self._file_nonexec_file = True
            if not is_doc:
                self.output.add_info('E', pkg, 'not-listed-as-documentation', fname)

    def _check_file_normal_file_non_devel(self, pkg, fname):
        if self.devel_pkg and fname.endswith('.typelib'):
            self.output.add_info('E', pkg, 'non-devel-file-in-devel-package', fname)

    def _check_file_normal_file_lib(self, pkg, fname, pkgfile):
        # check ldconfig call in %post and %postun
        mode = pkgfile.mode
        if lib_regex.search(fname):
            if self.devel_pkg and not (sofile_regex.search(fname) and stat.S_ISLNK(mode)):
                self.output.add_info('E', pkg, 'non-devel-file-in-devel-package', fname)
            if not self.postin:
                self.output.add_info('E', pkg, 'library-without-ldconfig-postin', fname)
            else:
                if not ldconfig_regex.search(self.postin):
                    self.output.add_info('E', pkg, 'postin-without-ldconfig', fname)

            if not self.postun:
                self.output.add_info('E', pkg, 'library-without-ldconfig-postun', fname)
            else:
                if not ldconfig_regex.search(self.postun):
                    self.output.add_info('E', pkg, 'postun-without-ldconfig', fname)

    def _check_file_normal_file_depmod_call(self, pkg, fname):
        # check depmod call in %post and %postun
        res = not self.is_kernel_package and kernel_modules_regex.search(fname)
        if res:
            kernel_version = res.group(1)
            kernel_version_regex = re.compile(
                r'\bdepmod\s+-a.*F\s+/boot/System\.map-' +
                re.escape(kernel_version) + r'\b.*\b' +
                re.escape(kernel_version) + r'\b',
                re.MULTILINE | re.DOTALL)

            if not self.postin or not depmod_regex.search(self.postin):
                self.output.add_info('E', pkg, 'module-without-depmod-postin', fname)
            # check that we run depmod on the right kernel
            elif not kernel_version_regex.search(self.postin):
                self.output.add_info('E', pkg, 'postin-with-wrong-depmod', fname)

            if not self.postun or not depmod_regex.search(self.postun):
                self.output.add_info('E', pkg, 'module-without-depmod-postun', fname)
            # check that we run depmod on the right kernel
            elif not kernel_version_regex.search(self.postun):
                self.output.add_info('E', pkg, 'postun-with-wrong-depmod', fname)

    def _check_file_normal_file_install_info(self, pkg, fname):
        # check install-info call in %post and %postun
        if fname.startswith('/usr/share/info/'):
            if not self.postin:
                self.output.add_info('E', pkg,
                                     'info-files-without-install-info-postin', fname)
            elif not install_info_regex.search(self.postin):
                self.output.add_info('E', pkg, 'postin-without-install-info', fname)

            preun = pkg[rpm.RPMTAG_PREUN] or \
                pkg.scriptprog(rpm.RPMTAG_PREUNPROG)
            if not self.postun and not preun:
                self.output.add_info('E', pkg,
                                     'info-files-without-install-info-postun', fname)
            elif not ((self.postun and install_info_regex.search(self.postun)) or
                      (preun and install_info_regex.search(preun))):
                self.output.add_info('E', pkg, 'postin-without-install-info', fname)

    def _check_file_normal_file_perl_temp(self, pkg, fname):
        # check perl temp file
        if perl_temp_file_regex.search(fname):
            self.output.add_info('W', pkg, 'perl-temp-file', fname)

    def _check_file_normal_file_rpaths_in_buildconfig(self, pkg, fname):
        # check rpaths in buildconfig files
        if self._file_is_buildconfig:
            ln = pkg.grep(buildconfig_rpath_regex, fname)
            if ln:
                self.output.add_info('E', pkg, 'rpath-in-buildconfig', fname, 'lines', ln)

    def _check_file_normal_file_look_for_man(self, pkg, fname):
        res = man_base_regex.fullmatch(fname)
        if res:
            self.man_basenames.add(res.group('binary'))

    def _check_file_normal_file_bin(self, pkg, fname, pkgfile):
        mode = pkgfile.mode
        perm = mode & 0o7777
        mode_is_exec = mode & 0o111
        res = bin_regex.search(fname)
        if res:
            if not mode_is_exec:
                self.output.add_info('W', pkg, 'non-executable-in-bin', fname,
                                     '%o' % perm)
            else:
                exe = res.group(1)
                if '/' not in exe:
                    self.bindir_exes.setdefault(exe, []).append(fname)

    def _check_file_normal_file_devel(self, pkg, fname, pkgfile):
        is_doc = fname in pkg.doc_files
        if (not self.devel_pkg and not is_doc and
            (self._file_is_buildconfig or includefile_regex.search(fname) or
             develfile_regex.search(fname))):
            self.output.add_info('W', pkg, 'devel-file-in-non-devel-package', fname)

    def _check_file_normal_file_non_readable(self, pkg, fname, pkgfile):
        mode = pkgfile.mode
        perm = mode & 0o7777
        if mode & 0o444 != 0o444 and perm & 0o7000 == 0:
            ok_nonreadable = False
            for regex in non_readable_regexs:
                if regex.search(fname):
                    ok_nonreadable = True
                    break
            if not ok_nonreadable:
                self.output.add_info('E', pkg, 'non-readable', fname, '%o' % perm)

    def _check_file_normal_file_zero_length(self, pkg, fname, pkgfile):
        size = pkgfile.size
        if size == 0 and not normal_zero_length_regex.search(fname) and \
                fname not in self.ghost_files:
            self.output.add_info('E', pkg, 'zero-length', fname)

    def _check_file_normal_file_world_w(self, pkg, fname, pkgfile):
        mode = pkgfile.mode
        perm = mode & 0o7777
        if mode & stat.S_IWOTH:
            self.output.add_info('E', pkg, 'world-writable', fname, '%o' % perm)

    def _check_file_normal_file_perl_dep(self, pkg, fname):
        if not self.perl_dep_error:
            res = perl_regex.search(fname)
            if res:
                deps = [x[0] for x in pkg.requires + pkg.recommends + pkg.suggests]
                if self.perl_version_trick:
                    vers = res.group(1) + '.' + res.group(2)
                else:
                    vers = res.group(1) + res.group(2)
                if not (pkg.check_versioned_dep('perl-base', vers) or
                        pkg.check_versioned_dep('perl', vers) or
                        f'perl(:MODULE_COMPAT_{vers})' in deps):
                    self.output.add_info('E', pkg, 'no-dependency-on',
                                         'perl-base', vers)
                    self.perl_dep_error = True

    def _check_file_normal_file_python_dep(self, pkg, fname):
        if not self.python_dep_error:
            res = python_regex.search(fname)
            if (res and not
                    any(pkg.check_versioned_dep(dep, res.group(1))
                        for dep in (
                            'python', 'python-base', 'python(abi)'))):
                self.output.add_info('E', pkg, 'no-dependency-on', 'python-base',
                                     res.group(1))
                self.python_dep_error = True

    def _check_file_normal_file_python_source(self, pkg, fname):
        source_file = python_bytecode_to_script(fname)
        if not source_file:
            return

        if source_file in pkg.files:
            if self._file_chunk:
                # Verify that the magic ABI value embedded in the
                # .pyc header is correct
                found_magic = pyc_magic_from_chunk(self._file_chunk)
                exp_magic, exp_version = get_expected_pyc_magic(fname, self.python_default_version)
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
                           fname, 'expected %s (%s), found %d (%s)' %
                           (' or '.join(map(str, exp_magic)),
                            exp_version or self.python_default_version,
                            found_magic, found_version))
                    if exp_version is not None:
                        self.output.add_info('E', *msg)
                    else:
                        self.output.add_info('W', *msg)

                # Verify that the timestamp embedded in the .pyc
                # header matches the mtime of the .py file:
                pyc_timestamp = pyc_mtime_from_chunk(self._file_chunk)
                # If it's a symlink, check target file mtime.
                srcfile = pkg.readlink(pkg.files[source_file])
                if not srcfile:
                    self.output.add_info('W', pkg, 'python-bytecode-without-source', fname)
                elif (pyc_timestamp is not None and
                      pyc_timestamp != srcfile.mtime):
                    cts = datetime.fromtimestamp(
                        pyc_timestamp).isoformat()
                    sts = datetime.fromtimestamp(
                        srcfile.mtime).isoformat()
                    self.output.add_info('E',
                                         pkg, 'python-bytecode-inconsistent-mtime',
                                         fname, cts, srcfile.name, sts)
        else:
            self.output.add_info('W', pkg, 'python-bytecode-without-source', fname)

    def _check_file_normal_file_exec(self, pkg, fname, pkgfile):
        mode = pkgfile.mode
        perm = mode & 0o7777
        mode_is_exec = mode & 0o111
        if mode & stat.S_IXUSR and perm != 0o755:
            self.output.add_info('E', pkg, 'non-standard-executable-perm',
                                 fname, '%o' % perm)
        if mode_is_exec:
            if fname in self.config_files:
                self.output.add_info('E', pkg, 'executable-marked-as-config-file', fname)
            if not self._file_nonexec_file:
                # doc_regex and log_regex checked earlier, no match,
                # check rest of usual cases here.  Sourced scripts have
                # their own check, so disregard them here.
                self._file_nonexec_file = fname.endswith('.pc') or \
                    compr_regex.search(fname) or \
                    includefile_regex.search(fname) or \
                    develfile_regex.search(fname) or \
                    logrotate_regex.search(fname)
            if self._file_nonexec_file:
                self.output.add_info('W', pkg, 'spurious-executable-perm', fname)

    def _check_file_normal_file_non_conf_in_etc(self, pkg, fname):
        if fname.startswith('/etc/') and fname not in self.config_files and \
                fname not in self.ghost_files and not fname.startswith('/etc/ld.so.conf.d/'):
            self.output.add_info('W', pkg, 'non-conffile-in-etc', fname)

    def _check_file_normal_file_python_noarch(self, pkg, fname):
        if pkg.arch == 'noarch' and fname.startswith('/usr/lib64/python'):
            self.output.add_info('E', pkg, 'noarch-python-in-64bit-path', fname)

    def _check_file_normal_file_debuginfo(self, pkg, fname):
        if self.debuginfo_package:
            if fname.endswith('.debug'):
                self.debuginfo_debugs = True
            else:
                self.debuginfo_srcs = True

    def _check_file_normal_file_gzipped_svg(self, pkg, fname):
        if fname.endswith('.svgz') and fname[0:-1] not in pkg.files \
                and scalable_icon_regex.search(fname):
            self.output.add_info('W', pkg, 'gzipped-svg-icon', fname)

    def _check_file_normal_file_pem(self, pkg, fname):
        if fname.endswith('.pem') and fname not in self.ghost_files:
            if pkg.grep(start_certificate_regex, fname):
                self.output.add_info('W', pkg, 'pem-certificate', fname)
            if pkg.grep(start_private_key_regex, fname):
                self.output.add_info('E', pkg, 'pem-private-key', fname)

    def _check_file_normal_file_tcl(self, pkg, fname):
        if tcl_regex.search(fname):
            self.output.add_info('E', pkg, 'tcl-extension-file', fname)

    def _check_file_normal_file_text(self, pkg, fname, pkgfile):
        if not self._file_istext:
            return

        mode = pkgfile.mode
        perm = mode & 0o7777
        mode_is_exec = mode & 0o111
        is_doc = fname in pkg.doc_files

        # ignore perl module shebang -- TODO: disputed...
        if fname.endswith('.pm'):
            self._file_interpreter = None
        # sourced scripts should not be executable
        if sourced_script_regex.search(fname):
            if self._file_interpreter:
                self.output.add_info('E', pkg,
                                     'sourced-script-with-shebang', fname,
                                     self._file_interpreter, self._file_interpreter_args)
            if mode_is_exec:
                self.output.add_info('E', pkg, 'executable-sourced-script',
                                     fname, '%o' % perm)
        # ...but executed ones should
        elif self._file_interpreter or mode_is_exec or script_regex.search(fname):
            if self._file_interpreter:
                res = interpreter_regex.search(self._file_interpreter)
                if (mode_is_exec or script_regex.search(fname)):
                    if res and res.group(1) == 'env':
                        self.output.add_info('E', pkg, 'env-script-interpreter',
                                             fname, self._file_interpreter,
                                             self._file_interpreter_args)
                    elif not res:
                        self.output.add_info('E', pkg, 'wrong-script-interpreter',
                                             fname, self._file_interpreter,
                                             self._file_interpreter_args)
            elif not self._file_nonexec_file and not \
                    (lib_path_regex.search(fname) and
                     fname.endswith('.la')):
                self.output.add_info('E', pkg, 'script-without-shebang', fname)

            if not mode_is_exec and not is_doc and \
                    self._file_interpreter and self._file_interpreter.startswith('/'):
                self.output.add_info('E', pkg, 'non-executable-script', fname,
                                     '%o' % perm, self._file_interpreter,
                                     self._file_interpreter_args)
            if b'\r' in self._file_chunk:
                self.output.add_info('E', pkg, 'wrong-script-end-of-line-encoding', fname)
        elif is_doc and not self.skipdocs_regex.search(fname):
            if b'\r' in self._file_chunk:
                self.output.add_info('W', pkg, 'wrong-file-end-of-line-encoding', fname)
            # We check only doc text files for UTF-8-ness;
            # checking everything may be slow and can generate
            # lots of unwanted noise.
            if not is_utf8(pkgfile.path):
                self.output.add_info('W', pkg, 'file-not-utf8', fname)
        if fsf_license_regex.search(self._file_chunk) and \
                fsf_wrong_address_regex.search(self._file_chunk):
            self.output.add_info('E', pkg, 'incorrect-fsf-address', fname)

    def _check_file_normal_file_not_utf8(self, pkg, fname, pkgfile):
        is_doc = fname in pkg.doc_files
        if not self._file_istext and is_doc and self._file_chunk and compr_regex.search(fname):
            ff = compr_regex.sub('', fname)
            # compressed docs, eg. info and man files etc
            if not self.skipdocs_regex.search(ff) and not is_utf8(pkgfile.path):
                self.output.add_info('W', pkg, 'file-not-utf8', fname)
