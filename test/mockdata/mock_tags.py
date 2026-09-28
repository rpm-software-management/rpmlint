import rpm

from Testing import get_tested_mock_package


UnexpandedMacroPackage = get_tested_mock_package(
    lazyload=True,
    name='unexpanded1',
    header={
        'requires': [],
        'provides': ['/%notreally', 'unexpanded1 = 0-0'],
        'suggests': ['/%asdf'],
        'conflicts': ['something:%unexpanded_conflicts'],
        'enhances': ['/%else'],
        'obsoletes': ['something:%unexpanded'],
        'recommends': ['/%unxpanded_recommends'],
        'supplements': ['/%something'],
        'arch': 'noarch',
        'name': 'unexpanded1',
        'version': '0',
        'release': '0',
    },
)


SelfPackage = get_tested_mock_package(
    lazyload=True,
    name='self',
    header={
        'requires': [
            'insserv',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
            'xinetd',
        ],
        'provides': [
            'self',
            'self = 0-0',
            'self(x86-64) = 0-0',
        ],
        'arch': 'x86_64',
        'name': 'self',
        'version': '0',
        'release': '0',
    },
)


FuseCommonPackage = get_tested_mock_package(
    lazyload=True,
    name='fuse-common',
    files={
        'etc/fuse.conf': {
            'content': '# mount_max = 1000\nuser_allow_other\n',
            'flags': rpm.RPMFILE_NOREPLACE | rpm.RPMFILE_CONFIG,
        },
    },
    header={
        'requires': [
            'config(fuse-common) = 3.10.2-5.el8',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ],
        'provides': [
            'config(fuse-common) = 3.10.2-5.el8',
            'fuse-common = 3.10.2-5.el8',
            'fuse-common = 3.2.1',
            'fuse-common = 3.3.0',
            'fuse-common(x86-64) = 3.10.2-5.el8',
        ],
        'arch': 'x86_64',
        'name': 'fuse-common',
        'version': '3.10.2',
        'release': '5.el8',
    },
)


FooDevelPackage = get_tested_mock_package(
    lazyload=True,
    name='foo-devel',
    header={
        'requires': [],
        'provides': [],
        'arch': 'x86_64',
        'name': 'foo-devel',
        'version': '0',
        'release': '0',
        'group': 'Games',
        'license': 'GPL-2.0+',
        'url': 'http://www.opensuse.org/',
        'buildhost': 'marxinbox.suse.cz',
        'summary': 'Lorem ipsum',
        'description': """Lorem ipsum dolor sit amet, consectetur adipisici elit, sed
eiusmod tempor incidunt ut labore et dolore magna aliqua. Ut enim
ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut
aliquid ex ea commodi consequat. Quis aute iure reprehenderit in
voluptate velit esse cillum dolore eu fugiat nulla pariatur.
Excepteur sint obcaecat cupiditat non proident, sunt in culpa qui
officia deserunt mollit anim id est laborum.
""",
        'changelogname': ['daniel.garcia@suse.com'],
        'changelogtime': [1303128000],
        'changelogtext': ['dummy'],
    },
)


MissingProvidesPackage = get_tested_mock_package(
    lazyload=True,
    name='missingprovides-devel',
    files=['/usr/lib64/pkgconfig/libparted.pc'],
    header={
        'requires': [],
        'provides': [],
        'arch': 'x86_64',
        'name': 'missingprovides-devel',
        'version': '0',
        'release': '0',
    },
)


InvalidExceptionPackage = MissingProvidesPackage.clone(
    extend=True,
    name='invalid-exception',
    header={
        'name': 'invalid-exception',
        'license': 'GPL-2.0+ WITH sparta',
    },
)


ValidExceptionPackage = InvalidExceptionPackage.clone(
    extend=True,
    name='valid-exception',
    header={
        'name': 'valid-exception',
        'license': 'GPL-2.0+ WITH 389-exception',
    },
)


DepsPackage = get_tested_mock_package(
    lazyload=True,
    name='pkg',
    header={
        'requires': [
            'expat-devel',
            'libexplicit',
        ],
        'ARCH': 'noarch',
        'NAME': 'pkg',
        'VERSION': '5.6.3',
        'RELEASE': '2.fc39',
        'EPOCH': 1,
    },
)


DepsDevPackage = DepsPackage.clone(
    extend=True,
    name='pkg-devel',
)


ForbiddenControlcharRequiresPackage = get_tested_mock_package(
    lazyload=True,
    name='forbidden-controlchar-requires',
    header={
        'requires': ['ksym(default:\x02)'],
        'arch': 'x86_64',
        'name': 'forbidden-controlchar-requires',
        'version': '0',
        'release': '0',
    },
)


