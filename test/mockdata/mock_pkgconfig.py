from Testing import get_tested_mock_package


XCB_PC = """
prefix=/usr
exec_prefix=/usr
libdir=/var/tmp/usr/lib64
includedir=/usr/include//xyz

Name: XCB Xinerama
Description: XCB Xinerama Extension
Version: 1.13
Requires.private: xcb
Libs: -L/usr/lib
Cflags: -I${includedir}
"""


PCPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/tmp/pkgconfig/xcb.pc': {'content': XCB_PC},
    },
    header={'arch': 'x86_64'},
)


LibReiserFSCoreDevelPackage = get_tested_mock_package(
    name='libreiserfscore-devel',
    lazyload=True,
    files={
        '/usr/include/reiserfs/io.h': {
            'content-path': 'files/reiserfs/io.h',
        },
        '/usr/include/reiserfs/misc.h': {
            'content-path': 'files/reiserfs/misc.h',
        },
        '/usr/include/reiserfs/reiserfs_err.h': {
            'content-path': 'files/reiserfs/reiserfs_err.h',
        },
        '/usr/include/reiserfs/reiserfs_fs.h': {
            'content-path': 'files/reiserfs/reiserfs_fs.h',
        },
        '/usr/include/reiserfs/reiserfs_lib.h': {
            'content-path': 'files/reiserfs/reiserfs_lib.h',
        },
        '/usr/include/reiserfs/swab.h': {
            'content-path': 'files/reiserfs/swab.h',
        },
        '/usr/lib64/libreiserfscore.a': {
            'content-path': 'files/reiserfs/libreiserfscore.a',
        },
        '/usr/lib64/libreiserfscore.la': {
            'content-path': 'files/reiserfs/libreiserfscore.la',
        },
        '/usr/lib64/libreiserfscore.so': {
            'link-to': 'libreiserfscore.so.0.0.0',
        },
        '/usr/lib64/libreiserfscore.so.0': {
            'link-to': 'libreiserfscore.so.0.0.0',
        },
        '/usr/lib64/pkgconfig/reiserfscore.pc': {
            'content-path': 'files/reiserfs/reiserfscore.pc',
        },
    },
    header={
        'requires': [
            '/usr/bin/pkg-config',
            'libcom_err-devel',
            'libreiserfscore0 = 3.6.27',
            'libuuid-devel',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ],
    },
)
