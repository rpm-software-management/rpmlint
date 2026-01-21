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


ForbiddenControlCharPackage = get_tested_mock_package(
    lazyload=True,
    name='xtables-addons-kmp-default',
    files=[],
    header={
        'requires': [
            'ksym(default:',
            'ksym(default:\b)',
            'ksym(default:HX_memmem) = 55bffe85',
            'ksym(default:PDE_DATA) = e515007f',
            'ksym(default:__alloc_skb) = a57f3289'
        ],
        'provides': [],
        'arch': 'x86_64',
        'name': 'xtables-addons-kmp-default',
        'version': '0',
        'release': '0',
    },
)


ForbiddenControlCharChangelogPackage = get_tested_mock_package(
    lazyload=True,
    name='ruby2.6-rubygem-fast_gettext',
    files=[],
    header={
        'requires': [],
        'provides': [],
        'arch': 'x86_64',
        'name': 'ruby2.6-rubygem-fast_gettext',
        'version': '0',
        'release': '0',
        'changelog': [
            ['daniel.garcia@suse.com', 'Text', 1557057600],
            ['daniel.garcia@suse.com', 'Forbiddeen character \x04 in changelog', 1557057600],
        ],
    },
)


ForbiddenControlCharAllPackage = ForbiddenControlCharPackage.clone(
    extend=True,
    name='SpecCheck4',
    files=[],
    header={
        'requires': ['/bin/sh', 'require\x06', 'rpmlib(CompressedFileNames) <= 3.0.4-1'],
        'provides': ['SpecCheck4 = 0.0.1-0', 'SpecCheck4(x86-64) = 0.0.1-0', 'provide\x06'],
        'obsoletes': ['obsoletes\x06'],
        'conflicts': ['conflicts\x06'],
        'changelog': [
            ['daniel.garcia@suse.com', 'changelog entry .... \x06', 1557057600],
        ],
    },
)
