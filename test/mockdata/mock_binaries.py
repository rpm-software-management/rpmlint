import stat

from Testing import get_tested_mock_package

# The ELF payloads below live in test/files/ and are regenerated with
# test/files/build-elf-fixtures.sh.

CryptoPolicyPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib/cyrus-imapd/arbitron': {
            'content-path': 'files/ssl-caller', 'create_dirs': True,
        },
        '/usr/lib64/dovecot/libssl_iostream_openssl.so': {
            'content-path': 'files/ssl-caller.so', 'create_dirs': True,
        },
    },
)

NgircdPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/sbin/ngircd': {
            'content-path': 'files/plain-pie', 'create_dirs': True,
        },
    },
)

LtoTextPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib64/libiberty.a': {
            'content-path': 'files/lto-no-text.a', 'create_dirs': True,
        },
        '/usr/lib64/libdl_p.a': {
            'content-path': 'files/lto-with-text.a', 'create_dirs': True,
        },
    },
)

GhcPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/ghc.a': {
            'content-path': 'files/ghc-no-text.a', 'create_dirs': True,
        },
    },
)

LibtoolWrapperPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/bin/main': {
            'content-path': 'files/nonpie-exec', 'create_dirs': True,
        },
        '/usr/share/main': {
            'content-path': 'files/nonpie-exec', 'create_dirs': True,
        },
        '/etc/main': {
            'content-path': 'files/nonpie-exec', 'create_dirs': True,
        },
        '/bin/libtool-wrapper': {
            'content-path': 'files/libtool-wrapper.sh', 'create_dirs': True,
        },
    },
)

NoarchPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/bin/main': {
            'content-path': 'files/nonpie-exec', 'create_dirs': True,
        },
        '/lib64/foo': {
            'content': 'just some text', 'create_dirs': True,
        },
    },
    header={'ARCH': 'noarch'},
)

LibnoexecPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/lib64/libfoo.so': {
            'content-path': 'files/exec-shlib.so',
            'metadata': {'mode': stat.S_IFREG | 0o755},
            'create_dirs': True,
        },
    },
)

GlibcPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/lib64/libpthread.so': {
            'content-path': 'files/nonexec-shlib.so', 'create_dirs': True,
        },
    },
)

BccLuaPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/bin/bcc-lua': {
            'content-path': 'files/nonpie-exec', 'create_dirs': True,
        },
    },
)

OnlyNonBinaryInUsrLibPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib64/file1': {
            'content': 'just some text', 'create_dirs': True,
        },
        '/usr/lib64/file2': {
            'content': 'just some text', 'create_dirs': True,
        },
        '/usr/lib64/file3': {
            'content': 'just some text', 'create_dirs': True,
        },
    },
)

OnlyNonBinaryInUsrLibExceptionPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib64/file1': {
            'content': 'just some text', 'create_dirs': True,
        },
        '/usr/lib64/file2': {
            'content': 'just some text', 'create_dirs': True,
        },
        '/usr/lib64/python/file3': {
            'content': 'just some text', 'create_dirs': True,
        },
    },
)

NoBinaryPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/etc/file1': {
            'content': 'just some text', 'create_dirs': True,
        },
        '/usr/share/file2': {
            'content': 'just some text', 'create_dirs': True,
        },
    },
)

InvalidLaFilePackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib64/static.la': {
            'content': "libdir='/home/user/sth'\n", 'create_dirs': True,
        },
    },
)

BinaryInEtcPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/etc/hello': {
            'content-path': 'files/plain-pie', 'create_dirs': True,
        },
    },
)

NonPositionIndependentExecPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/bin/hello': {
            'content-path': 'files/nonpie-stripped', 'create_dirs': True,
        },
    },
)

LibtestPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib64/hello.so': {
            'content-path': 'files/no-soname.so', 'create_dirs': True,
        },
        '/usr/bin/hello_exec': {
            'content-path': 'files/plain-pie', 'create_dirs': True,
        },
        '/usr/lib64/libhello.a': {
            'content-path': 'files/patchable.a', 'create_dirs': True,
        },
    },
)

Libtest1Package = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib64/libtest.so.1.5.0': {
            'content-path': 'files/invalid-soname.so', 'create_dirs': True,
        },
    },
)

Libtest2Package = get_tested_mock_package(
    lazyload=True,
    name='libtest2',
    files={
        '/usr/lib64/libtest.so.1.5.0': {
            'content-path': 'files/policy-soname.so', 'create_dirs': True,
        },
    },
)

Libtest3Package = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/share/wrongfile': {
            'content': 'just some text', 'create_dirs': True,
        },
        '/usr/lib64/libtest.so.3.5.0': {
            'content-path': 'files/ldconfig-soname.so', 'create_dirs': True,
        },
        '/usr/lib64/libtest.so.3': {
            'linkto': '../share/wrongfile', 'create_dirs': True,
        },
    },
)

Libtest4Package = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib64/libtest.so.4.5.0': {
            'content-path': 'files/ldconfig-ok.so', 'create_dirs': True,
        },
        '/usr/lib64/libtest.so.4': {
            'linkto': 'libtest.so.4.5.0', 'create_dirs': True,
        },
    },
)

MultipleErrorsPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/bin/hello': {
            'content-path': 'files/multi-error', 'create_dirs': True,
        },
    },
)
