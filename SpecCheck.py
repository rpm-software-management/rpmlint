#############################################################################
# File          : SpecCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Thu Oct  7 17:06:14 1999
# Version       : $Id$
# Purpose       : check the spec file of a source rpm.
#############################################################################

from Filter import *
import AbstractCheck
import Pkg
import re
import sys
import string
import Config

# Don't check for hardcoded library paths in biarch packages
DEFAULT_BIARCH_PACKAGES = '^(gcc|glibc)'

# Don't check for hardcoded library paths in packages which can have
# their noarch files in /usr/lib/<package>/*, or packages that can't
# be installed on biarch systems
DEFAULT_HARDCODED_LIB_PATH_EXCEPTIONS = '/lib/(modules|cpp|perl5|rpm|hotplug|firmware)($|[\s/,])'

patch_regex = re.compile("^Patch(\d*)\s*:\s*([^\s]+)", re.IGNORECASE)
# TODO: http://rpmlint.zarb.org/cgi-bin/trac.cgi/ticket/59
applied_patch_regex = re.compile("^%patch.*-P\s+(\d+)|^%patch(\d*)\s")
source_dir_regex = re.compile("^[^#]*(\$RPM_SOURCE_DIR|%{?_sourcedir}?)")
obsolete_tags_regex = re.compile("^(Copyright|Serial)\s*:\s*([^\s]+)")
buildroot_regex = re.compile('Buildroot\s*:\s*([^\s]+)', re.IGNORECASE)
prefix_regex = re.compile('^Prefix\s*:\s*([^\s]+)', re.IGNORECASE)
packager_regex = re.compile('^Packager\s*:\s*([^\s]+)', re.IGNORECASE)
noarch_regex = re.compile('^BuildArch(?:itectures)?\s*:\s*\\bnoarch\\b', re.IGNORECASE)
make_check_regexp = re.compile('(^|\s|%{?__)make}?\s+(check|test)')
rm_regex = re.compile('(^|\s)((.*/)?rm|%{?__rm}?) ')
rpm_buildroot_regex = re.compile('(\\\*)\${?RPM_BUILD_ROOT}?|(%+){?buildroot}?')
configure_start_regex = re.compile('\./configure')
configure_libdir_spec_regex = re.compile('ln |\./configure[^#]*--libdir=([^\s]+)[^#]*')
lib_package_regex = re.compile('^%package.*\Wlib')
mklibname_regex = re.compile('%mklibname')
ifarch_regex = re.compile('%ifn?arch\s+')
if_regex = re.compile('%if\s+')
endif_regex = re.compile('%endif\\b')
biarch_package_regex = re.compile(DEFAULT_BIARCH_PACKAGES)
hardcoded_lib_path_exceptions_regex = re.compile(Config.getOption('HardcodedLibPathExceptions', DEFAULT_HARDCODED_LIB_PATH_EXCEPTIONS))
prereq_regex = re.compile('^PreReq(\(.*\))?:\s*(.+?)\s*$', re.IGNORECASE)
buildprereq_regex = re.compile('^BuildPreReq:\s*(.+?)\s*$', re.IGNORECASE)
use_utf8 = Config.getOption('UseUTF8', Config.USEUTF8_DEFAULT)
macro_regex = re.compile('(%+)[{(]?(\w+)')
libdir_regex = re.compile('%{?_lib(?:dir)?\}?\\b')
comment_or_empty_regex = re.compile('^\s*(#|$)')
defattr_regex = re.compile('^\s*%defattr\\b')
attr_regex = re.compile('^\s*%attr\\b')

# Only check for /lib, /usr/lib, /usr/X11R6/lib
# TODO: better handling of X libraries and modules.
hardcoded_library_paths = '(/lib|/usr/lib|/usr/X11R6/lib/(?!([^/]+/)+)[^/]*\\.([oa]|la|so[0-9.]*))'
hardcoded_library_path_regex = re.compile('^[^#]*((^|\s+|\.\./\.\.|\${?RPM_BUILD_ROOT}?|%{?buildroot}?|%{?_prefix}?)' + hardcoded_library_paths + '(?=[\s;/])([^\s,;]*))')

# Requires(pre,post) is broken in some rpm versions, see
# https://bugzilla.redhat.com/118780 and bugs linked to that one.
scriptlet_requires_regex = re.compile('^(PreReq|Requires)\([^\)]*,', re.IGNORECASE)

depscript_override_regex = re.compile('(^|\s)%(define|global)\s+__find_(requires|provides)\s')
depgen_disable_regex = re.compile('(^|\s)%(define|global)\s+_use_internal_dependency_generator\s+0')

