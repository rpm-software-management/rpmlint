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
license_exception_regex = re.compile(r'(\S+)\s(?:WITH|with)\s(\S+)')
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
        self.valid_license_exceptions = config.configuration['ValidLicenseExceptions']
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
        """Contains methods that checks tags and values in a spec file of a package."""

        version = pkg[rpm.RPMTAG_VERSION]
        release = pkg[rpm.RPMTAG_RELEASE]
        epoch = pkg[rpm.RPMTAG_EPOCH]
        group = pkg[rpm.RPMTAG_GROUP]
        buildhost = pkg[rpm.RPMTAG_BUILDHOST]
        langs = pkg[rpm.RPMTAG_HEADERI18NTABLE]
        summary = byte_to_string(pkg[rpm.RPMTAG_SUMMARY])
        description = byte_to_string(pkg[rpm.RPMTAG_DESCRIPTION])
        changelog = pkg[rpm.RPMTAG_CHANGELOGNAME]
        rpm_license = pkg[rpm.RPMTAG_LICENSE]
        name = pkg.name
        deps = pkg.requires + pkg.prereq
        is_devel = FilesCheck.devel_regex.search(name)
        is_source = pkg.is_source

        # List of words to ignore in spell check
        ignored_words = set()
        for pf in pkg.files:
            ignored_words.update(pf.split('/'))
        for tag in ('provides', 'requires', 'conflicts', 'obsoletes'):
            ignored_words.update((x[0] for x in 'pkg.' + str(tag)))

        # Run checks for whole package
        self._check_invalid_packager(pkg)
        self._check_invalid_version_and_no_version_tag(pkg, version)
        self._check_non_standard_release_extension(pkg, release)
        self._check_no_epoch_tag(pkg, epoch)
        self._check_no_epoch_in_tags(pkg)
        self._check_multiple_dependencies(pkg, deps, is_devel, is_source)
        self._unexpanded_macros(pkg, 'Name', name)
        self._check_multiple_tags(pkg, name, is_devel, is_source, deps, epoch, version)
        self._check_summary_tag(pkg, summary, langs, ignored_words)
        self._check_description_tag(pkg, description, langs, ignored_words)
        self._check_group_tag(pkg, group)
        self._check_buildhost_tag(pkg, buildhost)
        self._check_changelog_tag(pkg, changelog, version, release, name, epoch)
        self._check_license(pkg, rpm_license)
        self._check_url(pkg)

        prov_names = [x[0] for x in pkg.provides]

        self._check_obsolete_not_provided(pkg, prov_names)

        for dep_token in pkg.obsoletes:
            value = Pkg.formatRequire(*dep_token)
            self._unexpanded_macros(pkg, 'Obsoletes {}'.format(value,), value)

        self._check_useless_provides(pkg, prov_names)
        self._check_forbidden_controlchar(pkg)
        self._check_self_obsoletion(pkg)
        self._check_non_coherent_filename(pkg)

        for tag in ('Distribution', 'DistTag', 'ExcludeArch', 'ExcludeOS',
                    'Vendor'):
            if hasattr(rpm, 'RPMTAG_%s' % tag.upper()):
                res = byte_to_string(pkg[getattr(rpm, 'RPMTAG_%s' % tag.upper())])
                self._unexpanded_macros(pkg, tag, res)

    def check_description(self, pkg, lang, ignored_words):
        description = pkg.langtag(rpm.RPMTAG_DESCRIPTION, lang)
        description = byte_to_string(description)
        self._unexpanded_macros(pkg, '%%description -l %s' % lang, description)
        if self.spellcheck:
            pkgname = byte_to_string(pkg.header[rpm.RPMTAG_NAME])
            typos = self.spellchecker.spell_check(description, '%description -l {}', lang, pkgname, ignored_words)
            for typo in typos.items():
                self.output.add_info('E', pkg, 'spelling-error', typo)
        for i in description.splitlines():
            if len(i) > self.max_line_len:
                self.output.add_info('E', pkg, 'description-line-too-long', self._lang_for_error(lang), i)
            res = self.forbidden_words_regex.search(i)
            if res and self.config.configuration['ForbiddenWords']:
                self.output.add_info('W', pkg, 'description-use-invalid-word', self._lang_for_error(lang),
                                     res.group(1))
            res = tag_regex.search(i)
            if res:
                self.output.add_info('W', pkg, 'tag-in-description', self._lang_for_error(lang), res.group(1))

    def _lang_for_error(self, lang):
        return lang if lang != 'C' and lang != 'C.UTF-8' else None

    def check_summary(self, pkg, lang, ignored_words):
        summary = pkg.langtag(rpm.RPMTAG_SUMMARY, lang)
        summary = byte_to_string(summary)
        self._unexpanded_macros(pkg, 'Summary(%s)' % lang, summary)
        if self.spellcheck:
            pkgname = byte_to_string(pkg.header[rpm.RPMTAG_NAME])
            typos = self.spellchecker.spell_check(summary, 'Summary({})', lang, pkgname, ignored_words)
            for typo in typos.items():
                self.output.add_info('E', pkg, 'spelling-error', typo)
        if any(nl in summary for nl in ('\n', '\r')):
            self.output.add_info('E', pkg, 'summary-on-multiple-lines', self._lang_for_error(lang))
        if (summary[0] != summary[0].upper() and
                summary.partition(' ')[0] not in CAPITALIZED_IGNORE_LIST):
            self.output.add_info('W', pkg, 'summary-not-capitalized', self._lang_for_error(lang), summary)
        if summary[-1] == '.':
            self.output.add_info('W', pkg, 'summary-ended-with-dot', self._lang_for_error(lang), summary)
        if len(summary) > self.max_line_len:
            self.output.add_info('E', pkg, 'summary-too-long', self._lang_for_error(lang), summary)
        if leading_space_regex.search(summary):
            self.output.add_info('E', pkg, 'summary-has-leading-spaces', self._lang_for_error(lang), summary)
        res = self.forbidden_words_regex.search(summary)
        if res and self.config.configuration['ForbiddenWords']:
            self.output.add_info('W', pkg, 'summary-use-invalid-word', self._lang_for_error(lang), res.group(1))
        if pkg.name:
            sepchars = r'[\s%s]' % punct
            res = re.search(r'(?:^|\s)(%s)(?:%s|$)' %
                            (re.escape(pkg.name), sepchars),
                            summary, re.IGNORECASE | re.UNICODE)
            if res:
                self.output.add_info('W', pkg, 'name-repeated-in-summary', self._lang_for_error(lang),
                                     res.group(1))

    def _check_invalid_packager(self, pkg):
        """Trigger invalid-packager and no-packager-tag

        The packager email must end with an email compatible with the Packager
        option of rpmlint. Please change it and rebuild your package.

        Args:
            pkg: Variable used to store package name in STDOUT

        Returns:
            Output info to STDOUT
        """

        packager = pkg[rpm.RPMTAG_PACKAGER]
        if packager:
            self._unexpanded_macros(pkg, 'Packager', packager)
            if self.config.configuration['Packager'] and \
               not self.packager_regex.search(packager):
                self.output.add_info('W', pkg, 'invalid-packager', packager)
        else:
            self.output.add_info('E', pkg, 'no-packager-tag')

    def _check_invalid_version_and_no_version_tag(self, pkg, version):
        """Trigger check invalid-version, no-version-tag.

        Args:
            version: Variable used to find Version: value tag in rpm package

        Returns:
            Output info to STDOUT
        """

        if version:
            self._unexpanded_macros(pkg, 'Version', version)
            res = invalid_version_regex.search(version)
            # Check if a package has a version tag value start with
            # pre, alpha, beta or rc suffixes
            if res:
                self.output.add_info('E', pkg, 'invalid-version', version)
        # Check if a package has no Version: tag in its spec file
        else:
            self.output.add_info('E', pkg, 'no-version-tag')

    def _check_non_standard_release_extension(self, pkg, release):
        """Trigger check not-standard-release-extension, no-release-tag

        Args:
            release: Variable checks Realease: tag value

        Returns:
            Output info to STDOUT
        """
        if release:
            self._unexpanded_macros(pkg, 'Release', release)
            # [This check is dynamically produced]
            # Check if the release tag matches the regex expression self.release_ext
            if self.release_ext and not self.extension_regex.search(release):
                self.output.add_info('W', pkg, 'not-standard-release-extension', release)
        # Check if there is no Release tag in spec file
        else:
            self.output.add_info('E', pkg, 'no-release-tag')

    def _check_no_epoch_tag(self, pkg, epoch):
        """Trigger check no-epoch-tag, unreasonable-epoch

        Args:
            epoch: Finds the Epoch: tag

        Returns:
            Output info to STDOUT
        """
        if epoch is None:
            # Check if a package does not contain an Epoch: tag
            if self.use_epoch:
                self.output.add_info('E', pkg, 'no-epoch-tag')
        else:
            # Check if a package has an Epoch: value of greater than 99
            if epoch > 99:
                self.output.add_info('W', pkg, 'unreasonable-epoch', epoch)

    def _check_no_epoch_in_tags(self, pkg):
        """Trigger check no-epoch-in-{} multiple tags

        Check if versioned dependency is not used in tags even when
        UseEpoch is set to true and trigger checks in tags
        ['Obsoletes', 'Conflicts', 'Provides', 'Recommends',
            'Suggests', 'Enhances', 'Supplements']

        Returns:
            Output info to STDOUT
        """
        if self.use_epoch:
            for tag in ('obsoletes', 'conflicts', 'provides', 'recommends',
                        'suggests', 'enhances', 'supplements'):
                for x in (x for x in getattr(pkg, tag)()
                          if x[1] and x[2][0] is None):
                    self.output.add_info('W', pkg, 'no-epoch-in-{}'.format(tag),
                                         Pkg.formatRequire(*x))

    def _check_multiple_dependencies(self, pkg, deps, is_source, is_devel):
        """Contain multiple check, no-epoch-in-dependency, invalid-dependency,
        invalid-build-requires, devel-dependency, explicit-devel-dependency

        Args:
            deps: Variable to find PreReq and Requires tag
            is_source: Variable to check if a package is of source type
            is_devel: The param to check if a package name ends with *-devel

        Returns:
            Output info to STDOUT
            example:
                tmp.x86_64: W: requires-on-release foo = 2.1-1
        """

        devel_depend = False
        for dep in deps:
            value = Pkg.formatRequire(*dep)
            # Check if a package has a versioned dependency in spec file without Epoch: tag
            if self.use_epoch and dep[1] and dep[2][0] is None and \
                    not dep[0].startswith('rpmlib('):
                self.output.add_info('W', pkg, 'no-epoch-in-dependency', value)
            # Check if a package has a invalid-dependency in spec file
            for req in self.invalid_requires:
                if req.search(dep[0]):
                    self.output.add_info('E', pkg, 'invalid-dependency', dep[0])

            # Check if a dependency requirement starts with /usr/local
            # For Ex:- Requires: /usr/local/something
            if dep[0].startswith('/usr/local/'):
                self.output.add_info('E', pkg, 'invalid-dependency', dep[0])

            # Check if a package contains a dependency whose name is not docile with
            # lib64 naming standards.
            if is_source:
                if lib_devel_number_regex.search(dep[0]):
                    self.output.add_info('E', pkg, 'invalid-build-requires', dep[0])

            # Check if a package containing a devel dependency
            # is not a devel package itself
            elif not is_devel:
                if not devel_depend and FilesCheck.devel_regex.search(dep[0]):
                    self.output.add_info('E', pkg, 'devel-dependency', dep[0])
                    devel_depend = True
                if not dep[1]:
                    res = lib_package_regex.search(dep[0])
                    # Check if a package cannot find the lib dependencies by itself
                    # without the packager using explicit Requires: TagsCheck
                    # For Ex:- Requires: lib*
                    if res and not res.group(1):
                        self.output.add_info('E', pkg, 'explicit-lib-dependency', dep[0])

            # Check if a package requires a specfic version of another package.
            # For Ex:- Requires: python==3.8
            if dep[1] == rpm.RPMSENSE_EQUAL and dep[2][2] is not None:
                self.output.add_info('W', pkg, 'requires-on-release', value)
            self._unexpanded_macros(pkg, 'dependency {}'.format(value,), value)

    def _check_multiple_tags(self, pkg, name, is_devel,
                             is_source, deps, epoch, version):
        """Trigger checks no-name-tag check, no-dependency-on,
        no-version-dependency-on, missing-dependency-on,
        no-major-in-name, no-provides, no-pkg-config-provides

        Args:
            name: Variable to find if Name: tag

        Returns:
            Output info to STDOUT
        """

        if not name:
            # Check if a package does not have a Name: tag
            self.output.add_info('E', pkg, 'no-name-tag')
        else:
            if is_devel and not is_source:
                base = is_devel.group(1)
                dep = None
                has_so = False
                has_pc = False
                for fname in pkg.files:
                    if fname.endswith('.so'):
                        has_so = True
                    if pkg_config_regex.match(fname) and fname.endswith('.pc'):
                        has_pc = True
                if has_so:
                    base_or_libs = base + '*' + '/' + base + '-libs/lib' + base + '*'
                    # try to match *%_isa as well (e.g. '(x86-64)', '(x86-32)')
                    base_or_libs_re = re.compile(
                        r'^(lib)?%s(-libs)?[\d_-]*(\(\w+-\d+\))?$' % re.escape(base))
                    for d in deps:
                        if base_or_libs_re.match(d[0]):
                            dep = d
                            break
                    if not dep:
                        self.output.add_info('W', pkg, 'no-dependency-on', base_or_libs)
                    elif version:
                        epoch = str(epoch)
                        exp = (epoch, version, None)
                        sexp = Pkg.versionToString(exp)
                        if not dep[1]:
                            self.output.add_info('W', pkg, 'no-version-dependency-on',
                                                 base_or_libs, sexp)
                        elif dep[2][:2] != exp[:2]:
                            version = Pkg.versionToString((dep[2][0], dep[2][1], None))
                            self.output.add_info('W', pkg,
                                                 'missing-dependency-on',
                                                 f'{base_or_libs} = {version}')
                    res = devel_number_regex.search(name)
                    if not res:
                        self.output.add_info('W', pkg, 'no-major-in-name', name)
                    else:
                        if res.group(3):
                            prov = res.group(1) + res.group(2) + '-devel'
                        else:
                            prov = res.group(1) + '-devel'

                        if prov not in (x[0] for x in pkg.provides):
                            self.output.add_info('W', pkg, 'no-provides', prov)

                if has_pc:
                    found_pkg_config_dep = False
                    for p in (x[0] for x in pkg.provides):
                        if p.startswith('pkgconfig('):
                            found_pkg_config_dep = True
                            break
                    if not found_pkg_config_dep:
                        self.output.add_info('E', pkg, 'no-pkg-config-provides')

    def _check_summary_tag(self, pkg, summary, langs, ignored_words):
        """Trigger check no-summary-tag

        Check if a package does not have a summary tag

        Args:
            summary: Variable to find Summary: tag
            langs:
                Variable to find RPMTAG_HEADERI18NTABLE which
                Contains a list of locales for which strings are provided in other parts of
                the package.
            ignored_words: Find ignored words list in the Require: tag

        Returns:
            Output info to STDOUT
        """
        if summary:
            if not langs:
                self._unexpanded_macros(pkg, 'Summary', summary)
            else:
                for lang in langs:
                    self.check_summary(pkg, lang, ignored_words)
        else:
            self.output.add_info('E', pkg, 'no-summary-tag')

    def _check_description_tag(self, pkg, description, langs, ignored_words):
        """Trigger check description-shorter-than-summary, no-description-tag

        Args:
            description: Find %description tag in package

        Returns:
            Output info to STDOUT
        """
        if description:
            if not langs:
                self._unexpanded_macros(pkg, '%description', description)
            else:
                for lang in langs:
                    self.check_description(pkg, lang, ignored_words)

            # Check if a package has a description shorter than Summary
            if len(description) < len(pkg[rpm.RPMTAG_SUMMARY]):
                self.output.add_info('W', pkg, 'description-shorter-than-summary')
        else:
            # Check if a package does not have a %description tag in spec file
            self.output.add_info('E', pkg, 'no-description-tag')

    def _check_group_tag(self, pkg, group):
        """Trigger check no-group-tag, devel-package-with-non-devel-group,
        non-standard-group

        Args:
            group: Find Group: tag in package

        Returns:
            Output info to STDOUT
        """
        self._unexpanded_macros(pkg, 'Group', group)
        # Check if a package does not have a group tag
        if not group:
            self.output.add_info('E', pkg, 'no-group-tag')
        # Check if a package name end with -devel but
        # has a Group: tag with value start other than Development/
        elif pkg.name.endswith('-devel') and not group.startswith('Development/'):
            self.output.add_info('W', pkg, 'devel-package-with-non-devel-group', group)
        # Check if a package has a non-standard-group
        # which does not comply with the standard group list
        elif self.valid_groups and group not in self.valid_groups:
            self.output.add_info('W', pkg, 'non-standard-group', group)

    def _check_buildhost_tag(self, pkg, buildhost):
        """Trigger check no-buildhost-tag, invalid-buildhost

        Args:
            buildhost: Variable to find BuildHost: tag_regex

        Returns:
            Output info to STDOUT
        """
        self._unexpanded_macros(pkg, 'BuildHost', buildhost)
        # Check if a package has no buildhost tag
        if not buildhost:
            self.output.add_info('E', pkg, 'no-buildhost-tag')
        # Check if a package has a invalid-buildhost which does not comply
        # with configuration ValidBuildHost
        elif self.config.configuration['ValidBuildHost'] and \
                not self.valid_buildhost_regex.search(buildhost):
            self.output.add_info('W', pkg, 'invalid-buildhost', buildhost)

    def _check_changelog_tag(self, pkg, changelog, version, release, name, epoch):
        """Trigger multiple check of type *-changelog, *-changelogname-*, changelog-*
        and forbidden-controlchar

        Contains all the checks that cause an issue during build of the rpm
        in the %changelog of the specfile

        Args:
            changelog: Find the %changelog in the specfile

        Returns:
            Output info to STDOUT
        """

        # Check if a package does not have a %changelog in its spec file
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
                # Check if a package does not have version in the %changelog in latest version
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
                        # Check if a package does not have a version that is
                        # compatible with epoch:vesrion-release tuple
                        if ret.group(1) not in expected:
                            if len(expected) == 1:
                                expected = expected[0]
                            self.output.add_info('W', pkg, 'incoherent-version-in-changelog',
                                                 ret.group(1), expected)
            if clt:
                changelog = changelog + clt
            for deptoken in changelog:
                dep = Pkg.has_forbidden_controlchars(deptoken)
                # Check if a package contains a forbidden character in %changelog
                if dep:
                    self.output.add_info('E', pkg, 'forbidden-controlchar-found', '%%changelog : %s' % dep)
                    break

            clt = pkg[rpm.RPMTAG_CHANGELOGTIME][0]
            if clt:
                clt -= clt % (24 * 3600)  # roll back to 00:00:00, see #246
                # Check if a package contains a changelog entry that is suspiciously too far behind
                if clt < oldest_changelog_timestamp:
                    self.output.add_info('W', pkg, 'changelog-time-overflow',
                                         time.strftime('%Y-%m-%d', time.gmtime(clt)))
                # Check if a package contians a entry in %changelog
                # with timestamp thats in the future of its writing
                elif clt > time.time():
                    self.output.add_info('E', pkg, 'changelog-time-in-future',
                                         time.strftime('%Y-%m-%d', time.gmtime(clt)))

    def _check_license(self, pkg, rpm_license):
        """Trigger check no-license, invalid-license-exception, invalid-license

        Checks are triggered due to the configuration set by the user in the configdefaults.toml

        Args:
            rpm_license: Find License: tag in the rpm package

        Returns:
            Output info to STDOUT
        """

        def split_license(text):
            return (x.strip() for x in
                    (i for i in license_regex.split(text) if i))

        def split_license_exception(text):
            x, y = license_exception_regex.split(text)[1:3] or (text, '')
            return x.strip(), y.strip()

        # Check if a package spec file conatins a License: tag
        if not rpm_license:
            self.output.add_info('E', pkg, 'no-license')
        else:
            valid_license = True
            if rpm_license not in self.valid_licenses:
                license_string = rpm_license

                l1, lexception = split_license_exception(rpm_license)
                # SPDX allows "<license> WITH <license-exception>"
                if lexception:
                    license_string = l1
                    # Check if a package contains 'with <x>' license exception
                    if lexception not in self.valid_license_exceptions:
                        self.output.add_info('W', pkg, 'invalid-license-exception', lexception)
                        valid_license = False

                for l1 in split_license(license_string):
                    if l1 in self.valid_licenses:
                        continue
                    for l2 in split_license(l1):
                        # Check if a package has a License: value other than ValidLicenses
                        if l2 not in self.valid_licenses:
                            self.output.add_info('W', pkg, 'invalid-license', l2)
                            valid_license = False
            if not valid_license:
                self._unexpanded_macros(pkg, 'License', rpm_license)

    def _check_url(self, pkg):
        """Trigger check invalid-url, no-url-tag """
        for tag in ('URL', 'DistURL', 'BugURL'):
            if hasattr(rpm, 'RPMTAG_{}'.format(tag.upper())):
                url = byte_to_string(pkg[getattr(rpm, 'RPMTAG_{}'.format(tag.upper()))])
                self._unexpanded_macros(pkg, tag, url, is_url=True)
                if url:
                    (scheme, netloc) = urlparse(url)[0:2]
                    # Check if a package contains a unreasonable URL
                    # [This check is also triggered with Source: tag value]
                    if not scheme or not netloc or '.' not in netloc or \
                            scheme not in ('http', 'https', 'ftp') or \
                            (self.config.configuration['InvalidURL'] and
                             self.invalid_url_regex.search(url)):
                        self.output.add_info('W', pkg, 'invalid-url', tag, url)
                # Check if a package does not have a URL: tag in its spec file
                elif tag == 'URL':
                    self.output.add_info('W', pkg, 'no-url-tag')

    def _check_obsolete_not_provided(self, pkg, prov_names):
        """Check if a package has the obsoleted package still provided
        in spec file to avoid dependency breakage

        Args:
            prov_names: Find the value of Provides: tag in specfile

        Returns:
            Output info to STDOUT
        """
        obs_names = [x[0] for x in pkg.obsoletes]
        for dep_token in (x for x in obs_names if x not in prov_names):
            self.output.add_info('W', pkg, 'obsolete-not-provided', dep_token)

    def _check_useless_provides(self, pkg, prov_names):
        """Trigger check useless-provides

        Check if a package has a multiple number of Provides: of the same dependency
        example:
        Provides: foo
        Provides: foo = 1.0

        Returns:
            Output info to STDOUT
        """

        # TODO: should take versions, <, <=, =, >=, > into account here
        #       https://bugzilla.redhat.com/460872
        useless_provides = set()
        for prov in prov_names:
            if (prov_names.count(prov) != 1 and
                    not prov.startswith('debuginfo(') and
                    prov not in useless_provides):
                useless_provides.add(prov)
        for prov in sorted(useless_provides):
            self.output.add_info('E', pkg, 'useless-provides', prov)

    def _check_forbidden_controlchar(self, pkg):
        """Trigger check forbidden-controlchar-found

        Check if package contains a forbidden_words or character in
        tags: Provides, Conflicts, Obsoletes,
        Supplements, Suggests, Enhances, Recommends and Requires

        Returns:
            Output info to STDOUT
        """

        for tagname, items in (
                ('Provides', pkg.provides),
                ('Conflicts', pkg.conflicts),
                ('Obsoletes', pkg.obsoletes),
                ('Supplements', pkg.supplements),
                ('Suggests', pkg.suggests),
                ('Enhances', pkg.enhances),
                ('Recommends', pkg.recommends)):
            for item in items:
                dep = Pkg.has_forbidden_controlchars(item)
                if dep:
                    self.output.add_info('E',
                                         pkg,
                                         'forbidden-controlchar-found',
                                         '{}: {}'.format(tagname, dep))
                value = Pkg.formatRequire(*item)
                self._unexpanded_macros(pkg, '{} {}'.format(tagname, value), value)

            # Check if a package contains forbidden-controlchar in Requires: tag.
            for pkg_token in (pkg.requires):
                dep = Pkg.has_forbidden_controlchars(pkg_token)
                if dep:
                    self.output.add_info('E',
                                         pkg,
                                         'forbidden-controlchar-found',
                                         'Requires: {}'.format(dep))

    def _check_self_obsoletion(self, pkg):
        """Trigger check self-obsoletion

        Check if a package does not obsoletes itself
        example:
        Name: lib-devel and Obsoletes: lib-devel in its spec file

        Returns:
        Output info to STDOUT
        """
        obss = pkg.obsoletes
        if obss:
            provs = pkg.provides
            for prov in provs:
                for obs in obss:
                    if Pkg.rangeCompare(obs, prov):
                        self.output.add_info('W', pkg,
                                             'self-obsoletion',
                                             '{} obsoletes {}'.format(Pkg.formatRequire(*obs),
                                                                      Pkg.formatRequire(*prov)))

    def _check_non_coherent_filename(self, pkg):
        """Trigger check in non-coherent-filename

        Check if a package has a
        named <NAME>-<VERSION>-<RELEASE>.<ARCH>.rpm in this order

        Returns:
        Output info STDOUT
        """
        expfmt = rpm.expandMacro('%{_build_name_fmt}')
        if pkg.is_source:
            # _build_name_fmt often (always?) ends up not outputting src/nosrc
            # as arch for source packages, do it ourselves
            expfmt = re.sub(r'(?i)%\{?ARCH\b\}?', pkg.arch, expfmt)
        expected = pkg.header.sprintf(expfmt).split('/')[-1]
        basename = Path(pkg.filename).name
        if basename != expected:
            self.output.add_info('W', pkg, 'non-coherent-filename', basename, expected)
