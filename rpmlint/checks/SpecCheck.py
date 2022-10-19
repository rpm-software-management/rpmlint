from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse

import rpm
from rpmlint import pkg as Pkg
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import ENGLISH_ENVIROMENT, readlines

# Don't check for hardcoded library paths in biarch packages
DEFAULT_BIARCH_PACKAGES = '^(gcc|glibc)'


def re_tag_compile(tag):
    rpm_tag = fr'^{tag}\s*:\s*(\S.*?)\s*$'
    return re.compile(rpm_tag, re.IGNORECASE)


patch_regex = re_tag_compile(r'Patch(\d*)')
applied_patch_regex = re.compile(r'^%patch(\d*)')
applied_patch_p_regex = re.compile(r'\s-P\s+(\d+)\b')
applied_patch_pipe_regex = re.compile(r'\s%\{PATCH(\d+)\}\s*\|\s*(%\{?__)?patch\b')
applied_patch_i_regex = re.compile(r'(?:%\{?__)?patch\}?.*?\s+(?:<|-i)\s+%\{PATCH(\d+)\}')
source_dir_regex = re.compile(r'^[^#]*(\$RPM_SOURCE_DIR|%{?_sourcedir}?)')
obsolete_tags_regex = re_tag_compile(r'(?:Serial|Copyright)')
buildroot_regex = re_tag_compile('BuildRoot')
prefix_regex = re_tag_compile('Prefix')
packager_regex = re_tag_compile('Packager')
buildarch_regex = re_tag_compile('BuildArch(?:itectures)?')
buildprereq_regex = re_tag_compile('BuildPreReq')
prereq_regex = re_tag_compile(r'PreReq(\(.*\))')
suse_version_regex = re.compile(r'%({\?)?suse_version}?\s*[<>=]+\s*(?P<version>\d+)')

make_check_regex = re.compile(r'(^|\s|%{?__)make}?\s+(check|test)')
rm_regex = re.compile(r'(^|\s)((.*/)?rm|%{?__rm}?) ')
rpm_buildroot_regex = re.compile(r'^[^#]*?(?:(\\*)\${?RPM_BUILD_ROOT}?|(%+){?buildroot}?)')
configure_libdir_spec_regex = re.compile(r'ln |\./configure[^#]*--libdir=(\S+)[^#]*')
lib_package_regex = re.compile(r'^%package.*\Wlib')
ifarch_regex = re.compile(r'^\s*%ifn?arch\s')
if_regex = re.compile(r'^\s*%if\s')
endif_regex = re.compile(r'^\s*%endif\b')
biarch_package_regex = re.compile(DEFAULT_BIARCH_PACKAGES)
libdir_regex = re.compile(r'%{?_lib(?:dir)?\}?\b')
section_regexs = {x: re.compile('^%' + x + r'(?:\s|$)')
                  for x in ('build', 'changelog', 'check', 'clean', 'description', 'files',
                            'install', 'package', 'prep') + Pkg.RPM_SCRIPTLETS}
deprecated_grep_regex = re.compile(r'\b[ef]grep\b')

# Only check for /lib, /usr/lib, /usr/X11R6/lib
# TODO: better handling of X libraries and modules.
hardcoded_library_paths = '(/lib|/usr/lib|/usr/X11R6/lib/(?!([^/]+/)+)[^/]*\\.([oa]|la|so[0-9.]*))'
hardcoded_library_path_regex = re.compile(r'^[^#]*((^|\s+|\.\./\.\.|\${?RPM_BUILD_ROOT}?|%{?buildroot}?|%{?_prefix}?)' + hardcoded_library_paths + r'(?=[\s;/])([^\s,;]*))')

DEFINE_RE = r'(^|\s)%(define|global)\s+'
depscript_override_regex = re.compile(DEFINE_RE + r'__find_(requires|provides)\s')
depgen_disable_regex = re.compile(DEFINE_RE + r'_use_internal_dependency_generator\s+0')
patch_fuzz_override_regex = re.compile(DEFINE_RE + r'_default_patch_fuzz\s+(\d+)')