indent_spaces_regex = re.compile(' {3}.*\S')
indent_tabs_regex = re.compile('\t.*\S')

provides_regex = re.compile('^Provides(?:\([^\)]+\))?:\s*(.*)', re.IGNORECASE)
obsoletes_regex = re.compile('^Obsoletes:\s*(.*)', re.IGNORECASE)

setup_q_regex = re.compile(' -[A-Za-z]*q')
setup_t_regex = re.compile(' -[A-Za-z]*T')
setup_ab_regex = re.compile(' -[A-Za-z]*[ab]')

def deptokens(line):
    '''Parse provides/requires/conflicts/obsoletes line to dep token list.'''
    prco = []
    tmp = ''
    wantmore = 0
    for tok in re.split('[\s,]+', line.strip()):
        if len(tok) == 0:
            continue
        if len(tmp) == 0:
            tmp = tok
        elif wantmore:
            tmp += ' ' + tok
            wantmore = 0
        elif tok[0] in ('=', '<', '>'):
            tmp += ' ' + tok
            wantmore = 1
        else:
            prco.append(tmp)
            wantmore = 0
            tmp = tok
    if len(tmp) != 0:
        prco.append(tmp)
    return prco

def versioned(toks):
    '''Return versioned dependency tokens from the given list.'''
    res = []
    for tok in toks:
        if tok.find('=') > 0 or tok.find('<') > 0 or tok.find('>') > 0:
            res.append(tok)
    return res

def unversioned(toks):
    '''Return unversioned dependency tokens from the given list.'''
    res = []
    for tok in toks:
        if tok.find(' ') < 0:
            res.append(tok)
    return res

def contains_buildroot(line):
    '''Check if the given line contains use of rpm buildroot.'''
    res = rpm_buildroot_regex.search(line)
    if res and \
           (not res.group(1) or len(res.group(1)) % 2 == 0) and \
           (not res.group(2) or len(res.group(2)) % 2 != 0):
        return 1
    return 0

class SpecCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "SpecCheck")
        self._spec_file = None

    def check(self, pkg):
        if not pkg.isSource():
            return

        wrong_spec = False
        # lookup spec file
        files = pkg.files()
        for f in files.keys():
            if f.endswith('.spec'):
                if f == pkg.name + ".spec":
                        self._spec_file = pkg.dirName() + "/" + f
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
            spec_lines = Pkg.readlines(self._spec_file)
            self.check_spec(pkg, spec_lines)

    def check_spec(self, pkg, spec_lines):
        patches = {}
        applied_patches = []
        applied_patches_ifarch = []
        source_dir = None
        buildroot = 0
        noarch = 0
        configure = 0
        configure_cmdline = ""
        mklibname = 0
        lib = 0
        if_depth = 0
        ifarch_depth = -1
        current_section = 'package'       
        buildroot_clean={'clean':0 , 'install':0}
        depscript_override = 0
        depgen_disabled = 0
        indent_spaces = 0
        indent_tabs = 0
        files_has_defattr = 0
        section = {}
        for sec in ['description', 'prep', 'build', 'install', 'clean',
                    'files', 'changelog', 'package', 'check']:
            section[sec] = {
                'count': 0,
                're': re.compile('^%' + sec + '(?:\s|$)'),
                }

        if self._spec_file:
            if use_utf8 and not Pkg.is_utf8(self._spec_file):
                printError(pkg, "non-utf8-spec-file", self._spec_file)

        # gather info from spec lines

        pkg.current_linenum = 0
        for line in spec_lines:
            pkg.current_linenum += 1
            if chr(0xA0) in line:
                printWarning(pkg, "non-break-space", "line %s" % (pkg.current_linenum)) 
            section_marker = 0
            for i in section.keys():
                if section[i]['re'].search(line):
                    current_section = i
                    section_marker = 1
                    section[i]['count'] = section[i]['count'] + 1

            if section_marker:
                if current_section == 'files':
                    files_has_defattr = 0
                continue

            if current_section in ('prep', 'build'):
                if contains_buildroot(line):
                    printWarning(pkg, 'rpm-buildroot-usage', '%' + current_section, line[:-1].strip())

            if make_check_regexp.search(line) and current_section not in ('check', 'changelog', 'package', 'description'):
                printWarning(pkg, 'make-check-outside-check-section', line[:-1])

            if current_section in buildroot_clean.keys():
                if contains_buildroot(line) and rm_regex.search(line):
                    buildroot_clean[current_section] = 1

            if ifarch_regex.search(line):
                if_depth = if_depth + 1
                ifarch_depth = if_depth

            if if_regex.search(line):
                if_depth = if_depth + 1

            if line.startswith('%setup'):
                if not setup_q_regex.search(line):
                    # Don't warn if there's a -T without -a or -b
                    if setup_t_regex.search(line):
                        if setup_ab_regex.search(line):
                            printWarning(pkg, 'setup-not-quiet')
                    else:
                        printWarning(pkg, 'setup-not-quiet')

            if endif_regex.search(line):
                if ifarch_depth == if_depth:
                    ifarch_depth = -1
                if_depth = if_depth - 1

            res=patch_regex.search(line)
            if res:
                pnum = int(res.group(1) or 0)
                patches[pnum] = res.group(2)
            else:
                res = applied_patch_regex.search(line)
                if res:
                    pnum = int(res.group(1) or res.group(2) or 0)
                    applied_patches.append(pnum)
                    if ifarch_depth > 0:
                        applied_patches_ifarch.append(pnum)
                elif not source_dir:
                    res = source_dir_regex.search(line)
                    if res:
                        source_dir = 1
                        printError(pkg, "use-of-RPM_SOURCE_DIR")

            res=obsolete_tags_regex.search(line)
            if res:
                printWarning(pkg, "obsolete-tag", res.group(1))

            if configure:
                if configure_cmdline[-1] == "\\":
                    configure_cmdline=configure_cmdline[:-1] + string.strip(line)
                else:
                    configure = 0
                    res = configure_libdir_spec_regex.search(configure_cmdline)
                    if not res:
                        printWarning(pkg, "configure-without-libdir-spec")
                    elif res.group(1):
                        res = re.match(hardcoded_library_paths, res.group(1))
                        if res:
                            printError(pkg, "hardcoded-library-path", res.group(1), "in configure options")

            if current_section != 'changelog' and configure_start_regex.search(line):
                configure = 1
                configure_cmdline = string.strip(line)

            res = hardcoded_library_path_regex.search(line)
            if current_section != 'changelog' and res and not (biarch_package_regex.match(pkg.name) or hardcoded_lib_path_exceptions_regex.search(string.lstrip(res.group(1)))):
                printError(pkg, "hardcoded-library-path", "in", string.lstrip(res.group(1)))

            res = buildroot_regex.search(line)
            if res:
                buildroot=1
                if res.group(1).startswith('/'):
                    printWarning(pkg, 'hardcoded-path-in-buildroot-tag', res.group(1))

            res = packager_regex.search(line)
            if res:
                printWarning(pkg, 'hardcoded-packager-tag', res.group(1))
            res=prefix_regex.search(line)
            if res:
                if res.group(1) == '%{_prefix}' or res.group(1) == '%_prefix':
                    printWarning(pkg, 'redundant-prefix-tag')
                else:
                    printWarning(pkg, 'hardcoded-prefix-tag', res.group(1))

            res = noarch_regex.search(line)
            if res:
                noarch = 1

            if mklibname_regex.search(line):
                mklibname = 1

            if lib_package_regex.search(line):
                lib = 1

            res = prereq_regex.search(line)
            if res:
                printWarning(pkg, 'prereq-use', res.group(2))

            res = buildprereq_regex.search(line)
            if res:
                printWarning(pkg, 'buildprereq-use', res.group(1))

            if scriptlet_requires_regex.search(line) and current_section == 'package':
                printError(pkg, 'broken-syntax-in-scriptlet-requires', string.strip(line))

            if current_section == 'changelog':
                res = macro_regex.search(line)
                if res and len(res.group(1)) % 2:
                    printWarning(pkg, 'macro-in-%changelog', res.group(2))
            else:
                if not depscript_override:
                    depscript_override = depscript_override_regex.search(line)
                if not depgen_disabled:
                    depgen_disabled = depgen_disable_regex.search(line)

                res = provides_regex.search(line)
                if res:
                    for prov in unversioned(deptokens(res.group(1))):
                        printWarning(pkg, 'unversioned-explicit-provides', prov)

                res = obsoletes_regex.search(line)
                if res:
                    for obs in unversioned(deptokens(res.group(1))):
                        printWarning(pkg, 'unversioned-explicit-obsoletes', obs)

            if current_section == 'files':
                if not comment_or_empty_regex.search(line) and not \
                   (ifarch_regex.search(line) or if_regex.search(line) or
                    endif_regex.search(line)):
                    if defattr_regex.search(line):
            	        files_has_defattr = 1;
                    elif not (files_has_defattr or attr_regex.search(line)):
    	    	        printError(pkg, 'files-attr-not-set')

            # TODO: check scriptlets for these too
            if current_section == 'files' and noarch:
                res = libdir_regex.search(line)
                if res:
                    printWarning(pkg, 'libdir-macro-in-noarch-package', line.rstrip())

            if not indent_tabs and indent_tabs_regex.search(line):
                indent_tabs = pkg.current_linenum
            if not indent_spaces and indent_spaces_regex.search(line):
                indent_spaces = pkg.current_linenum

        # No useful line number info beyond this point.
        pkg.current_linenum = None

        for sect in buildroot_clean:
            if not buildroot_clean[sect]:
                printError(pkg, 'no-cleaning-of-buildroot', '%' + sect)

        if not buildroot:
            printError(pkg, 'no-buildroot-tag')

        for sec in ('prep', 'build', 'install', 'clean'):
            if not section[sec]['count']:
                printWarning(pkg, 'no-%%%s-section' % sec)
        for sec in ('changelog',):
            # prep, build, install, clean, check prevented by rpmbuild
            if section[sec]['count'] > 1:
                printWarning(pkg, 'more-than-one-%%%s-section' % sec)

        if lib and not mklibname:
            printError(pkg, 'lib-package-without-%mklibname')

        if depscript_override and not depgen_disabled:
            printWarning(pkg, 'depscript-without-disabling-depgen')

        if indent_spaces and indent_tabs:
            printWarning(pkg, 'mixed-use-of-spaces-and-tabs',
                         '(spaces: line %d, tab: line %d)' %
                         (indent_spaces, indent_tabs))

        # process gathered info
        for p in patches.keys():
            if p in applied_patches_ifarch:
                printWarning(pkg, "%ifarch-applied-patch", "Patch%d:" % p, patches[p])
            if p not in applied_patches:
                printWarning(pkg, "patch-not-applied", "Patch%d:" % p, patches[p])