ForbiddenControlcharChangelogPackage = get_tested_mock_package(
    lazyload=True,
    name='forbidden-controlchar-changelog',
    header={
        'arch': 'x86_64',
        'name': 'forbidden-controlchar-changelog',
        'version': '2.0.1',
        'release': '1.1',
        'changelogname': ['Stephan Kulow <coolo@suse.com>'],
        'changelogtime': [1557057600],
        'changelogtext': ['- updated to version 2.0.1\n  see installed CHANGELOG\n  2.0.0 -- Changed p_ separator to \x04'],
    },
)


ForbiddenControlcharSpecPackage = get_tested_mock_package(
    lazyload=True,
    name='SpecCheck4',
    header={
        'requires': ['require\x06'],
        'provides': ['provide\x06'],
        'obsoletes': ['obsolete\x06'],
        'conflicts': ['conflict\x06'],
        'arch': 'x86_64',
        'name': 'SpecCheck4',
        'version': '0.0.1',
        'release': '0',
        'changelogname': ['Frank Schreiner <frank@fs.samaxi.de>'],
        'changelogtime': [1500000000],
        'changelogtext': ['- changelog entry .... \x06'],
    },
)


UnexpandedMacroExpPackage = UnexpandedMacroPackage.clone(
    extend=True,
    name='unexpanded-macro-exp',
    header={
        'name': 'unexpanded-macro-exp',
        'packager': 'someone%ppc',
        'group': 'Undefined%ppc',
        'provides': ['/something%ppc'],
        'conflicts': ['something:%ppc'],
        'recommends': ['/%ppc'],
        'suggests': ['/%ppc'],
        'enhances': ['/%ppc'],
        'supplements': ['packageand(python-gobject:%{gdk_real_package})%ppc'],
    },
)


InvalidVersionPackage = get_tested_mock_package(
    lazyload=True,
    name='invalid-version',
    header={
        'arch': 'x86_64',
        'name': 'invalid-version',
        'version': '0pre',
        'release': '3.1',
        'summary': 'no-epoch-tag warning',
    },
)


SummaryWarningPackage = get_tested_mock_package(
    lazyload=True,
    name='summary-warning',
    header={
        'headeri18ntable': ['C'],
        'arch': 'x86_64',
        'name': 'summary-warning',
        'version': '0',
        'release': '1.1',
        'summary': '\xa0\xa0lorem Ipsum is simply dummy text of the printing and typesetting industry   \xa0\xa0\xa0\xa0',
        'description': 'shorter description than summary.',
        'url': 'http://rpmlint.zarb.org/#summary-warning',
    },
)


NoUrlTagPackage = get_tested_mock_package(
    lazyload=True,
    name='no-url-tag',
    header={
        'headeri18ntable': ['C'],
        'arch': 'x86_64',
        'name': 'no-url-tag',
        'version': '0',
        'release': '0',
        'summary': 'no-url-tag warning.',
    },
)


InvalidLaFilePackage = get_tested_mock_package(
    lazyload=True,
    name='invalid-la-file',
    header={
        'headeri18ntable': ['C'],
        'arch': 'x86_64',
        'name': 'invalid-la-file',
        'version': '0',
        'release': '0',
        'summary': 'A package for invalid-la-file testing',
        'description': 'This package contains an .la file that contains a reference to /home\nthat is not allowed.',
        'url': 'https://www.invalid-la-file.com',
    },
)


MiscWarningsPackage = get_tested_mock_package(
    lazyload=True,
    name='misc-warnings',
    header={
        'headeri18ntable': ['C'],
        'arch': 'x86_64',
        'name': 'misc-warnings',
        'version': '0',
        'release': '0',
        'summary': 'package contains misc-warnings and errors',
        'description': 'Name: misc-warnings',
        'url': 'so;mething.',
    },
)


MiscNoWarningsPackage = get_tested_mock_package(
    lazyload=True,
    name='misc-no-warnings',
    header={
        'headeri18ntable': ['C'],
        'arch': 'x86_64',
        'name': 'misc-no-warnings',
        'version': '0',
        'release': '0',
        'summary': 'none',
        'description': 'A plain package without any tag warnings.',
        'url': 'https://build.opensuse.org',
    },
)


InvalidDependencyPackage = get_tested_mock_package(
    lazyload=True,
    name='invalid-dependency',
    header={
        'requires': ['/usr/local/something'],
        'arch': 'x86_64',
        'name': 'invalid-dependency',
        'version': '0',
        'release': '0',
        'epoch': 100,
        'summary': 'invalid-dependency warning',
    },
)


