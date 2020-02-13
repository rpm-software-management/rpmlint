#############################################################################
# File          : SpecCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Thu Oct  7 17:06:14 1999
# Purpose       : check the spec file of a source rpm.
#############################################################################

from pathlib import Path
import re
import subprocess
from urllib.parse import urlparse

import rpm
from rpmlint import pkg as Pkg
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import readlines

# Don't check for hardcoded library paths in biarch packages
DEFAULT_BIARCH_PACKAGES = '^(gcc|glibc)'


def re_tag_compile(tag):
    r = r'^%s\s*:\s*(\S.*?)\s*$' % tag
    return re.compile(r, re.IGNORECASE)


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

make_check_regex = re.compile(r'(^|\s|%{?__)make}?\s+(check|test)')
rm_regex = re.compile(r'(^|\s)((.*/)?rm|%{?__rm}?) ')
rpm_buildroot_regex = re.compile(r'^[^#]*(?:(\\\*)\${?RPM_BUILD_ROOT}?|(%+){?buildroot}?)')
configure_libdir_spec_regex = re.compile(r'ln |\./configure[^#]*--libdir=(\S+)[^#]*')
lib_package_regex = re.compile(r'^%package.*\Wlib')
ifarch_regex = re.compile(r'^\s*%ifn?arch\s')
if_regex = re.compile(r'^\s*%if\s')
endif_regex = re.compile(r'^\s*%endif\b')
biarch_package_regex = re.compile(DEFAULT_BIARCH_PACKAGES)
libdir_regex = re.compile(r'%{?_lib(?:dir)?\}?\b')
section_regexs = dict(
    ([x, re.compile('^%' + x + r'(?:\s|$)')]
     for x in ('build', 'changelog', 'check', 'clean', 'description', 'files',
               'install', 'package', 'prep') + Pkg.RPM_SCRIPTLETS))
deprecated_grep_regex = re.compile(r'\b[ef]grep\b')

# Only check for /lib, /usr/lib, /usr/X11R6/lib
# TODO: better handling of X libraries and modules.
hardcoded_library_paths = '(/lib|/usr/lib|/usr/X11R6/lib/(?!([^/]+/)+)[^/]*\\.([oa]|la|so[0-9.]*))'
hardcoded_library_path_regex = re.compile(r'^[^#]*((^|\s+|\.\./\.\.|\${?RPM_BUILD_ROOT}?|%{?buildroot}?|%{?_prefix}?)' + hardcoded_library_paths + r'(?=[\s;/])([^\s,;]*))')

# Requires(pre,post) is broken in some rpm versions, see
# https://bugzilla.redhat.com/118780 and bugs linked to that one.
scriptlet_requires_regex = re.compile(r'^(PreReq|Requires)\([^\)]*,', re.IGNORECASE)

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