# Create an object to enable the auto registration of the test
check = SpecCheck()

# Add information about checks
if Config.info:
    addDetails(
'no-spec-file',
'''No spec file was specified in your RPM building. Please specify a valid
SPEC file to build a valid RPM package.''',

'invalid-spec-name',
'''Your spec filename must end with '.spec'. If it's not the case, rename your
file and rebuild your package.''',

'non-utf8-spec-file',
'''The character encoding of the spec file is not UTF-8.  Convert it for
example using iconv(1).''',

'use-of-RPM_SOURCE_DIR',
'''You use $RPM_SOURCE_DIR or %{_sourcedir} in your spec file. If you have to
use a directory for building, use $RPM_BUILD_ROOT instead.''',

'patch-not-applied',
'''A patch is included in your package but was not applied. Refer to the patches
documentation to see what's wrong.''',

'obsolete-tag',
'''The following tags are obsolete: Copyright and Serial. They must
be replaced by License and Epoch respectively.''',

'no-buildroot-tag',
'''The BuildRoot tag isn't used in your spec. It must be used in order to
allow building the package as non root on some systems.''',

'hardcoded-path-in-buildroot-tag',
'''A path is hardcoded in your Buildroot tag. It should be replaced
by something like %{_tmppath}/%name-root.''',

'hardcoded-packager-tag',
'''The Packager tag is hardcoded in your spec file. It should be removed, so
as to use rebuilder's own defaults.''',

'hardcoded-prefix-tag',
'''The Prefix tag is hardcoded in your spec file. It should be removed, so as
to allow package relocation.''',

'redundant-prefix-tag',
'''The Prefix tag is uselessly defined as %{_prefix} in your spec file. It
should be removed, as it is redundant with rpm defaults.''',

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

'setup-not-quiet',
'''Use the -q option to the %setup macro to avoid useless build output from
unpacking the sources.''',

'no-cleaning-of-buildroot',
'''You should clean $RPM_BUILD_ROOT in the %clean section and just after the
beginning of %install section. Use "rm -Rf $RPM_BUILD_ROOT".''',

'rpm-buildroot-usage',
'''$RPM_BUILD_ROOT should not be touched during %build or %prep stage, as it
will break short circuiting.''',

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

'files-attr-not-set',
'''A file or a directory entry in a %files section does not have attributes
set which may result in security issues in the resulting binary package
depending on the system where the package is built.  Add default attributes
using %defattr before it in the %files section, or use per line %attr's.''',
)

# SpecCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