InvalidDependencyMultiplePackage = get_tested_mock_package(
    lazyload=True,
    name='invalid-dependency-multiple',
    header={
        'requires': ['/usr/bin/python3', '/bin/sh'],
        'arch': 'x86_64',
        'name': 'invalid-dependency-multiple',
        'version': '0.7.4',
        'release': '29.1',
        'summary': 'Windows Event Log files parser',
    },
)


RandomExpPackage = get_tested_mock_package(
    lazyload=True,
    name='random-exp',
    header={
        'headeri18ntable': ['C'],
        'requires': ['/usr/something/'],
        'obsoletes': ['python'],
        'arch': 'x86_64',
        'name': 'random-exp',
        'version': '0',
        'release': '0',
        'summary': 'random-exp warning',
        'description': 'This is ridiculously long description that has no meaning but is used to test the check description-line-too-long.',
        'license': 'MIT',
    },
)


RandomDevelPackage = get_tested_mock_package(
    lazyload=True,
    name='random-devel',
    header={
        'headeri18ntable': ['C'],
        'requires': ['python'],
        'provides': ['foo', 'foo = 2.1', 'random-devel = 0-2.1', 'random-devel(x86-64) = 0-2.1'],
        'obsoletes': ['random-devel'],
        'arch': 'x86_64',
        'name': 'random-devel',
        'version': '0',
        'release': '2.1',
        'summary': 'random-exp warning',
        'description': 'This is ridiculously good enough description.',
        'license': 'MIT',
    },
)


RequiresOnReleasePackage = get_tested_mock_package(
    lazyload=True,
    name='requires-on-release',
    header={
        'requires': ['baz = 2.1-1'],
        'arch': 'x86_64',
        'name': 'requires-on-release',
        'version': '0',
        'release': '1.1',
        'summary': 'requires-on-release warning',
    },
)


InvalidLicensePackage = get_tested_mock_package(
    lazyload=True,
    name='invalid-license',
    header={
        'arch': 'x86_64',
        'name': 'invalid-license',
        'version': '0',
        'release': '1.1',
        'summary': 'Invalid-license warning',
        'license': 'Apache License',
    },
)


NotStandardReleaseExtensionPackage = get_tested_mock_package(
    lazyload=True,
    name='not-standard-release-extension',
    header={
        'arch': 'x86_64',
        'name': 'not-standard-release-extension',
        'version': '0',
        'release': '1.1',
        'summary': 'not-standard-release-extension warning',
        'license': 'Apache-2.0',
    },
)


NonStandardGroupPackage = get_tested_mock_package(
    lazyload=True,
    name='non-standard-group',
    header={
        'arch': 'x86_64',
        'name': 'non-standard-group',
        'version': '0',
        'release': '2.1',
        'summary': 'non-standard-group warning',
        'group': 'non/standard/group',
        'license': 'Apache License',
    },
)


DevDependencyPackage = get_tested_mock_package(
    lazyload=True,
    name='dev-dependency',
    header={
        'requires': ['glibc-devel'],
        'arch': 'x86_64',
        'name': 'dev-dependency',
        'version': '0',
        'release': '3.1',
        'summary': 'devel-dependency warning',
        'group': 'Devel/Something',
        'license': 'MIT',
    },
)


SummaryOnMultipleLinesPackage = get_tested_mock_package(
    lazyload=True,
    name='summary-on-multiple-lines',
    header={
        'headeri18ntable': ['C'],
        'arch': 'x86_64',
        'name': 'summary-on-multiple-lines',
        'version': '1.0',
        'release': '0',
        'summary': 'summary\ron-multiple-lines',
        'description': 'A test package with a summary spread over multiple lines.',
    },
)


SpellingErrorDefaultPackage = get_tested_mock_package(
    lazyload=True,
    name='spellingerrors-default',
    header={
        'arch': 'x86_64',
        'name': 'spellingerrors-default',
        'version': '0',
        'release': '0',
        'summary': 'Spelling errors default',
        'description': 'This is ridiculously long description with spellling error.',
        'headeri18ntable': ['C'],
    },
)


SpellingErrorLangPackage = get_tested_mock_package(
    lazyload=True,
    name='spellingerrors-lang',
    header={
        'arch': 'x86_64',
        'name': 'spellingerrors-lang',
        'version': '0',
        'release': '0',
        'summary': 'Spelling errors lang',
        'description': "Ceci est une description riddiculement longue avec une faute d'orthographe.",
        'headeri18ntable': ['C', 'fr'],
    },
)