# See https://bugzilla.redhat.com/488146 for details
indent_spaces_regex = re.compile('( \t|(^|\t)([^\t]{8})*[^\t]{4}[^\t]?([^\t][^\t.!?]|[^\t]?[.!?] )  )')

requires_regex = re.compile(r'^(?:Build)?(?:Pre)?Req(?:uires)?(?:\([^\)]+\))?:\s*(.*)', re.IGNORECASE)
provides_regex = re.compile(r'^Provides(?:\([^\)]+\))?:\s*(.*)', re.IGNORECASE)
obsoletes_regex = re.compile(r'^Obsoletes:\s*(.*)', re.IGNORECASE)
conflicts_regex = re.compile(r'^(?:Build)?Conflicts:\s*(.*)', re.IGNORECASE)

compop_regex = re.compile(r'[<>=]')

setup_regex = re.compile(r'%setup\b')  # intentionally no whitespace before!
setup_q_regex = re.compile(r' -[A-Za-z]*q')
setup_t_regex = re.compile(r' -[A-Za-z]*T')
setup_ab_regex = re.compile(r' -[A-Za-z]*[ab]')
autosetup_regex = re.compile(r'^\s*%autosetup(\s.*|$)')
autosetup_n_regex = re.compile(r' -[A-Za-z]*N')
autopatch_regex = re.compile(r'^\s*%autopatch(?:\s|$)')

filelist_regex = re.compile(r'\s+-f\s+\S+')
pkgname_regex = re.compile(r'\s+(?:-n\s+)?(\S+)')
tarball_regex = re.compile(r'\.(?:t(?:ar|[glx]z|bz2?)|zip)\b', re.IGNORECASE)

python_setup_test_regex = re.compile(r'^[^#]*(setup.py test)')

UNICODE_NBSP = '\xa0'


def unversioned(deps):
    """Yield unversioned dependency names from the given list."""
    for dep in deps:
        if not dep[1]:
            yield dep[0]


def contains_buildroot(line):
    """Check if the given line contains use of rpm buildroot."""
    res = rpm_buildroot_regex.search(line)
    if res and \
       (not res.group(1) or len(res.group(1)) % 2 == 0) and \
       (not res.group(2) or len(res.group(2)) % 2 != 0):
        return True
    return False


