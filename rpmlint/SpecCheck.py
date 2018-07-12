# -*- coding: utf-8 -*-
#############################################################################
# File          : SpecCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Thu Oct  7 17:06:14 1999
# Purpose       : check the spec file of a source rpm.
#############################################################################

import re
import sys
try:
    from urlparse import urlparse
except ImportError:  # Python 3
    from urllib.parse import urlparse

import rpm

import rpmlint.AbstractCheck as AbstractCheck
import rpmlint.Config as Config
import rpmlint.Pkg as Pkg
from rpmlint.Filter import addDetails, printError, printWarning
from rpmlint.TagsCheck import VALID_GROUPS

# Don't check for hardcoded library paths in biarch packages
DEFAULT_BIARCH_PACKAGES = '^(gcc|glibc)'

# Don't check for hardcoded library paths in packages which can have
# their noarch files in /usr/lib/<package>/*, or packages that can't
# be installed on biarch systems
DEFAULT_HARDCODED_LIB_PATH_EXCEPTIONS = r'/lib/(modules|cpp|perl5|rpm|hotplug|firmware|systemd)($|[\s/,])'


def re_tag_compile(tag):
    r = r"^%s\s*:\s*(\S.*?)\s*$" % tag
    return re.compile(r, re.IGNORECASE)


patch_regex = re_tag_compile(r'Patch(\d*)')
applied_patch_regex = re.compile(r"^%patch(\d*)")
applied_patch_p_regex = re.compile(r"\s-P\s+(\d+)\b")
applied_patch_pipe_regex = re.compile(r'\s%\{PATCH(\d+)\}\s*\|\s*(%\{?__)?patch\b')
applied_patch_i_regex = re.compile(r"(?:%\{?__)?patch\}?.*?\s+(?:<|-i)\s+%\{PATCH(\d+)\}")
source_dir_regex = re.compile(r"^[^#]*(\$RPM_SOURCE_DIR|%{?_sourcedir}?)")
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
hardcoded_lib_path_exceptions_regex = re.compile(Config.getOption('HardcodedLibPathExceptions', DEFAULT_HARDCODED_LIB_PATH_EXCEPTIONS))
use_utf8 = Config.getOption('UseUTF8', Config.USEUTF8_DEFAULT)
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
    '''Yield unversioned dependency names from the given list.'''
    for dep in deps:
        if not dep[1]:
            yield dep[0]


def contains_buildroot(line):
    '''Check if the given line contains use of rpm buildroot.'''
    res = rpm_buildroot_regex.search(line)
    if res and \
       (not res.group(1) or len(res.group(1)) % 2 == 0) and \
       (not res.group(2) or len(res.group(2)) % 2 != 0):
        return True
    return False


class SpecCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "SpecCheck")
        self._spec_file = None
        self._spec_name = None

    def check_source(self, pkg):
        wrong_spec = False

        # lookup spec file
        for fname, pkgfile in pkg.files().items():
            if fname.endswith('.spec'):
                self._spec_file = pkgfile.path
                self._spec_name = pkgfile.name
                if fname == pkg.name + ".spec":
                    wrong_spec = False
                    break
                else:
                    wrong_spec = True
        if not self._spec_file:
            printError(pkg, "no-spec-file")
        else:
            if wrong_spec:
                printError(pkg, "invalid-spec-name")

            # check content of spec file
            self.check_spec(pkg, self._spec_file)

    def check_spec(self, pkg, spec_file, spec_lines=None):
        self._spec_file = spec_file
        spec_only = isinstance(pkg, Pkg.FakePkg)
        if not spec_lines:
            spec_lines = Pkg.readlines(spec_file)
        patches = {}
        applied_patches = []
        applied_patches_ifarch = []
        patches_auto_applied = False
        source_dir = False
        buildroot = False
        configure_linenum = None
        configure_cmdline = ""
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

        is_utf8 = False
        if self._spec_file and use_utf8:
            if Pkg.is_utf8(self._spec_file):
                is_utf8 = True
            else:
                printError(pkg, "non-utf8-spec-file",
                           self._spec_name or self._spec_file)

        # gather info from spec lines

        pkg.current_linenum = 0

        nbsp = UNICODE_NBSP if is_utf8 else chr(0xA0)
        do_unicode = is_utf8 and sys.version_info[0] <= 2

        for line in spec_lines:

            pkg.current_linenum += 1

            if do_unicode:
                line = unicode(line, "utf-8", "replace")  # noqa false positive

            char = line.find(nbsp)
            if char != -1:
                printWarning(pkg, "non-break-space", "line %s, char %d" %
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
                printWarning(pkg, 'rpm-buildroot-usage', '%' + current_section,
                             line[:-1].strip())

            if make_check_regex.search(line) and current_section not in \
                    ('check', 'changelog', 'package', 'description'):
                printWarning(pkg, 'make-check-outside-check-section',
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
                            printWarning(pkg, 'setup-not-quiet')
                    else:
                        printWarning(pkg, 'setup-not-quiet')
                if current_section != 'prep':
                    printWarning(pkg, 'setup-not-in-prep')
            elif autopatch_regex.search(line):
                patches_auto_applied = True
                if current_section != 'prep':
                    printWarning(pkg, '%autopatch-not-in-prep')
            else:
                res = autosetup_regex.search(line)
                if res:
                    if not autosetup_n_regex.search(res.group(1)):
                        patches_auto_applied = True
                    if current_section != 'prep':
                        printWarning(pkg, '%autosetup-not-in-prep')

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
                    printError(pkg, "use-of-RPM_SOURCE_DIR")

            if configure_linenum:
                if configure_cmdline[-1] == "\\":
                    configure_cmdline = configure_cmdline[:-1] + line.strip()
                else:
                    res = configure_libdir_spec_regex.search(configure_cmdline)
                    if not res:
                        # Hack to get the correct (start of ./configure) line
                        # number displayed:
                        real_linenum = pkg.current_linenum
                        pkg.current_linenum = configure_linenum
                        printWarning(pkg, "configure-without-libdir-spec")
                        pkg.current_linenum = real_linenum
                    elif res.group(1):
                        res = re.match(hardcoded_library_paths, res.group(1))
                        if res:
                            printError(pkg, "hardcoded-library-path",
                                       res.group(1), "in configure options")
                    configure_linenum = None

            hashPos = line.find("#")

            if current_section != 'changelog':
                cfgPos = line.find('./configure')
                if cfgPos != -1 and (hashPos == -1 or hashPos > cfgPos):
                    # store line where it started
                    configure_linenum = pkg.current_linenum
                    configure_cmdline = line.strip()

            res = hardcoded_library_path_regex.search(line)
            if current_section != 'changelog' and res and not \
                    (biarch_package_regex.match(pkg.name) or
                     hardcoded_lib_path_exceptions_regex.search(
                         res.group(1).lstrip())):
                printError(pkg, "hardcoded-library-path", "in",
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
                    printWarning(pkg, "obsolete-tag", res.group(1))

                res = buildroot_regex.search(line)
                if res:
                    buildroot = True
                    if res.group(1).startswith('/'):
                        printWarning(pkg, 'hardcoded-path-in-buildroot-tag',
                                     res.group(1))

                res = buildarch_regex.search(line)
                if res:
                    if res.group(1) != "noarch":
                        printError(pkg,
                                   'buildarch-instead-of-exclusivearch-tag',
                                   res.group(1))
                    else:
                        package_noarch[current_package] = True

                res = packager_regex.search(line)
                if res:
                    printWarning(pkg, 'hardcoded-packager-tag', res.group(1))

                res = prefix_regex.search(line)
                if res:
                    if not res.group(1).startswith('%'):
                        printWarning(pkg, 'hardcoded-prefix-tag', res.group(1))

                res = prereq_regex.search(line)
                if res:
                    printError(pkg, 'prereq-use', res.group(2))

                res = buildprereq_regex.search(line)
                if res:
                    printError(pkg, 'buildprereq-use', res.group(1))

                if scriptlet_requires_regex.search(line):
                    printError(pkg, 'broken-syntax-in-scriptlet-requires',
                               line.strip())

                res = requires_regex.search(line)
                if res:
                    reqs = Pkg.parse_deps(res.group(1))
                    for req in unversioned(reqs):
                        if compop_regex.search(req):
                            printWarning(pkg,
                                         'comparison-operator-in-deptoken',
                                         req)

                res = provides_regex.search(line)
                if res:
                    provs = Pkg.parse_deps(res.group(1))
                    for prov in unversioned(provs):
                        if not prov.startswith('/'):
                            printWarning(pkg, 'unversioned-explicit-provides',
                                         prov)
                        if compop_regex.search(prov):
                            printWarning(pkg,
                                         'comparison-operator-in-deptoken',
                                         prov)

                res = obsoletes_regex.search(line)
                if res:
                    obses = Pkg.parse_deps(res.group(1))
                    for obs in unversioned(obses):
                        if not obs.startswith('/'):
                            printWarning(pkg, 'unversioned-explicit-obsoletes',
                                         obs)
                        if compop_regex.search(obs):
                            printWarning(pkg,
                                         'comparison-operator-in-deptoken',
                                         obs)

                res = conflicts_regex.search(line)
                if res:
                    confs = Pkg.parse_deps(res.group(1))
                    for conf in unversioned(confs):
                        if compop_regex.search(conf):
                            printWarning(pkg,
                                         'comparison-operator-in-deptoken',
                                         conf)

            if current_section == 'changelog':
                for match in AbstractCheck.macro_regex.findall(line):
                    res = re.match('%+', match)
                    if len(res.group(0)) % 2:
                        printWarning(pkg, 'macro-in-%changelog', match)
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
                        printWarning(pkg, 'libdir-macro-in-noarch-package',
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
                    printWarning(pkg, "deprecated-grep", greps)

            # If not checking spec file only, we're checking one inside a
            # SRPM -> skip this check to avoid duplicate warnings (#167)
            if spec_only and VALID_GROUPS and \
               line.lower().startswith("group:"):
                group = line[6:].strip()
                if group not in VALID_GROUPS:
                    printWarning(pkg, 'non-standard-group', group)

            # Test if there are macros in comments
            if hashPos != -1 and \
                    (hashPos == 0 or line[hashPos - 1] in (" ", "\t")):
                for match in AbstractCheck.macro_regex.findall(
                        line[hashPos + 1:]):
                    res = re.match('%+', match)
                    if len(res.group(0)) % 2:
                        printWarning(pkg, 'macro-in-comment', match)

        # Last line read is not useful after this point
        pkg.current_linenum = None

        for sect in (x for x in buildroot_clean if not buildroot_clean[x]):
            printWarning(pkg, 'no-cleaning-of-buildroot', '%' + sect)

        if not buildroot:
            printWarning(pkg, 'no-buildroot-tag')

        for sec in ('prep', 'build', 'install', 'clean'):
            if not section.get(sec):
                printWarning(pkg, 'no-%%%s-section' % sec)
        for sec in ('changelog',):
            # prep, build, install, clean, check prevented by rpmbuild 4.4
            if section.get(sec, 0) > 1:
                printWarning(pkg, 'more-than-one-%%%s-section' % sec)

        if is_lib_pkg and not mklibname:
            printError(pkg, 'lib-package-without-%mklibname')

        if depscript_override and not depgen_disabled:
            printWarning(pkg, 'depscript-without-disabling-depgen')

        if patch_fuzz_override:
            printWarning(pkg, 'patch-fuzz-is-changed')

        if indent_spaces and indent_tabs:
            pkg.current_linenum = max(indent_spaces, indent_tabs)
            printWarning(pkg, 'mixed-use-of-spaces-and-tabs',
                         '(spaces: line %d, tab: line %d)' %
                         (indent_spaces, indent_tabs))
            pkg.current_linenum = None

        # process gathered info
        if not patches_auto_applied:
            for pnum, pfile in patches.items():
                if pnum in applied_patches_ifarch:
                    printWarning(pkg, "%ifarch-applied-patch",
                                 "Patch%d:" % pnum, pfile)
                if pnum not in applied_patches:
                    printWarning(pkg, "patch-not-applied",
                                 "Patch%d:" % pnum, pfile)

        # Rest of the checks require a real spec file
        if not self._spec_file:
            return

        # We'd like to parse the specfile only once using python bindings,
        # but it seems errors from rpmlib get logged to stderr and we can't
        # capture and print them nicely, so we do it once each way :P

        out = Pkg.getstatusoutput(
            ('rpm', '-q', '--qf=', '-D', '_sourcedir %s' % pkg.dirName(), '--specfile', self._spec_file))
        parse_error = False
        for line in out[1].splitlines():
            # No such file or dir hack: https://bugzilla.redhat.com/487855
            if 'No such file or directory' not in line:
                parse_error = True
                printError(pkg, 'specfile-error', line)

        if not parse_error:
            # grab sources and patches from parsed spec object to get
            # them with macros expanded for URL checking

            spec_obj = None
            rpm.addMacro('_sourcedir', pkg.dirName())
            try:
                ts = rpm.TransactionSet()
                spec_obj = ts.parseSpec(self._spec_file)
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
                        srctype = "Source"
                    else:
                        srctype = "Patch"
                    tag = '%s%s' % (srctype, num)
                    if scheme and netloc:
                        info = self.check_url(pkg, tag, url)
                        if not info or not hasattr(pkg, 'files'):
                            continue
                        clen = info.get("Content-Length")
                        if clen is not None:
                            clen = int(clen)
                        cmd5 = info.get("Content-MD5")
                        if cmd5 is not None:
                            cmd5 = cmd5.lower()
                        if clen is not None or cmd5 is not None:
                            # Not using path from urlparse results to match how
                            # rpm itself parses the basename.
                            pkgfile = pkg.files().get(url.split("/")[-1])
                            if pkgfile:
                                if clen is not None and pkgfile.size != clen:
                                    printWarning(pkg, 'file-size-mismatch',
                                                 '%s = %s, %s = %s' %
                                                 (pkgfile.name, pkgfile.size,
                                                  url, clen))
                                # pkgfile.md5 could be some other digest than
                                # MD5, treat as MD5 only if it's 32 chars long
                                if cmd5 and len(pkgfile.md5) == 32 \
                                        and pkgfile.md5 != cmd5:
                                    printWarning(pkg, 'file-md5-mismatch',
                                                 '%s = %s, %s = %s' %
                                                 (pkgfile.name, pkgfile.md5,
                                                  url, cmd5))
                    elif srctype == "Source" and tarball_regex.search(url):
                        printWarning(pkg, 'invalid-url', '%s:' % tag, url)


# Create an object to enable the auto registration of the test
check = SpecCheck()

# Add information about checks
addDetails(
'no-spec-file',
'''No spec file was specified in your RPM building. Please specify a valid
SPEC file to build a valid RPM package.''',

'invalid-spec-name',
'''The spec file name (without the .spec suffix) must match the package name
("Name:" tag). Either rename your package or the specfile.''',

'non-utf8-spec-file',
'''The character encoding of the spec file is not UTF-8.  Convert it for
example using iconv(1).''',

'use-of-RPM_SOURCE_DIR',
'''You use $RPM_SOURCE_DIR or %{_sourcedir} in your spec file. If you have to
use a directory for building, use $RPM_BUILD_ROOT instead.''',

'patch-not-applied',
'''A patch is included in your package but was not applied. Refer to the
patches documentation to see what's wrong.''',

'obsolete-tag',
'''The following tags are obsolete: Copyright and Serial. They must
be replaced by License and Epoch respectively.''',

'deprecated-grep',
'''Direct use of grep as egrep or fgrep is deprecated in GNU grep and
historical in POSIX, use grep -E and grep -F instead.''',

'no-buildroot-tag',
'''The BuildRoot tag isn't used in your spec. It must be used in order to
allow building the package as non root on some systems. For some rpm versions
(e.g. rpm.org >= 4.6) the BuildRoot tag is not necessary in specfiles and is
ignored by rpmbuild; if your package is only going to be built with such rpm
versions you can ignore this warning.''',

'hardcoded-path-in-buildroot-tag',
'''A path is hardcoded in your Buildroot tag. It should be replaced
by something like %{_tmppath}/%{name}-%{version}-build.''',

'hardcoded-packager-tag',
'''The Packager tag is hardcoded in your spec file. It should be removed, so
as to use rebuilder's own defaults.''',

'buildarch-instead-of-exclusivearch-tag',
'''Use ExclusiveArch instead of BuildArch (or BuildArchitectures)
to restrict build on some specific architectures.
Only use BuildArch with noarch''',

'hardcoded-prefix-tag',
'''The Prefix tag is hardcoded in your spec file. It should be removed, so as
to allow package relocation.''',

'hardcoded-library-path',
'''A library path is hardcoded to one of the following paths: /lib,
/usr/lib. It should be replaced by something like /%{_lib} or %{_libdir}.''',

'configure-without-libdir-spec',
'''A configure script is run without specifying the libdir. configure
options must be augmented with something like --libdir=%{_libdir} whenever
the script supports it.''',

'no-%prep-section',
'''The spec file does not contain a %prep section.  Even if some packages don't
directly need it, section markers may be overridden in rpm's configuration
to provide additional "under the hood" functionality.  Add the section, even
if empty.''',

'no-%build-section',
'''The spec file does not contain a %build section.  Even if some packages
don't directly need it, section markers may be overridden in rpm's
configuration to provide additional "under the hood" functionality, such as
injection of automatic -debuginfo subpackages.  Add the section, even if
empty.''',

'no-%install-section',
'''The spec file does not contain an %install section.  Even if some packages
don't directly need it, section markers may be overridden in rpm's
configuration to provide additional "under the hood" functionality.  Add the
section, even if empty.''',

'no-%clean-section',
'''The spec file doesn't contain a %clean section to remove the files installed
by the %install section.''',

'more-than-one-%changelog-section',
'''The spec file unnecessarily contains more than one %changelog section;
remove the extra ones.''',

'lib-package-without-%mklibname',
'''The package name must be built using %mklibname to allow lib64 and lib32
coexistence.''',

'%ifarch-applied-patch',
'''A patch is applied inside an %ifarch block. Patches must be applied
on all architectures and may contain necessary configure and/or code
patch to be effective only on a given arch.''',

'prereq-use',
'''The use of PreReq is deprecated. In the majority of cases, a plain Requires
is enough and the right thing to do. Sometimes Requires(pre), Requires(post),
Requires(preun) and/or Requires(postun) can also be used instead of PreReq.''',

'buildprereq-use',
'''The use of BuildPreReq is deprecated, build dependencies are always required
before a package can be built.  Use plain BuildRequires instead.''',

'broken-syntax-in-scriptlet-requires',
'''Comma separated context marked dependencies are silently broken in some
versions of rpm.  One way to work around it is to split them into several ones,
eg. replace "Requires(post,preun): foo" with "Requires(post): foo" and
"Requires(preun): foo".''',

'setup-not-in-prep',
'''The %setup macro should only be used within the %prep section because it may
not expand to anything outside of it and can break the build in unpredictable
ways.''',

'setup-not-quiet',
'''Use the -q option to the %setup macro to avoid useless build output from
unpacking the sources.''',

'no-cleaning-of-buildroot',
'''You should clean $RPM_BUILD_ROOT in the %clean section and in the beginning
of the %install section. Use "rm -rf $RPM_BUILD_ROOT". Some rpm configurations
do this automatically; if your package is only going to be built in such
configurations, you can ignore this warning for the section(s) where your rpm
takes care of it.''',

'rpm-buildroot-usage',
'''$RPM_BUILD_ROOT should not be touched during %build or %prep stage, as it
may break short circuit builds.''',

'make-check-outside-check-section',
'''Make check or other automated regression test should be run in %check, as
they can be disabled with a rpm macro for short circuiting purposes.''',

'macro-in-%changelog',
'''Macros are expanded in %changelog too, which can in unfortunate cases lead
to the package not building at all, or other subtle unexpected conditions that
affect the build.  Even when that doesn\'t happen, the expansion results in
possibly "rewriting history" on subsequent package revisions and generally
odd entries eg. in source rpms, which is rarely wanted.  Avoid use of macros
in %changelog altogether, or use two '%'s to escape them, like '%%foo'.''',

'depscript-without-disabling-depgen',
'''In some common rpm configurations/versions, defining __find_provides and/or
__find_requires has no effect if rpm's internal dependency generator has not
been disabled for the build.  %define _use_internal_dependency_generator to 0
to disable it in the specfile, or don't define __find_provides/requires.''',

'mixed-use-of-spaces-and-tabs',
'''The specfile mixes use of spaces and tabs for indentation, which is a
cosmetic annoyance.  Use either spaces or tabs for indentation, not both.''',

'unversioned-explicit-provides',
'''The specfile contains an unversioned Provides: token, which will match all
older, equal, and newer versions of the provided thing.  This may cause
update problems and will make versioned dependencies, obsoletions and conflicts
on the provided thing useless -- make the Provides versioned if possible.''',

'unversioned-explicit-obsoletes',
'''The specfile contains an unversioned Obsoletes: token, which will match all
older, equal and newer versions of the obsoleted thing.  This may cause update
problems, restrict future package/provides naming, and may match something it
was originally not inteded to match -- make the Obsoletes versioned if
possible.''',

'libdir-macro-in-noarch-package',
'''The %{_libdir} or %{_lib} macro was found in a noarch package in a section
that gets included in binary packages.  This is most likely an error because
these macros are expanded on the build host and their values vary between
architectures, probably resulting in a package that does not work properly
on all architectures at runtime. Investigate whether the package is really
architecture independent or if some other dir/macro should be instead.''',

'non-break-space',
'''The spec file contains a non-break space, which looks like a regular space
in some editors but can lead to obscure errors. It should be replaced by a
regular space.''',

'non-standard-group',
'''The value of the Group tag in the package is not valid.  Valid groups are:
"%s".''' % '", "'.join(VALID_GROUPS),

'specfile-error',
'''This error occurred when rpmlint used rpm to query the specfile.  The error
is output by rpm and the message should contain more information.''',

'comparison-operator-in-deptoken',
'''This dependency token contains a comparison operator (<, > or =).  This is
usually not intended and may be caused by missing whitespace between the
token's name, the comparison operator and the version string.''',

'macro-in-comment',
'''There is a unescaped macro after a shell style comment in the specfile.
Macros are expanded everywhere, so check if it can cause a problem in this
case and escape the macro with another leading % if appropriate.''',

'file-size-mismatch',
'''The size of the file in the package does not match the size indicated by
peeking at its URL.  Verify that the file in the package has the intended
contents.''',

'file-md5-mismatch',
'''The MD5 hash of the file in the package does not match the MD5 hash
indicated by peeking at its URL.  Verify that the file in the package has the
intended contents.''',

'patch-fuzz-is-changed',
'''The internal patch fuzz value was changed, and could hide patchs issues, or
could lead to applying a patch at the wrong location. Usually, this is often
the sign that someone didn't check if a patch is still needed and do not want
to rediff it. It is usually better to rediff the patch and try to send it
upstream.'''
)

# SpecCheck.py ends here
