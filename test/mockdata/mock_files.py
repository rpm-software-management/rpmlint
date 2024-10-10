import stat

import rpm

from Testing import get_tested_mock_package


UnexpandedMacroFilesPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/%{unexpanded}/test': {},
        '/usr/bin/unexpanded-macro-files': {'is_dir': True},
        '/usr/share/licenses/unexpanded-macro-files': {'is_dir': True},
        '/usr/share/licenses/unexpanded-macro-files/LICENSE': {},
    },
    header={'requires': []},
)


Python3PowerPackage = get_tested_mock_package(
    name='python3-power',
    lazyload=True,
    header={'requires': ['python(abi) = 3.3']},
    files={
        '/usr/lib/python3.3/site-packages/power/__init__.py': {
            'content-path': 'files/python3-power/__init__.py',
            'metadata': {'mtime': 1_363_887_182},
        },
        '/usr/lib/python3.3/site-packages/power/common.py': {
            'content-path': 'files/python3-power/common.py',
            'metadata': {'mtime': 1_363_887_182},
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/__init__.cpython-33.pyc': {
            'content-path': 'files/python3-power/__init__.cpython-33.pyc',
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/__init__.cpython-33.pyo': {
            'content-path': 'files/python3-power/__init__.cpython-33.pyo',
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/common.cpython-33.pyc': {
            'content-path': 'files/python3-power/common.cpython-33.pyc',
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/common.cpython-33.pyo': {
            'content-path': 'files/python3-power/common.cpython-33.pyo',
        },
        '/usr/share/doc/python3-power-1.1/index.html': {
            'metadata': {'flags': rpm.RPMFILE_DOC, 'size': 100},
        },
    },
)


Python3PowerBrokenPackage = Python3PowerPackage.clone(
    files={
        '/usr/lib/python3.3/site-packages/power/__init__.py': {
            'content-path': 'files/python3-power/__init__.py',
            'metadata': {'mtime': 1_363_887_182},
        },
        '/usr/lib/python3.3/site-packages/power/__pycache__/__init__.cpython-33.pyc': {
            'content': 'BROKEN-MAGIC-PYC',
        },
        '/usr/share/doc/python3-power-1.1/index.html': {
            'metadata': {'flags': rpm.RPMFILE_DOC, 'size': 100},
        },
    },
)


TestDocumentationPackage = get_tested_mock_package(
    name='testdocumentation',
    lazyload=True,
    files={
        'usr/share/doc/packages/testdocumentation': {'is_dir': True},
        '/usr/share/doc/packages/testdocumentation/README1.gz': {
            'content-path': 'files/README1.gz',
            'metadata': {'flags': rpm.RPMFILE_DOC},
        },
        '/usr/share/doc/packages/testdocumentation/README2.bz2': {
            'content-path': 'files/README2.bz2',
            'metadata': {'flags': rpm.RPMFILE_DOC},
        },
        '/usr/share/doc/packages/testdocumentation/README3.xz': {
            'content-path': 'files/README3.xz',
            'metadata': {'flags': rpm.RPMFILE_DOC},
        },
    },
    header={'requires': {}},
)


NetmaskDebugsourcePackage = get_tested_mock_package(
    lazyload=True,
    name='netmask-debugsource',
    files={
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/errors.c': {
            'content-path': 'files/netmask/errors.c',
        },
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/errors.h': {
            'content-path': 'files/netmask/errors.h',
        },
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/main.c': {
            'content-path': 'files/netmask/main.c',
        },
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/netmask.c': {
            'content-path': 'files/netmask/netmask.c',
        },
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/netmask.h': {
            'content-path': 'files/netmask/netmask.h',
        },
    },
    header={
        'version': '2.4.3',
        'release': '5.fc27',
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ]
    }
)

MakefileJunkPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/share/CMakeLists.txt': {},
        '/usr/share/Makefile.am': {'metadata': {'flags': rpm.RPMFILE_DOC}},
        '/usr/share/Makefile.in': {},
        '/usr/share/selinux': {'is_dir': True},
        '/usr/share/selinux/Makefile': {},
        '/usr/src/foo': {'is_dir': True},
        '/usr/src/foo/Makefile': {}
    },
    header={'requires': []},
)

SphinxInvPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/share/doc/packages/python3-greenlet/html/objects.inv': {
            'metadata': {'flags': rpm.RPMFILE_DOC},
            'content': '# Sphinx inventory version 2',
        },
    },
    header={'requires': []},
)