class SpecCheck(AbstractCheck):
    """Contain check methods that catch errors and warnings in a specfile."""

    def __init__(self, config, output):
        super().__init__(config, output)
        self._spec_file = None
        self._spec_name = None
        self.valid_groups = config.configuration['ValidGroups']
        self.mini_mode = config.mini_mode
        self.output.error_details.update({'non-standard-group':
                                         """The value of the Group tag in the package is not valid.  Valid groups are:
                                         '%s'.""" % ', '.join(self.valid_groups)})
        self.hardcoded_lib_path_exceptions_regex = re.compile(config.configuration['HardcodedLibPathExceptions'])

        # Default state
        self.patches = {}
        self.applied_patches = []
        self.applied_patches_ifarch = []
        self.patches_auto_applied = False
        self.source_dir = False
        self.buildroot = False
        self.configure_linenum = None
        self.configure_cmdline = ''
        self.mklibname = False
        self.is_lib_pkg = False
        self.if_depth = 0
        self.ifarch_depth = -1
        self.depscript_override = False
        self.depgen_disabled = False
        self.patch_fuzz_override = False
        self.indent_spaces = 0
        self.indent_tabs = 0
        self.section = {}

        self.current_section = 'package'
        # None == main package
        self.current_package = None
        self.package_noarch = {}

    def check_source(self, pkg):
        """Find specfile in SRPM and run spec file related checks."""
        wrong_spec = False
        self._spec_file = None
        self._spec_name = None

        # Check if a specfile exist in a specified path
        for fname, pkgfile in pkg.files.items():
            if fname.endswith('.spec'):
                self._spec_file = pkgfile.path
                self._spec_name = pkgfile.name
                if fname == pkg.name + '.spec':
                    wrong_spec = False
                    break
                else:
                    wrong_spec = True

        # method call
        self._check_no_spec_file(pkg)
        self._check_invalid_spec_name(pkg, wrong_spec)

        if self._spec_file:
            # check content of spec file
            with Pkg.FakePkg(self._spec_file) as package:
                self.check_spec(package)

    def check_spec(self, pkg):
        """Find specfile in specified path and run spec file related checks."""
        self._spec_file = pkg.name
        self._spec_file_dir = str(Path(self._spec_file).parent)

        # method call
        self._check_non_utf8_spec_file(pkg)

        self.pkg = pkg
        self.spec_only = isinstance(pkg, Pkg.FakePkg)

        spec_lines = readlines(self._spec_file)
        # Analyse specfile line by line to check for (E)rrors or (W)arnings
        # And initialize the SpecCheck instance for following checks
        self._check_lines(spec_lines)

        # Run checks for whole package
        self._check_no_buildroot_tag(pkg, self.buildroot)
        self._check_no_s_section(pkg, self.section)
        self._check_superfluous_clean_section(pkg, self.section)
        self._check_more_than_one_changelog_section(pkg, self.section)
        self._check_lib_package_without_mklibname(pkg, self.is_lib_pkg, self.mklibname)
        self._check_descript_without_disabling_depgen(pkg, self.depscript_override,
                                                      self.depgen_disabled)
        self._check_patch_fuzz_is_changed(pkg, self.patch_fuzz_override)
        self._check_mixed_use_of_space_and_tabs(pkg, self.indent_spaces, self.indent_tabs)
        self.check_ifarch_and_not_applied_patches(pkg, self.patches_auto_applied, self.patches,
                                                  self.applied_patches_ifarch, self.applied_patches)

        # Checks below require a real spec file
        if not self._spec_file:
            return
        if not self.mini_mode:
            self._check_specfile_error(pkg)
            self._check_invalid_url(pkg, rpm)

    def _check_no_spec_file(self, pkg):
        """Check if no spec file is found in RPM meta data."""
        if not self._spec_file:
            self.output.add_info('E', pkg, 'no-spec-file')

    def _check_invalid_spec_name(self, pkg, wrong_spec):
        """Check if spec file has same name as the 'Name: ' tag."""
        if wrong_spec and self._spec_file:
            self.output.add_info('E', pkg, 'invalid-spec-name')

    def _check_non_utf8_spec_file(self, pkg):
        """Check if spec file has UTF-8 character encoding."""
        if self._spec_file and not Pkg.is_utf8(self._spec_file):
            self.output.add_info('E', pkg, 'non-utf8-spec-file',
                                 self._spec_name or self._spec_file)

    def _check_no_buildroot_tag(self, pkg, buildroot):
        """Check if BuildRoot tag is used in the specfile."""
        if not buildroot:
            self.output.add_info('W', pkg, 'no-buildroot-tag')

    def _check_no_s_section(self, pkg, section):
        """Check if there is no (%prep, %build, %install)
        in the specfile.
        """
        for sec in ('prep', 'build', 'install'):
            if not section.get(sec):
                self.output.add_info('W', pkg, 'no-%%%s-section' % sec)

    def _check_superfluous_clean_section(self, pkg, section):
        """Check for a superfluous %clean section in the specfile.
        """
        if section.get('clean'):
            self.output.add_info('E', pkg, 'superfluous-%clean-section')

    def _check_more_than_one_changelog_section(self, pkg, section):
        """Check if specfile has more than one %changelog.
        prep, build, install, check prevented by rpmbuild 4.4
        """
        if section.get('changelog', 0) > 1:
            self.output.add_info('W', pkg, 'more-than-one-%changelog-section')

    def _check_lib_package_without_mklibname(self, pkg, is_lib_pkg, mklibname):
        """Check if package name is built using %mklibname to allow lib64 and lib32
        coexistence. This check is specific to Mandriva and it's derivatives,
        check issue #9 in rpm-software-management/rpmlint/issues
        """
        if is_lib_pkg and not mklibname:
            self.output.add_info('E', pkg, 'lib-package-without-%mklibname')

    def _check_descript_without_disabling_depgen(self, pkg, depscript_override, depgen_disabled):
        """Check if specfile has %define _use_internal_dependency_generator set to 0
        to disable it, or does not have define __find_provides/requires.
        """
        if depscript_override and not depgen_disabled:
            self.output.add_info('W', pkg, 'depscript-without-disabling-depgen')

    def _check_patch_fuzz_is_changed(self, pkg, patch_fuzz_override):
        """Check if specfile has internal patch fuzz was changed."""
        if patch_fuzz_override:
            self.output.add_info('W', pkg, 'patch-fuzz-is-changed')

    def _check_mixed_use_of_space_and_tabs(self, pkg, indent_spaces, indent_tabs):
        """Check if specfile has mixed uses of spaces and tabs."""
        if indent_spaces and indent_tabs:
            pkg.current_linenum = max(indent_spaces, indent_tabs)
            self.output.add_info('W', pkg, 'mixed-use-of-spaces-and-tabs',
                                 '(spaces: line %d, tab: line %d)' %
                                 (indent_spaces, indent_tabs))
            pkg.current_linenum = None

    def check_ifarch_and_not_applied_patches(self, pkg, patches_auto_applied,
                                             patches, applied_patches_ifarch, applied_patches):
        """Check if specfile has a patch applied inside an %ifarch block.
        and check if a patch was included but not applied."""
        if not patches_auto_applied:
            for pnum, pfile in patches.items():
                if pnum in applied_patches_ifarch:
                    self.output.add_info('W', pkg, '%ifarch-applied-patch',
                                         'Patch%d:' % pnum, pfile)

                # Check if a patch is included in specfile but was not applied.
                if pnum not in applied_patches:
                    self.output.add_info('W', pkg, 'patch-not-applied',
                                         'Patch%d:' % pnum, pfile)

    def _check_specfile_error(self, pkg):
        """It parse the specfile with rpm and forward errors to rpmlint output."""

        # We'd like to parse the specfile only once using python bindings,
        # but it seems errors from rpmlib get logged to stderr and we can't
        # capture and print them nicely, so we do it once each way :P
        try:
            outcmd = subprocess.run(
                ('rpm', '-q', '--qf=', '-D', '_sourcedir %s' % self._spec_file_dir,
                 '--specfile', self._spec_file), stderr=subprocess.PIPE, encoding='utf8', env=ENGLISH_ENVIROMENT)

            for line in outcmd.stderr.splitlines():
                line = line.strip()
                if line and 'warning:' not in line:
                    self.output.add_info('E', pkg, 'specfile-error', line)
        except UnicodeDecodeError as e:
            self.output.add_info('E', pkg, 'specfile-error', str(e))

    def _check_invalid_url(self, pkg, rpm):
        """Check if specfile has an invalid url."""
        # grab sources and patches from parsed spec object to get
        # them with macros expanded for URL checking
        spec_obj = None
        rpm.addMacro('_sourcedir', self._spec_file_dir)
        try:
            transaction_set = rpm.TransactionSet()
            spec_obj = transaction_set.parseSpec(str(self._spec_file))
        except (ValueError, rpm.error) as e:
            self.output.add_info('E', pkg, 'specfile-error', str(e).strip(),
                                 str(self._spec_file))
        rpm.delMacro('_sourcedir')
        if spec_obj:
            for src in spec_obj.sources:
                (url, num, flags) = src
                (scheme, netloc) = urlparse(url)[0:2]
                if flags & 1:  # rpmspec.h, rpm.org ticket #123
                    srctype = 'Source'
                else:
                    srctype = 'Patch'
                tag = f'{srctype}{num}'
                if scheme and netloc:
                    continue
                elif srctype == 'Source' and tarball_regex.search(url):
                    self.output.add_info('W', pkg, 'invalid-url', '%s:' % tag, url)

    def _check_lines(self, lines):
        # gather info from spec lines
        self.pkg.current_linenum = 0
        for line in lines:
            self.pkg.current_linenum += 1
            self._check_line(line)
        # Last line read is not useful after this point
        self.pkg.current_linenum = None

    def _check_line(self, line):
        """
        Run check methods for this line.
        """

        self._checkline_break_space(line)
        if self._checkline_section(line):
            return
        self._checkline_buildroot_usage(line)
        self._checkline_make_check(line)
        self._checkline_setup(line)
        self._checkline_autopatch(line)
        self._checkline_applied_patch(line)
        self._checkline_sourcedir(line)
        self._checkline_configure(line)
        self._checkline_hardcoded_library_path(line)
        self._checkline_mklibname(line)
        self._checkline_package(line)
        self._checkline_changelog(line)
        self._checkline_files(line)
        self._checkline_indent(line)
        self._checkline_deprecated_grep(line)
        self._checkline_valid_groups(line)
        self._checkline_macros_in_comments(line)
        self._checkline_python_setup_test(line)

        # If statement, starts
        if ifarch_regex.search(line):
            self.if_depth = self.if_depth + 1
            self.ifarch_depth = self.if_depth
        elif if_regex.search(line):
            self.if_depth = self.if_depth + 1

        # If statement, ends
        elif endif_regex.search(line):
            if self.ifarch_depth == self.if_depth:
                self.ifarch_depth = -1
            self.if_depth = self.if_depth - 1

    # line checks methods

    def _checkline_break_space(self, line):
        char = line.find(UNICODE_NBSP)
        if char != -1:
            self.output.add_info('W', self.pkg, 'non-break-space', 'line %s, char %d' %
                                 (self.pkg.current_linenum, char))

    def _checkline_section(self, line):
        section_marker = False
        for sec, regex in section_regexs.items():
            res = regex.search(line)
            if res:
                self.current_section = sec
                section_marker = True
                self.section[sec] = self.section.get(sec, 0) + 1
                if sec in ('package', 'files'):
                    rest = filelist_regex.sub('', line[res.end() - 1:])
                    res = pkgname_regex.search(rest)
                    if res:
                        self.current_package = res.group(1)
                    else:
                        self.current_package = None
                break

        if section_marker:
            if not self.is_lib_pkg and lib_package_regex.search(line):
                self.is_lib_pkg = True
            return True

    def _checkline_buildroot_usage(self, line):
        if (self.current_section in Pkg.RPM_SCRIPTLETS + ('prep', 'build') and
                contains_buildroot(line)):
            self.output.add_info('E', self.pkg, 'rpm-buildroot-usage', '%' + self.current_section,
                                 line[:-1].strip())

    def _checkline_make_check(self, line):
        if make_check_regex.search(line) and self.current_section not in \
                ('check', 'changelog', 'package', 'description'):
            self.output.add_info('W', self.pkg, 'make-check-outside-check-section',
                                 line[:-1])

    def _checkline_setup(self, line):
        # %setup check
        if setup_regex.match(line):
            if not setup_q_regex.search(line):
                # Don't warn if there's a -T without -a or -b
                if setup_t_regex.search(line):
                    if setup_ab_regex.search(line):
                        self.output.add_info('W', self.pkg, 'setup-not-quiet')
                else:
                    self.output.add_info('W', self.pkg, 'setup-not-quiet')

            if self.current_section != 'prep':
                self.output.add_info('W', self.pkg, 'setup-not-in-prep')
            return

        res = autosetup_regex.search(line)
        if res:
            if not autosetup_n_regex.search(res.group(1)):
                self.patches_auto_applied = True
            if self.current_section != 'prep':
                self.output.add_info('W', self.pkg, '%autosetup-not-in-prep')

    def _checkline_autopatch(self, line):
        # %autopach check
        if autopatch_regex.search(line):
            self.patches_auto_applied = True
            if self.current_section != 'prep':
                self.output.add_info('W', self.pkg, '%autopatch-not-in-prep')

    def _checkline_applied_patch(self, line):
        # Check for %patch -P
        res = applied_patch_regex.search(line)
        if res:
            pnum = res.group(1) or 0
            for tmp in applied_patch_p_regex.findall(line) or [pnum]:
                pnum = int(tmp)
                self.applied_patches.append(pnum)
                if self.ifarch_depth > 0:
                    self.applied_patches_ifarch.append(pnum)
            return

        # Check for %{PATCH0} | patch
        res = applied_patch_pipe_regex.search(line)
        if res:
            pnum = int(res.group(1))
            self.applied_patches.append(pnum)
            if self.ifarch_depth > 0:
                self.applied_patches_ifarch.append(pnum)
            return

        # Check for patch < %{PATCH0}
        res = applied_patch_i_regex.search(line)
        if res:
            pnum = int(res.group(1))
            self.applied_patches.append(pnum)
            if self.ifarch_depth > 0:
                self.applied_patches_ifarch.append(pnum)
            return

    def _checkline_sourcedir(self, line):
        if self.source_dir:
            return

        res = source_dir_regex.search(line)
        if res:
            self.source_dir = True
            self.output.add_info('E', self.pkg, 'use-of-RPM_SOURCE_DIR')

    def _checkline_configure(self, line):
        if self.configure_linenum:
            if self.configure_cmdline[-1] == '\\':
                self.configure_cmdline = self.configure_cmdline[:-1] + line.strip()
            else:
                res = configure_libdir_spec_regex.search(self.configure_cmdline)
                if not res:
                    # Hack to get the correct (start of ./configure) line
                    # number displayed:
                    real_linenum = self.pkg.current_linenum
                    self.pkg.current_linenum = self.configure_linenum
                    self.output.add_info('W', self.pkg, 'configure-without-libdir-spec')
                    self.pkg.current_linenum = real_linenum
                elif res.group(1):
                    res = re.match(hardcoded_library_paths, res.group(1))
                    if res:
                        self.output.add_info('E', self.pkg, 'hardcoded-library-path',
                                             res.group(1), 'in configure options')
                self.configure_linenum = None

        hash_pos = line.find('#')

        if self.current_section != 'changelog':
            cfg_pos = line.find('./configure')
            if cfg_pos != -1 and (hash_pos == -1 or hash_pos > cfg_pos):
                # store line where it started
                self.configure_linenum = self.pkg.current_linenum
                self.configure_cmdline = line.strip()

    def _checkline_hardcoded_library_path(self, line):
        res = hardcoded_library_path_regex.search(line)
        if self.current_section != 'changelog' and res and not \
                (biarch_package_regex.match(self.pkg.name) or
                 self.hardcoded_lib_path_exceptions_regex.search(
                     res.group(1).lstrip())):
            self.output.add_info('E', self.pkg, 'hardcoded-library-path', 'in',
                                 res.group(1).lstrip())

    def _checkline_mklibname(self, line):
        self.mklibname = '%mklibname' in line

    # line checks package methods
    def _checkline_package_patch(self, line):
        # Would be cleaner to get sources and patches from the
        # specfile parsed in Python (see below), but we want to
        # catch %ifarch'd etc ones as well, and also catch these when
        # the specfile is not parseable.
        res = patch_regex.search(line)
        if res:
            pnum = int(res.group(1) or 0)
            self.patches[pnum] = res.group(2)

    def _checkline_package_obsolete_tags(self, line):
        res = obsolete_tags_regex.search(line)
        if res:
            self.output.add_info('W', self.pkg, 'obsolete-tag', res.group(1))

    def _checkline_package_buildroot(self, line):
        res = buildroot_regex.search(line)
        if res:
            self.buildroot = True
            if res.group(1).startswith('/'):
                self.output.add_info('W', self.pkg, 'hardcoded-path-in-buildroot-tag',
                                     res.group(1))

    def _checkline_package_buildarch(self, line):
        res = buildarch_regex.search(line)
        if res:
            if res.group(1) != 'noarch':
                self.output.add_info('E', self.pkg,
                                     'buildarch-instead-of-exclusivearch-tag',
                                     res.group(1))
            else:
                self.package_noarch[self.current_package] = True

    def _checkline_package_packager(self, line):
        res = packager_regex.search(line)
        if res:
            self.output.add_info('W', self.pkg, 'hardcoded-packager-tag', res.group(1))

    def _checkline_package_prefix(self, line):
        res = prefix_regex.search(line)
        if res and not res.group(1).startswith('%'):
            self.output.add_info('W', self.pkg, 'hardcoded-prefix-tag', res.group(1))

    def _checkline_package_suse_prefix(self, line):
        res = suse_version_regex.search(line)
        if res:
            version = int(res.group('version'))
            if version > 0 and version < 1315:
                self.output.add_info('E', self.pkg, 'obsolete-suse-version-check', version)
            elif version > 1550:
                self.output.add_info('E', self.pkg, 'invalid-suse-version-check', version)

    def _checkline_package_prereq(self, line):
        res = prereq_regex.search(line)
        if res:
            self.output.add_info('E', self.pkg, 'prereq-use', res.group(2))

    def _checkline_package_buildprereq(self, line):
        res = buildprereq_regex.search(line)
        if res:
            self.output.add_info('E', self.pkg, 'buildprereq-use', res.group(1))

    def _checkline_package_requires(self, line):
        res = requires_regex.search(line)
        if res:
            reqs = Pkg.parse_deps(res.group(1))
            deptoken = Pkg.has_forbidden_controlchars(reqs)
            if deptoken:
                self.output.add_info('E', self.pkg,
                                     'forbidden-controlchar-found',
                                     f'Requires: {deptoken}')
            for req in unversioned(reqs):
                if compop_regex.search(req):
                    self.output.add_info('W', self.pkg,
                                         'comparison-operator-in-deptoken',
                                         req)

    def _checkline_package_provides(self, line):
        res = provides_regex.search(line)
        if res:
            provs = Pkg.parse_deps(res.group(1))
            deptoken = Pkg.has_forbidden_controlchars(provs)
            if deptoken:
                self.output.add_info('E', self.pkg,
                                     'forbidden-controlchar-found',
                                     f'Provides: {deptoken}')
            for prov in unversioned(provs):
                if not prov.startswith('/'):
                    self.output.add_info('W', self.pkg, 'unversioned-explicit-provides',
                                         prov)
                if compop_regex.search(prov):
                    self.output.add_info('W', self.pkg,
                                         'comparison-operator-in-deptoken',
                                         prov)

    def _checkline_package_obsoletes(self, line):
        res = obsoletes_regex.search(line)
        if res:
            obses = Pkg.parse_deps(res.group(1))
            deptoken = Pkg.has_forbidden_controlchars(obses)
            if deptoken:
                self.output.add_info('E', self.pkg,
                                     'forbidden-controlchar-found',
                                     f'Obsoletes: {deptoken}')
            for obs in unversioned(obses):
                if not obs.startswith('/'):
                    self.output.add_info('W', self.pkg, 'unversioned-explicit-obsoletes',
                                         obs)
                if compop_regex.search(obs):
                    self.output.add_info('W', self.pkg,
                                         'comparison-operator-in-deptoken',
                                         obs)

    def _checkline_package_conflicts(self, line):
        res = conflicts_regex.search(line)
        if res:
            confs = Pkg.parse_deps(res.group(1))
            deptoken = Pkg.has_forbidden_controlchars(confs)
            if deptoken:
                self.output.add_info('E', self.pkg,
                                     'forbidden-controlchar-found',
                                     f'Conflicts: {deptoken}')
            for conf in unversioned(confs):
                if compop_regex.search(conf):
                    self.output.add_info('W', self.pkg,
                                         'comparison-operator-in-deptoken',
                                         conf)

    def _checkline_package(self, line):
        if self.current_section != 'package':
            return

        self._checkline_package_patch(line)
        self._checkline_package_obsolete_tags(line)
        self._checkline_package_buildroot(line)
        self._checkline_package_buildarch(line)
        self._checkline_package_packager(line)
        self._checkline_package_prefix(line)
        self._checkline_package_suse_prefix(line)
        self._checkline_package_prereq(line)
        self._checkline_package_buildprereq(line)
        self._checkline_package_requires(line)
        self._checkline_package_provides(line)
        self._checkline_package_obsoletes(line)
        self._checkline_package_conflicts(line)

    def _checkline_changelog(self, line):
        if self.current_section == 'changelog':
            deptoken = Pkg.has_forbidden_controlchars(line)
            if deptoken:
                self.output.add_info('E', self.pkg,
                                     'forbidden-controlchar-found',
                                     '%%changelog: %s' % deptoken)
            for match in self.macro_regex.findall(line):
                res = re.match('%+', match)
                if len(res.group(0)) % 2 and match != '%autochangelog':
                    self.output.add_info('W', self.pkg, 'macro-in-%changelog', match)
        else:
            if not self.depscript_override:
                self.depscript_override = \
                    depscript_override_regex.search(line) is not None
            if not self.depgen_disabled:
                self.depgen_disabled = \
                    depgen_disable_regex.search(line) is not None
            if not self.patch_fuzz_override:
                self.patch_fuzz_override = \
                    patch_fuzz_override_regex.search(line) is not None

    def _checkline_files(self, line):
        # TODO: check scriptlets for these too?
        if (self.current_section == 'files' and
                (self.package_noarch.get(self.current_package) or
                    (self.current_package not in self.package_noarch and self.package_noarch.get(None)))):
            res = libdir_regex.search(line)
            if res:
                pkgname = self.current_package
                if pkgname is None:
                    pkgname = '(main package)'
                self.output.add_info('W', self.pkg, 'libdir-macro-in-noarch-package',
                                     pkgname, line.rstrip())

    def _checkline_indent(self, line):
        if not self.indent_tabs and '\t' in line:
            self.indent_tabs = self.pkg.current_linenum
        if not self.indent_spaces and indent_spaces_regex.search(line):
            self.indent_spaces = self.pkg.current_linenum

    def _checkline_deprecated_grep(self, line):
        # Check if egrep or fgrep is used
        if self.current_section not in \
                ('package', 'changelog', 'description', 'files'):
            greps = deprecated_grep_regex.findall(line)
            if greps:
                self.output.add_info('W', self.pkg, 'deprecated-grep', greps)

    def _checkline_valid_groups(self, line):
        # If not checking spec file only, we're checking one inside a
        # SRPM -> skip this check to avoid duplicate warnings (#167)

        if self.spec_only and self.valid_groups and \
           line.lower().startswith('group:'):
            group = line[6:].strip()
            if group not in self.valid_groups:
                self.output.add_info('W', self.pkg, 'non-standard-group', group)

    def _checkline_macros_in_comments(self, line):
        hash_pos = line.find('#')
        # Test if there are macros in comments
        if hash_pos != -1 and \
                (hash_pos == 0 or line[hash_pos - 1] in (' ', '\t')):
            for match in self.macro_regex.findall(
                    line[hash_pos + 1:]):
                res = re.match('%+', match)
                if len(res.group(0)) % 2:
                    self.output.add_info('W', self.pkg, 'macro-in-comment', match)

    def _checkline_python_setup_test(self, line):
        # Test if the "python setup.py test" deprecated subcommand is used
        if self.current_section == 'check' and python_setup_test_regex.search(line):
            self.output.add_info('W', self.pkg, 'python-setup-test', line[:-1])