UNICODE_NBSP = u'\xa0'


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

    def __init__(self, config, output):
        super().__init__(config, output)
        self._spec_file = None
        self._spec_name = None
        self.valid_groups = config.configuration['ValidGroups']
        self.output.error_details.update({'non-standard-group':
                                         """The value of the Group tag in the package is not valid.  Valid groups are:
                                         '%s'.""" % ', '.join(self.valid_groups)})
        self.hardcoded_lib_path_exceptions_regex = re.compile(config.configuration['HardcodedLibPathExceptions'])

    def check_source(self, pkg):
        wrong_spec = False

        # lookup spec file
        for fname, pkgfile in pkg.files().items():
            if fname.endswith('.spec'):
                self._spec_file = pkgfile.path
                self._spec_name = pkgfile.name
                if fname == pkg.name + '.spec':
                    wrong_spec = False
                    break
                else:
                    wrong_spec = True
        if not self._spec_file:
            self.output.add_info('E', pkg, 'no-spec-file')
        else:
            if wrong_spec:
                self.output.add_info('E', pkg, 'invalid-spec-name')

            # check content of spec file
            with Pkg.FakePkg(self._spec_file) as package:
                self.check_spec(package)

    def check_spec(self, pkg):
        self._spec_file = pkg.name
        spec_only = isinstance(pkg, Pkg.FakePkg)
        spec_lines = readlines(self._spec_file)
        patches = {}
        applied_patches = []
        applied_patches_ifarch = []
        patches_auto_applied = False
        source_dir = False
        buildroot = False
        configure_linenum = None
        configure_cmdline = ''
        mklibname = False
        is_lib_pkg = False
        if_depth = 0
        ifarch_depth = -1
        current_section = 'package'
        buildroot_clean = {'clean': False, 'install': False}
        depscript_override = False
        depgen_disabled = False
        patch_fuzz_override = False
        indent_spaces = 0
        indent_tabs = 0
        section = {}
        # None == main package
        current_package = None
        package_noarch = {}

        if self._spec_file:
            if not Pkg.is_utf8(self._spec_file):
                self.output.add_info('E', pkg, 'non-utf8-spec-file',
                                     self._spec_name or self._spec_file)

        # gather info from spec lines

        pkg.current_linenum = 0

        nbsp = UNICODE_NBSP

        for line in spec_lines:

            pkg.current_linenum += 1

            char = line.find(nbsp)
            if char != -1:
                self.output.add_info('W', pkg, 'non-break-space', 'line %s, char %d' %
                                     (pkg.current_linenum, char))

            section_marker = False
            for sec, regex in section_regexs.items():
                res = regex.search(line)
                if res:
                    current_section = sec
                    section_marker = True
                    section[sec] = section.get(sec, 0) + 1
                    if sec in ('package', 'files'):
                        rest = filelist_regex.sub('', line[res.end() - 1:])
                        res = pkgname_regex.search(rest)
                        if res:
                            current_package = res.group(1)
                        else:
                            current_package = None
                    break

            if section_marker:

                if not is_lib_pkg and lib_package_regex.search(line):
                    is_lib_pkg = True

                continue

            if (current_section in Pkg.RPM_SCRIPTLETS + ('prep', 'build') and
                    contains_buildroot(line)):
                self.output.add_info('W', pkg, 'rpm-buildroot-usage', '%' + current_section,
                                     line[:-1].strip())

            if make_check_regex.search(line) and current_section not in \
                    ('check', 'changelog', 'package', 'description'):
                self.output.add_info('W', pkg, 'make-check-outside-check-section',
                                     line[:-1])

            if current_section in buildroot_clean and \
                    not buildroot_clean[current_section] and \
                    contains_buildroot(line) and rm_regex.search(line):
                buildroot_clean[current_section] = True

            if ifarch_regex.search(line):
                if_depth = if_depth + 1
                ifarch_depth = if_depth

            if if_regex.search(line):
                if_depth = if_depth + 1

            if setup_regex.match(line):
                if not setup_q_regex.search(line):
                    # Don't warn if there's a -T without -a or -b
                    if setup_t_regex.search(line):
                        if setup_ab_regex.search(line):
                            self.output.add_info('W', pkg, 'setup-not-quiet')
                    else:
                        self.output.add_info('W', pkg, 'setup-not-quiet')
                if current_section != 'prep':
                    self.output.add_info('W', pkg, 'setup-not-in-prep')
            elif autopatch_regex.search(line):
                patches_auto_applied = True
                if current_section != 'prep':
                    self.output.add_info('W', pkg, '%autopatch-not-in-prep')
            else:
                res = autosetup_regex.search(line)
                if res:
                    if not autosetup_n_regex.search(res.group(1)):
                        patches_auto_applied = True
                    if current_section != 'prep':
                        self.output.add_info('W', pkg, '%autosetup-not-in-prep')

            if endif_regex.search(line):
                if ifarch_depth == if_depth:
                    ifarch_depth = -1
                if_depth = if_depth - 1

            res = applied_patch_regex.search(line)
            if res:
                pnum = res.group(1) or 0
                for tmp in applied_patch_p_regex.findall(line) or [pnum]:
                    pnum = int(tmp)
                    applied_patches.append(pnum)
                    if ifarch_depth > 0:
                        applied_patches_ifarch.append(pnum)
            else:
                res = applied_patch_pipe_regex.search(line)
                if res:
                    pnum = int(res.group(1))
                    applied_patches.append(pnum)
                    if ifarch_depth > 0:
                        applied_patches_ifarch.append(pnum)
                else:
                    res = applied_patch_i_regex.search(line)
                    if res:
                        pnum = int(res.group(1))
                        applied_patches.append(pnum)
                        if ifarch_depth > 0:
                            applied_patches_ifarch.append(pnum)
            if not res and not source_dir:
                res = source_dir_regex.search(line)
                if res:
                    source_dir = True
                    self.output.add_info('E', pkg, 'use-of-RPM_SOURCE_DIR')

            if configure_linenum:
                if configure_cmdline[-1] == '\\':
                    configure_cmdline = configure_cmdline[:-1] + line.strip()
                else:
                    res = configure_libdir_spec_regex.search(configure_cmdline)
                    if not res:
                        # Hack to get the correct (start of ./configure) line
                        # number displayed:
                        real_linenum = pkg.current_linenum
                        pkg.current_linenum = configure_linenum
                        self.output.add_info('W', pkg, 'configure-without-libdir-spec')
                        pkg.current_linenum = real_linenum
                    elif res.group(1):
                        res = re.match(hardcoded_library_paths, res.group(1))
                        if res:
                            self.output.add_info('E', pkg, 'hardcoded-library-path',
                                                 res.group(1), 'in configure options')
                    configure_linenum = None

            hashPos = line.find('#')

            if current_section != 'changelog':
                cfgPos = line.find('./configure')
                if cfgPos != -1 and (hashPos == -1 or hashPos > cfgPos):
                    # store line where it started
                    configure_linenum = pkg.current_linenum
                    configure_cmdline = line.strip()

            res = hardcoded_library_path_regex.search(line)
            if current_section != 'changelog' and res and not \
                    (biarch_package_regex.match(pkg.name) or
                     self.hardcoded_lib_path_exceptions_regex.search(
                         res.group(1).lstrip())):
                self.output.add_info('E', pkg, 'hardcoded-library-path', 'in',
                                     res.group(1).lstrip())

            if '%mklibname' in line:
                mklibname = True

            if current_section == 'package':

                # Would be cleaner to get sources and patches from the
                # specfile parsed in Python (see below), but we want to
                # catch %ifarch'd etc ones as well, and also catch these when
                # the specfile is not parseable.

                res = patch_regex.search(line)
                if res:
                    pnum = int(res.group(1) or 0)
                    patches[pnum] = res.group(2)

                res = obsolete_tags_regex.search(line)
                if res:
                    self.output.add_info('W', pkg, 'obsolete-tag', res.group(1))

                res = buildroot_regex.search(line)
                if res:
                    buildroot = True
                    if res.group(1).startswith('/'):
                        self.output.add_info('W', pkg, 'hardcoded-path-in-buildroot-tag',
                                             res.group(1))

                res = buildarch_regex.search(line)
                if res:
                    if res.group(1) != 'noarch':
                        self.output.add_info('E', pkg,
                                             'buildarch-instead-of-exclusivearch-tag',
                                             res.group(1))
                    else:
                        package_noarch[current_package] = True

                res = packager_regex.search(line)
                if res:
                    self.output.add_info('W', pkg, 'hardcoded-packager-tag', res.group(1))

                res = prefix_regex.search(line)
                if res:
                    if not res.group(1).startswith('%'):
                        self.output.add_info('W', pkg, 'hardcoded-prefix-tag', res.group(1))

                res = prereq_regex.search(line)
                if res:
                    self.output.add_info('E', pkg, 'prereq-use', res.group(2))

                res = buildprereq_regex.search(line)
                if res:
                    self.output.add_info('E', pkg, 'buildprereq-use', res.group(1))

                if scriptlet_requires_regex.search(line):
                    self.output.add_info('E', pkg, 'broken-syntax-in-scriptlet-requires',
                                         line.strip())

                res = requires_regex.search(line)
                if res:
                    reqs = Pkg.parse_deps(res.group(1))
                    e = Pkg.has_forbidden_controlchars(reqs)
                    if e:
                        self.output.add_info('E', pkg,
                                             'forbidden-controlchar-found',
                                             'Requires: %s' % e)
                    for req in unversioned(reqs):
                        if compop_regex.search(req):
                            self.output.add_info('W', pkg,
                                                 'comparison-operator-in-deptoken',
                                                 req)

                res = provides_regex.search(line)
                if res:
                    provs = Pkg.parse_deps(res.group(1))
                    e = Pkg.has_forbidden_controlchars(provs)
                    if e:
                        self.output.add_info('E', pkg,
                                             'forbidden-controlchar-found',
                                             'Provides: %s' % e)
                    for prov in unversioned(provs):
                        if not prov.startswith('/'):
                            self.output.add_info('W', pkg, 'unversioned-explicit-provides',
                                                 prov)
                        if compop_regex.search(prov):
                            self.output.add_info('W', pkg,
                                                 'comparison-operator-in-deptoken',
                                                 prov)

                res = obsoletes_regex.search(line)
                if res:
                    obses = Pkg.parse_deps(res.group(1))
                    e = Pkg.has_forbidden_controlchars(obses)
                    if e:
                        self.output.add_info('E', pkg,
                                             'forbidden-controlchar-found',
                                             'Obsoletes: %s' % e)
                    for obs in unversioned(obses):
                        if not obs.startswith('/'):
                            self.output.add_info('W', pkg, 'unversioned-explicit-obsoletes',
                                                 obs)
                        if compop_regex.search(obs):
                            self.output.add_info('W', pkg,
                                                 'comparison-operator-in-deptoken',
                                                 obs)

                res = conflicts_regex.search(line)
                if res:
                    confs = Pkg.parse_deps(res.group(1))
                    e = Pkg.has_forbidden_controlchars(confs)
                    if e:
                        self.output.add_info('E', pkg,
                                             'forbidden-controlchar-found',
                                             'Conflicts: %s' % e)
                    for conf in unversioned(confs):
                        if compop_regex.search(conf):
                            self.output.add_info('W', pkg,
                                                 'comparison-operator-in-deptoken',
                                                 conf)

            if current_section == 'changelog':
                e = Pkg.has_forbidden_controlchars(line)
                if e:
                    self.output.add_info('E', pkg,
                                         'forbidden-controlchar-found',
                                         '%%changelog: %s' % e)
                for match in self.macro_regex.findall(line):
                    res = re.match('%+', match)
                    if len(res.group(0)) % 2:
                        self.output.add_info('W', pkg, 'macro-in-%changelog', match)
            else:
                if not depscript_override:
                    depscript_override = \
                        depscript_override_regex.search(line) is not None
                if not depgen_disabled:
                    depgen_disabled = \
                        depgen_disable_regex.search(line) is not None
                if not patch_fuzz_override:
                    patch_fuzz_override = \
                        patch_fuzz_override_regex.search(line) is not None

            if current_section == 'files':
                # TODO: check scriptlets for these too?
                if package_noarch.get(current_package) or \
                        (current_package not in package_noarch and
                         package_noarch.get(None)):
                    res = libdir_regex.search(line)
                    if res:
                        pkgname = current_package
                        if pkgname is None:
                            pkgname = '(main package)'
                        self.output.add_info('W', pkg, 'libdir-macro-in-noarch-package',
                                             pkgname, line.rstrip())

            if not indent_tabs and '\t' in line:
                indent_tabs = pkg.current_linenum
            if not indent_spaces and indent_spaces_regex.search(line):
                indent_spaces = pkg.current_linenum

            # Check if egrep or fgrep is used
            if current_section not in \
                    ('package', 'changelog', 'description', 'files'):
                greps = deprecated_grep_regex.findall(line)
                if greps:
                    self.output.add_info('W', pkg, 'deprecated-grep', greps)

            # If not checking spec file only, we're checking one inside a
            # SRPM -> skip this check to avoid duplicate warnings (#167)
            if spec_only and self.valid_groups and \
               line.lower().startswith('group:'):
                group = line[6:].strip()
                if group not in self.valid_groups:
                    self.output.add_info('W', pkg, 'non-standard-group', group)

            # Test if there are macros in comments
            if hashPos != -1 and \
                    (hashPos == 0 or line[hashPos - 1] in (' ', '\t')):
                for match in self.macro_regex.findall(
                        line[hashPos + 1:]):
                    res = re.match('%+', match)
                    if len(res.group(0)) % 2:
                        self.output.add_info('W', pkg, 'macro-in-comment', match)

        # Last line read is not useful after this point
        pkg.current_linenum = None

        for sect in (x for x in buildroot_clean if not buildroot_clean[x]):
            self.output.add_info('W', pkg, 'no-cleaning-of-buildroot', '%' + sect)

        if not buildroot:
            self.output.add_info('W', pkg, 'no-buildroot-tag')

        for sec in ('prep', 'build', 'install', 'clean'):
            if not section.get(sec):
                self.output.add_info('W', pkg, 'no-%%%s-section' % sec)
        for sec in ('changelog',):
            # prep, build, install, clean, check prevented by rpmbuild 4.4
            if section.get(sec, 0) > 1:
                self.output.add_info('W', pkg, 'more-than-one-%%%s-section' % sec)

        if is_lib_pkg and not mklibname:
            self.output.add_info('E', pkg, 'lib-package-without-%mklibname')

        if depscript_override and not depgen_disabled:
            self.output.add_info('W', pkg, 'depscript-without-disabling-depgen')

        if patch_fuzz_override:
            self.output.add_info('W', pkg, 'patch-fuzz-is-changed')

        if indent_spaces and indent_tabs:
            pkg.current_linenum = max(indent_spaces, indent_tabs)
            self.output.add_info('W', pkg, 'mixed-use-of-spaces-and-tabs',
                                 '(spaces: line %d, tab: line %d)' %
                                 (indent_spaces, indent_tabs))
            pkg.current_linenum = None

        # process gathered info
        if not patches_auto_applied:
            for pnum, pfile in patches.items():
                if pnum in applied_patches_ifarch:
                    self.output.add_info('W', pkg, '%ifarch-applied-patch',
                                         'Patch%d:' % pnum, pfile)
                if pnum not in applied_patches:
                    self.output.add_info('W', pkg, 'patch-not-applied',
                                         'Patch%d:' % pnum, pfile)

        # Rest of the checks require a real spec file
        if not self._spec_file:
            return

        # We'd like to parse the specfile only once using python bindings,
        # but it seems errors from rpmlib get logged to stderr and we can't
        # capture and print them nicely, so we do it once each way :P

        outcmd = subprocess.run(
            ('rpm', '-q', '--qf=', '-D', '_sourcedir %s' % Path(self._spec_file).parent, '--specfile', self._spec_file), stdout=subprocess.PIPE)
        text = outcmd.stdout.decode()
        if text.endswith('\n'):
            text = text[:-1]

        parse_error = False
        for line in text.splitlines():
            # No such file or dir hack: https://bugzilla.redhat.com/487855
            if 'No such file or directory' not in line:
                parse_error = True
                self.output.add_info('E', pkg, 'specfile-error', line)

        if not parse_error:
            # grab sources and patches from parsed spec object to get
            # them with macros expanded for URL checking

            spec_obj = None
            rpm.addMacro('_sourcedir', pkg.dirName())
            try:
                ts = rpm.TransactionSet()
                spec_obj = ts.parseSpec(str(self._spec_file))
            except (ValueError, rpm.error):
                # errors logged above already
                pass
            rpm.delMacro('_sourcedir')
            if spec_obj:
                try:
                    # rpm < 4.8.0
                    sources = spec_obj.sources()
                except TypeError:
                    # rpm >= 4.8.0
                    sources = spec_obj.sources
                for src in sources:
                    (url, num, flags) = src
                    (scheme, netloc) = urlparse(url)[0:2]
                    if flags & 1:  # rpmspec.h, rpm.org ticket #123
                        srctype = 'Source'
                    else:
                        srctype = 'Patch'
                    tag = '%s%s' % (srctype, num)
                    if scheme and netloc:
                        continue
                    elif srctype == 'Source' and tarball_regex.search(url):
                        self.output.add_info('W', pkg, 'invalid-url', '%s:' % tag, url)
