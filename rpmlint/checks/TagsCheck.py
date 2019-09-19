#############################################################################
# File          : TagsCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 00:03:24 1999
# Purpose       : Check a package to see if some rpm tags are present
#############################################################################

import calendar
from pathlib import Path
import re
import time
from urllib.parse import urlparse

import rpm
from rpmlint import pkg as Pkg
from rpmlint.checks import FilesCheck
from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import byte_to_string
from rpmlint.spellcheck import Spellcheck

CAPITALIZED_IGNORE_LIST = ('jQuery', 'openSUSE', 'wxWidgets', 'a', 'an', 'uWSGI')

changelog_version_regex = re.compile(r'[^>]([^ >]+)\s*$')
changelog_text_version_regex = re.compile(r'^\s*-\s*((\d+:)?[\w\.]+-[\w\.]+)')
devel_number_regex = re.compile(r'(.*?)([0-9.]+)(_[0-9.]+)?-devel')
lib_devel_number_regex = re.compile(r'^lib(.*?)([0-9.]+)(_[0-9.]+)?-devel')
lib_package_regex = re.compile(r'(?:^(?:compat-)?lib.*?(\.so.*)?|libs?[\d-]*)$', re.IGNORECASE)
leading_space_regex = re.compile(r'^\s+')
pkg_config_regex = re.compile(r'^/usr/(?:lib\d*|share)/pkgconfig/')
license_regex = re.compile(r'\(([^)]+)\)|\s(?:and|or|AND|OR)\s')
invalid_version_regex = re.compile(r'([0-9](?:rc|alpha|beta|pre).*)', re.IGNORECASE)
# () are here for grouping purpose in the regexp
tag_regex = re.compile(r'^((?:Auto(?:Req|Prov|ReqProv)|Build(?:Arch(?:itectures)?|Root)|(?:Build)?Conflicts|(?:Build)?(?:Pre)?Requires|Copyright|(?:CVS|SVN)Id|Dist(?:ribution|Tag|URL)|DocDir|(?:Build)?Enhances|Epoch|Exclu(?:de|sive)(?:Arch|OS)|Group|Icon|License|Name|No(?:Patch|Source)|Obsoletes|Packager|Patch\d*|Prefix(?:es)?|Provides|(?:Build)?Recommends|Release|RHNPlatform|Serial|Source\d*|(?:Build)?Suggests|Summary|(?:Build)?Supplements|(?:Bug)?URL|Vendor|Version)(?:\([^)]+\))?:)\s*\S', re.IGNORECASE)
punct = '.,:;!?'
so_dep_regex = re.compile(r'\.so(\.[0-9a-zA-Z]+)*(\([^)]*\))*$')
# we assume that no rpm packages existed before rpm itself existed...
oldest_changelog_timestamp = calendar.timegm(time.strptime('1995-01-01', '%Y-%m-%d'))