FileChecksPackage = get_tested_mock_package(
    lazyload=True,
    files=[
        '/run/foo',
        '/etc/systemd/system/foo',
        '/etc/udev/rules.d/foo',
        '/etc/tmpfiles.d/foo',
        '/bin/foo/bar',
        '/site_perl/foo',
        '/~backup.rej',
        '/.gitignore',
        '/.htaccess',
        '/usr/share/doc/perl-foo/MANIFEST',
        '/usr/info/dir',
    ],
    header={'requires': []},
)


TclPackage = get_tested_mock_package(
    lazyload=True,
    files=['/usr/lib64/tcl/pkgIndex.tcl'],
    header={'requires': []},
)


RustFilesPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/etc/bar.rs': {
            'content': '#![allow(box_pointers)]',
            'metadata': {'mode': 0o644 | stat.S_IFREG},
        },
        '/etc/foo.rs': {
            'content': '#![allow(box_pointers)]',
            'metadata': {'mode': 0o755 | stat.S_IFREG},
        },
    },
    header={'requires': []},
)


ManPagesPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/etc/ngircd.conf': {'content': 'conf'},
        '/usr/sbin/ngircd': {'content': 'XXXX', 'metadata': {'mode': 0o755 | stat.S_IFREG}},
        '/usr/share/man/man5/ngircd.conf.5.gz': {'content': 'gz'},
        '/usr/share/man/man8/ngircd.8.gz': {'content': 'gz', 'metadata': {'flags': rpm.RPMFILE_DOC}},
    },
    header={'requires': []},
)


DevelopmentPackage = get_tested_mock_package(
    lazyload=True,
    name='my-package-devel',
    files={
        '/usr/x.typelib': {'metadata': {'size': 100}},
    },
    header={'requires': []},
)


Shlib1Package = get_tested_mock_package(
    name='shlib1',
    lazyload=True,
    files={
        '/usr/lib/libfoo-2.so': {
            'content-path': 'files/shlib2/libfoo-2.so',
            'metadata': {'mode': 0o755 | stat.S_IFREG},
        },
        '/usr/lib/libfoo-2.so.foo': {
            'content-path': 'files/shlib2/libfoo-2.so.foo',
            'metadata': {'mode': 0o644 | stat.S_IFREG},
        },
        '/usr/lib/libfoo.so': {
            'linkto': 'libfoo.so.1',
            'metadata': {'mode': 0o777 | stat.S_IFREG},
        },
        '/usr/lib/libfoo.so.1': {
            'content-path': 'files/shlib2/libfoo.so.1',
            'metadata': {'mode': 0o755 | stat.S_IFREG},
        },
    },
    header={'requires': []},
)
Shlib2DevelPackage = Shlib1Package.clone(name='shlib2-devel')


FileZeroLengthPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib/python': {'is_dir': True},
        # Ok files
        '/etc/security/console.apps/myapp': {
            'create_dirs': True,
            'metadata': {
                'mode': 0o644 | stat.S_IFREG,
                'size': 100,
                'flags': rpm.RPMFILE_CONFIG,
            },
        },
        '/etc/share/doc/packages/file-zero-length/dummydoc': {
            'create_dirs': True,
            'metadata': {
                'mode': 0o644 | stat.S_IFREG,
                'size': 100,
                'flags': rpm.RPMFILE_DOC,
            },
        },
        '/usr/lib/nonemptyfile': {
            'metadata': {'mode': 0o644 | stat.S_IFREG, 'size': 100},
        },
        # Not Ok file
        '/usr/lib/emptyfile': {'metadata': {'mode': 0o644 | stat.S_IFREG}},
        # Ignored by normal_zero_length_regex
        '/usr/lib/.nosearch': {'metadata': {'mode': 0o644 | stat.S_IFREG}},
        '/usr/lib/python/__init__.py': {'metadata': {'mode': 0o644 | stat.S_IFREG}},
        '/usr/lib/python/py.typed': {'metadata': {'mode': 0o644 | stat.S_IFREG}},
        '/usr/lib/python/pypackagefromwheel-0.0.0.dist-info/REQUESTED': {'metadata': {'mode': 0o644 | stat.S_IFREG}},
        '/usr/lib/ruby/gem.build_complete': {'metadata': {'mode': 0o644 | stat.S_IFREG}},
    },
    header={'requires': []},
)


ManualPagesPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/share/man/man0p': {'is_dir': True},
        '/usr/share/man/man0p/foo.3.gz': {},
        '/usr/share/man/man1': {'is_dir': True},
        '/usr/share/man/man1/test.1.zst': {},
        '/usr/share/man/man3': {'is_dir': True},
        '/usr/share/man/man3/foo': {'is_dir': True},
        '/usr/share/man/man3/foo/bar': {'is_dir': True},
        '/usr/share/man/man3/foo/bar/baz.3.gz': {},
        '/usr/share/man/man3/some.3pm.gz': {}
    },
    header={'requires': []},
)


PythonShebangLinkPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/share/package/bin.py': {
            'content': '#!/usr/bin/python3\nprint("python required")',
            'metadata': {'mode': 0o755 | stat.S_IFREG},
        },
        '/usr/bin/testlink': {
            'linkto': '../share/package/bin.py',
        },
    },
    header={},
)
PythonShebangLinkOkPackage = PythonShebangLinkPackage.clone(
    header={'requires': ['/usr/bin/python3']},
)


DirectoryWithoutXPermPackage = get_tested_mock_package(
    lazyload=True,
    header={'requires': []},
    files={
        '/etc/raddb/mods-config/sql/moonshot-targeted-ids/mysql': {
            'is_dir': True,
            'metadata': {'mode': 0o640 | stat.S_IFDIR},
        },
        '/etc/raddb/mods-config/sql/moonshot-targeted-ids/postgresql': {
            'is_dir': True,
            'metadata': {'mode': 0o640 | stat.S_IFDIR},
        },
        '/etc/raddb/mods-config/sql/moonshot-targeted-ids/sqlite': {
            'is_dir': True,
            'metadata': {'mode': 0o640 | stat.S_IFDIR},
        },
    },
)


DirectoryWithoutXPerm2Package = get_tested_mock_package(
    lazyload=True,
    header={'requires': []},
    files={
        '/etc/raddb': {'is_dir': True, 'metadata': {'mode': 0o640 | stat.S_IFDIR}},
        '/etc/raddb/certs': {'is_dir': True, 'metadata': {'mode': 0o640 | stat.S_IFDIR}},
        '/etc/raddb/mods-available': {'is_dir': True, 'metadata': {'mode': 0o640 | stat.S_IFDIR}},
        '/etc/raddb/mods-config': {'is_dir': True, 'metadata': {'mode': 0o640 | stat.S_IFDIR}},
        '/etc/raddb/policy.d': {'is_dir': True, 'metadata': {'mode': 0o640 | stat.S_IFDIR}},
        '/etc/raddb/sites-available': {'is_dir': True, 'metadata': {'mode': 0o640 | stat.S_IFDIR}},
        '/etc/raddb/sites-enabled': {'is_dir': True, 'metadata': {'mode': 0o640 | stat.S_IFDIR}},
        '/usr/lib64/freeradius': {'is_dir': True, 'metadata': {'mode': 0o640 | stat.S_IFDIR}},
        '/usr/share/freeradius': {'is_dir': True, 'metadata': {'mode': 0o640 | stat.S_IFDIR}},
    },
)


FilesWithoutPermsPackage = get_tested_mock_package(
    lazyload=True,
    header={'requires': []},
    files={
        '/var/lib/pipewire': {'is_dir': True, 'metadata': {'mode': 0o000 | stat.S_IFDIR}},
        '/var/lib/dir_read': {'is_dir': True, 'metadata': {'mode': 0o755 | stat.S_IFDIR}},
        '/var/lib/pipewire/ghost_file': {'metadata': {'mode': 0o000, 'flags': rpm.RPMFILE_GHOST}},
        '/var/lib/pipewire/ghost_file_read': {'metadata': {'mode': 0o644, 'flags': rpm.RPMFILE_GHOST}},
        '/var/lib/pipewire/normal_file': {'metadata': {'mode': 0o000}},
        '/var/lib/pipewire/normal_file_read': {'metadata': {'mode': 0o644}},
    },
)


FilesWithoutPermsTmpfilesPackage = get_tested_mock_package(
    lazyload=True,
    header={'requires': []},
    files={
        '/run/netconfig/resolv.conf': {'metadata': {'mode': 0o000, 'flags': rpm.RPMFILE_GHOST}},
        '/run/netconfig/yp.conf': {'metadata': {'mode': 0o644, 'flags': rpm.RPMFILE_GHOST}},
        '/run/netconfig': {'is_dir': True, 'metadata': {'mode': 0o000, 'flags': rpm.RPMFILE_GHOST | stat.S_IFDIR}},
        '/usr/lib/tmpfiles.d/netconfig.conf': {
            'content': """
d /run/netconfig 0755 root group -
f /run/netconfig/resolv.conf 0644 root root -
f /run/netconfig/yp.conf 0644 root root -
"""
        },
    },
)
