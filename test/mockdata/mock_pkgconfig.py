from Testing import get_tested_mock_package


PKGCONFIG = get_tested_mock_package(
files={
'/tmp/pkgconfig/xcb.pc': {'content': """
prefix=/usr
exec_prefix=/usr
libdir=/var/tmp/usr/lib64
includedir=/usr/include//xyz

Name: XCB Xinerama
Description: XCB Xinerama Extension
Version: 1.13
Requires.private: xcb
Libs: -L/usr/lib
Cflags: -I${includedir}"""}
},
header={
    'arch': 'x86_64'
})


PKGCONFIG2 = get_tested_mock_package(
files={
'/usr/include/reiserfs',
'/usr/include/reiserfs/io.h',
'/usr/include/reiserfs/misc.h',
'/usr/include/reiserfs/reiserfs_err.h',
'/usr/include/reiserfs/reiserfs_fs.h',
'/usr/include/reiserfs/reiserfs_lib.h',
'/usr/include/reiserfs/swab.h',
'/usr/lib64/libreiserfscore.a',
'/usr/lib64/libreiserfscore.la',
'/usr/lib64/libreiserfscore.so',
'/usr/lib64/libreiserfscore.so.0',
'/usr/lib64/pkgconfig/reiserfscore.pc'}
)