class TagsCheck(AbstractCheck):

    def __init__(self, config, output):
        super().__init__(config, output)
        self.valid_groups = config.configuration['ValidGroups']
        self.valid_licenses = config.configuration['ValidLicenses']
        self.invalid_requires = map(re.compile, config.configuration['InvalidRequires'])
        self.packager_regex = re.compile(config.configuration['Packager'])
        self.release_ext = config.configuration['ReleaseExtension']
        self.extension_regex = self.release_ext and re.compile(self.release_ext)
        self.use_version_in_changelog = config.configuration['UseVersionInChangelog']
        self.invalid_url_regex = re.compile(config.configuration['InvalidURL'], re.IGNORECASE)
        self.forbidden_words_regex = re.compile(r'(%s)' % config.configuration['ForbiddenWords'], re.IGNORECASE)
        self.valid_buildhost_regex = re.compile(config.configuration['ValidBuildHost'])
        self.use_epoch = config.configuration['UseEpoch']
        self.max_line_len = config.configuration['MaxLineLength']
        self.spellcheck = config.configuration['UseEnchant']
        if self.spellcheck:
            self.spellchecker = Spellcheck()

        for i in ('obsoletes', 'conflicts', 'provides', 'recommends', 'suggests',
                  'enhances', 'supplements'):
            self.output.error_details.update({'no-epoch-in-{}'.format(i):
                                              'Your package contains a versioned %s entry without an Epoch.'
                                              % i.capitalize()})
        self.output.error_details.update({'non-standard-group':
                                          """The value of the Group tag in the package is not valid.  Valid groups are:
                                          '%s'.""" % ', '.join(self.valid_groups),
                                          'not-standard-release-extension':
                                          'Your release tag must match the regular expression ' + self.release_ext + '.',
                                          'summary-too-long':
                                          "The 'Summary:' must not exceed %d characters." % self.max_line_len,
                                          'description-line-too-long':
                                          """Your description lines must not exceed %d characters. If a line is exceeding
                                          this number, cut it to fit in two lines.""" % self.max_line_len,
                                          'invalid-license':
                                          """The value of the License tag was not recognized.  Known values are:
                                          '%s'.""" % ', '.join(self.valid_licenses),
                                          })

    def _unexpanded_macros(self, pkg, tagname, value, is_url=False):
        if not value:
            return
        if not isinstance(value, (list, tuple)):
            value = [value]
        for val in value:
            for match in self.macro_regex.findall(val):
                # Do not warn about %XX URL escapes
                if is_url and re.match('^%[0-9A-F][0-9A-F]$', match, re.I):
                    continue
                self.output.add_info('W', pkg, 'unexpanded-macro', tagname, match)

    def check(self, pkg):

        packager = pkg[rpm.RPMTAG_PACKAGER]
        if packager:
            self._unexpanded_macros(pkg, 'Packager', packager)
            if self.config.configuration['Packager'] and \
               not self.packager_regex.search(packager):
                self.output.add_info('W', pkg, 'invalid-packager', packager)
        else:
            self.output.add_info('E', pkg, 'no-packager-tag')

        version = pkg[rpm.RPMTAG_VERSION]
        if version:
            self._unexpanded_macros(pkg, 'Version', version)
            res = invalid_version_regex.search(version)
            if res:
                self.output.add_info('E', pkg, 'invalid-version', version)
        else:
            self.output.add_info('E', pkg, 'no-version-tag')

        release = pkg[rpm.RPMTAG_RELEASE]
        if release:
            self._unexpanded_macros(pkg, 'Release', release)
            if self.release_ext and not self.extension_regex.search(release):
                self.output.add_info('W', pkg, 'not-standard-release-extension', release)
        else:
            self.output.add_info('E', pkg, 'no-release-tag')

        epoch = pkg[rpm.RPMTAG_EPOCH]
        if epoch is None:
            if self.use_epoch:
                self.output.add_info('E', pkg, 'no-epoch-tag')
        else:
            if epoch > 99:
                self.output.add_info('W', pkg, 'unreasonable-epoch', epoch)
            epoch = str(epoch)

        if self.use_epoch:
            for tag in ('obsoletes', 'conflicts', 'provides', 'recommends',
                        'suggests', 'enhances', 'supplements'):
                for x in (x for x in getattr(pkg, tag)()
                          if x[1] and x[2][0] is None):
                    self.output.add_info('W', pkg, 'no-epoch-in-%s' % tag,
                                         Pkg.formatRequire(*x))

        name = pkg.name
        deps = pkg.requires() + pkg.prereq()
        devel_depend = False
        is_devel = FilesCheck.devel_regex.search(name)
        is_source = pkg.isSource()
        for d in deps:
            value = Pkg.formatRequire(*d)
            if self.use_epoch and d[1] and d[2][0] is None and \
                    not d[0].startswith('rpmlib('):
                self.output.add_info('W', pkg, 'no-epoch-in-dependency', value)
            for r in self.invalid_requires:
                if r.search(d[0]):
                    self.output.add_info('E', pkg, 'invalid-dependency', d[0])

            if d[0].startswith('/usr/local/'):
                self.output.add_info('E', pkg, 'invalid-dependency', d[0])

            if is_source:
                if lib_devel_number_regex.search(d[0]):
                    self.output.add_info('E', pkg, 'invalid-build-requires', d[0])
            elif not is_devel:
                if not devel_depend and FilesCheck.devel_regex.search(d[0]):
                    self.output.add_info('E', pkg, 'devel-dependency', d[0])
                    devel_depend = True
                if not d[1]:
                    res = lib_package_regex.search(d[0])
                    if res and not res.group(1):
                        self.output.add_info('E', pkg, 'explicit-lib-dependency', d[0])

            if d[1] == rpm.RPMSENSE_EQUAL and d[2][2] is not None:
                self.output.add_info('W', pkg, 'requires-on-release', value)
            self._unexpanded_macros(pkg, 'dependency %s' % (value,), value)

        self._unexpanded_macros(pkg, 'Name', name)
        if not name:
            self.output.add_info('E', pkg, 'no-name-tag')
        else:
            if is_devel and not is_source:
                base = is_devel.group(1)
                dep = None
                has_so = False
                has_pc = False
                for fname in pkg.files():
                    if fname.endswith('.so'):
                        has_so = True
                    if pkg_config_regex.match(fname) and fname.endswith('.pc'):
                        has_pc = True
                if has_so:
                    base_or_libs = base + '/' + base + '-libs/lib' + base
                    # try to match *%_isa as well (e.g. '(x86-64)', '(x86-32)')
                    base_or_libs_re = re.compile(
                        r'^(lib)?%s(-libs)?(\(\w+-\d+\))?$' % re.escape(base))
                    for d in deps:
                        if base_or_libs_re.match(d[0]):
                            dep = d
                            break
                    if not dep:
                        self.output.add_info('W', pkg, 'no-dependency-on', base_or_libs)
                    elif version:
                        exp = (epoch, version, None)
                        sexp = Pkg.versionToString(exp)
                        if not dep[1]:
                            self.output.add_info('W', pkg, 'no-version-dependency-on',
                                                 base_or_libs, sexp)
                        elif dep[2][:2] != exp[:2]:
                            self.output.add_info('W', pkg,
                                                 'incoherent-version-dependency-on',
                                                 base_or_libs,
                                                 Pkg.versionToString((dep[2][0],
                                                                     dep[2][1], None)),
                                                 sexp)
                    res = devel_number_regex.search(name)
                    if not res:
                        self.output.add_info('W', pkg, 'no-major-in-name', name)
                    else:
                        if res.group(3):
                            prov = res.group(1) + res.group(2) + '-devel'
                        else:
                            prov = res.group(1) + '-devel'

                        if prov not in (x[0] for x in pkg.provides()):
                            self.output.add_info('W', pkg, 'no-provides', prov)

                if has_pc:
                    found_pkg_config_dep = False
                    for p in (x[0] for x in pkg.provides()):
                        if p.startswith('pkgconfig('):
                            found_pkg_config_dep = True
                            break
                    if not found_pkg_config_dep:
                        self.output.add_info('E', pkg, 'no-pkg-config-provides')

        # List of words to ignore in spell check
        ignored_words = set()
        for pf in pkg.files():
            ignored_words.update(pf.split('/'))
        ignored_words.update((x[0] for x in pkg.provides()))
        ignored_words.update((x[0] for x in pkg.requires()))
        ignored_words.update((x[0] for x in pkg.conflicts()))
        ignored_words.update((x[0] for x in pkg.obsoletes()))

        langs = pkg[rpm.RPMTAG_HEADERI18NTABLE]

        summary = byte_to_string(pkg[rpm.RPMTAG_SUMMARY])
        if summary:
            if not langs:
                self._unexpanded_macros(pkg, 'Summary', summary)
            else:
                for lang in langs:
                    self.check_summary(pkg, lang, ignored_words)
        else:
            self.output.add_info('E', pkg, 'no-summary-tag')

        description = byte_to_string(pkg[rpm.RPMTAG_DESCRIPTION])
        if description:
            if not langs:
                self._unexpanded_macros(pkg, '%description', description)
            else:
                for lang in langs:
                    self.check_description(pkg, lang, ignored_words)

            if len(description) < len(pkg[rpm.RPMTAG_SUMMARY]):
                self.output.add_info('W', pkg, 'description-shorter-than-summary')
        else:
            self.output.add_info('E', pkg, 'no-description-tag')

        group = pkg[rpm.RPMTAG_GROUP]
        self._unexpanded_macros(pkg, 'Group', group)
        if not group:
            self.output.add_info('E', pkg, 'no-group-tag')
        elif pkg.name.endswith('-devel') and not group.startswith('Development/'):
            self.output.add_info('W', pkg, 'devel-package-with-non-devel-group', group)
        elif self.valid_groups and group not in self.valid_groups:
            self.output.add_info('W', pkg, 'non-standard-group', group)

        buildhost = pkg[rpm.RPMTAG_BUILDHOST]
        self._unexpanded_macros(pkg, 'BuildHost', buildhost)
        if not buildhost:
            self.output.add_info('E', pkg, 'no-buildhost-tag')
        elif self.config.configuration['ValidBuildHost'] and \
                not self.valid_buildhost_regex.search(buildhost):
            self.output.add_info('W', pkg, 'invalid-buildhost', buildhost)

        changelog = pkg[rpm.RPMTAG_CHANGELOGNAME]
        if not changelog:
            self.output.add_info('E', pkg, 'no-changelogname-tag')
        else:
            clt = pkg[rpm.RPMTAG_CHANGELOGTEXT]
            if self.use_version_in_changelog:
                ret = changelog_version_regex.search(byte_to_string(changelog[0]))
                if not ret and clt:
                    # we also allow the version specified as the first
                    # thing on the first line of the text
                    ret = changelog_text_version_regex.search(byte_to_string(clt[0]))
                if not ret:
                    self.output.add_info('W', pkg, 'no-version-in-last-changelog')
                elif version and release:
                    srpm = pkg[rpm.RPMTAG_SOURCERPM] or ''
                    # only check when source name correspond to name
                    if srpm[0:-8] == '%s-%s-%s' % (name, version, release):
                        expected = [version + '-' + release]
                        if epoch is not None:  # regardless of use_epoch
                            expected[0] = str(epoch) + ':' + expected[0]
                        # Allow EVR in changelog without release extension,
                        # the extension is often a macro or otherwise dynamic.
                        if self.release_ext:
                            expected.append(self.extension_regex.sub('', expected[0]))
                        if ret.group(1) not in expected:
                            if len(expected) == 1:
                                expected = expected[0]
                            self.output.add_info('W', pkg, 'incoherent-version-in-changelog',
                                                 ret.group(1), expected)

            if clt:
                changelog = changelog + clt
            for s in changelog:
                if not Pkg.is_utf8_bytestr(s):
                    self.output.add_info('E', pkg, 'tag-not-utf8', '%changelog')
                    break

            clt = pkg[rpm.RPMTAG_CHANGELOGTIME][0]
            if clt:
                clt -= clt % (24 * 3600)  # roll back to 00:00:00, see #246
                if clt < oldest_changelog_timestamp:
                    self.output.add_info('W', pkg, 'changelog-time-overflow',
                                         time.strftime('%Y-%m-%d', time.gmtime(clt)))
                elif clt > time.time():
                    self.output.add_info('E', pkg, 'changelog-time-in-future',
                                         time.strftime('%Y-%m-%d', time.gmtime(clt)))

        def split_license(license):
            return (x.strip() for x in
                    (l for l in license_regex.split(license) if l))

        rpm_license = pkg[rpm.RPMTAG_LICENSE]
        if not rpm_license:
            self.output.add_info('E', pkg, 'no-license')
        else:
            valid_license = True
            if rpm_license not in self.valid_licenses:
                for l1 in split_license(rpm_license):
                    if l1 in self.valid_licenses:
                        continue
                    for l2 in split_license(l1):
                        if l2 not in self.valid_licenses:
                            self.output.add_info('W', pkg, 'invalid-license', l2)
                            valid_license = False
            if not valid_license:
                self._unexpanded_macros(pkg, 'License', rpm_license)

        for tag in ('URL', 'DistURL', 'BugURL'):
            if hasattr(rpm, 'RPMTAG_%s' % tag.upper()):
                url = byte_to_string(pkg[getattr(rpm, 'RPMTAG_%s' % tag.upper())])
                self._unexpanded_macros(pkg, tag, url, is_url=True)
                if url:
                    (scheme, netloc) = urlparse(url)[0:2]
                    if not scheme or not netloc or '.' not in netloc or \
                            scheme not in ('http', 'https', 'ftp') or \
                            (self.config.configuration['InvalidURL'] and
                             self.invalid_url_regex.search(url)):
                        self.output.add_info('W', pkg, 'invalid-url', tag, url)
                elif tag == 'URL':
                    self.output.add_info('W', pkg, 'no-url-tag')

        obs_names = [x[0] for x in pkg.obsoletes()]
        prov_names = [x[0] for x in pkg.provides()]

        for o in (x for x in obs_names if x not in prov_names):
            self.output.add_info('W', pkg, 'obsolete-not-provided', o)
        for o in pkg.obsoletes():
            value = Pkg.formatRequire(*o)
            self._unexpanded_macros(pkg, 'Obsoletes %s' % (value,), value)

        # TODO: should take versions, <, <=, =, >=, > into account here
        #       https://bugzilla.redhat.com/460872
        useless_provides = set()
        for p in prov_names:
            if (prov_names.count(p) != 1 and
                    not p.startswith('debuginfo(') and
                    p not in useless_provides):
                useless_provides.add(p)
        for p in sorted(useless_provides):
            self.output.add_info('E', pkg, 'useless-provides', p)

        for tagname, items in (
                ('Provides', pkg.provides()),
                ('Conflicts', pkg.conflicts()),
                ('Obsoletes', pkg.obsoletes()),
                ('Supplements', pkg.supplements()),
                ('Suggests', pkg.suggests()),
                ('Enhances', pkg.enhances()),
                ('Recommends', pkg.recommends())):
            for p in items:
                value = Pkg.formatRequire(*p)
                self._unexpanded_macros(pkg, '%s %s' % (tagname, value), value)

        obss = pkg.obsoletes()
        if obss:
            provs = pkg.provides()
            for prov in provs:
                for obs in obss:
                    if Pkg.rangeCompare(obs, prov):
                        self.output.add_info('W', pkg, 'self-obsoletion',
                                             '%s obsoletes %s' %
                                             (Pkg.formatRequire(*obs),
                                              Pkg.formatRequire(*prov)))

        expfmt = rpm.expandMacro('%{_build_name_fmt}')
        if pkg.isSource():
            # _build_name_fmt often (always?) ends up not outputting src/nosrc
            # as arch for source packages, do it ourselves
            expfmt = re.sub(r'(?i)%\{?ARCH\b\}?', pkg.arch, expfmt)
        expected = pkg.header.sprintf(expfmt).split('/')[-1]
        basename = Path(pkg.filename).parent
        if basename != expected:
            self.output.add_info('W', pkg, 'non-coherent-filename', basename, expected)

        for tag in ('Distribution', 'DistTag', 'ExcludeArch', 'ExcludeOS',
                    'Vendor'):
            if hasattr(rpm, 'RPMTAG_%s' % tag.upper()):
                res = byte_to_string(pkg[getattr(rpm, 'RPMTAG_%s' % tag.upper())])
                self._unexpanded_macros(pkg, tag, res)

    def check_description(self, pkg, lang, ignored_words):
        description = pkg.langtag(rpm.RPMTAG_DESCRIPTION, lang)
        if not Pkg.is_utf8_bytestr(description):
            self.output.add_info('E', pkg, 'tag-not-utf8', '%description', lang)
        description = byte_to_string(description)
        self._unexpanded_macros(pkg, '%%description -l %s' % lang, description)
        if self.spellcheck:
            pkgname = byte_to_string(pkg.header[rpm.RPMTAG_NAME])
            typos = self.spellchecker.spell_check(description, '%description -l {}', lang, pkgname, ignored_words)
            for typo in typos.items():
                self.output.add_info('E', pkg, 'spelling-error', typo)
        for l in description.splitlines():
            if len(l) > self.max_line_len:
                self.output.add_info('E', pkg, 'description-line-too-long', lang, l)
            res = self.forbidden_words_regex.search(l)
            if res and self.config.configuration['ForbiddenWords']:
                self.output.add_info('W', pkg, 'description-use-invalid-word', lang,
                                     res.group(1))
            res = tag_regex.search(l)
            if res:
                self.output.add_info('W', pkg, 'tag-in-description', lang, res.group(1))

    def check_summary(self, pkg, lang, ignored_words):
        summary = pkg.langtag(rpm.RPMTAG_SUMMARY, lang)
        if not Pkg.is_utf8_bytestr(summary):
            self.output.add_info('E', pkg, 'tag-not-utf8', 'Summary', lang)
        summary = byte_to_string(summary)
        self._unexpanded_macros(pkg, 'Summary(%s)' % lang, summary)
        if self.spellcheck:
            pkgname = byte_to_string(pkg.header[rpm.RPMTAG_NAME])
            typos = self.spellchecker.spell_check(summary, 'Summary({})', lang, pkgname, ignored_words)
            for typo in typos.items():
                self.output.add_info('E', pkg, 'spelling-error', typo)
        if '\n' in summary:
            self.output.add_info('E', pkg, 'summary-on-multiple-lines', lang)
        if (summary[0] != summary[0].upper() and
                summary.partition(' ')[0] not in CAPITALIZED_IGNORE_LIST):
            self.output.add_info('W', pkg, 'summary-not-capitalized', lang, summary)
        if summary[-1] == '.':
            self.output.add_info('W', pkg, 'summary-ended-with-dot', lang, summary)
        if len(summary) > self.max_line_len:
            self.output.add_info('E', pkg, 'summary-too-long', lang, summary)
        if leading_space_regex.search(summary):
            self.output.add_info('E', pkg, 'summary-has-leading-spaces', lang, summary)
        res = self.forbidden_words_regex.search(summary)
        if res and self.config.configuration['ForbiddenWords']:
            self.output.add_info('W', pkg, 'summary-use-invalid-word', lang, res.group(1))
        if pkg.name:
            sepchars = r'[\s%s]' % punct
            res = re.search(r'(?:^|\s)(%s)(?:%s|$)' %
                            (re.escape(pkg.name), sepchars),
                            summary, re.IGNORECASE | re.UNICODE)
            if res:
                self.output.add_info('W', pkg, 'name-repeated-in-summary', lang,
                                     res.group(1))
