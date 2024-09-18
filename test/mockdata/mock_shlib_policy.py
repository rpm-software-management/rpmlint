from Testing import get_tested_mock_package

SHLIBPOLICY = get_tested_mock_package(
    name='libtest1',
    files={
        '/usr/lib64/libtest.so.1.5.0': {'content-path': 'files/shlib_policy/libtest.so.1.5.0'}
    },
    header={
        'requires': [
            '/sbin/ldconfig',
            'libc.so.6()(64bit)',
            'libc.so.6(GLIBC_2.2.5)(64bit)',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ]
    }
)

SHLIBPOLICY2 = get_tested_mock_package(
    name='libslp-missing-suffix',
    files={
        '/usr/lib64/hello': {'is_dir': True},
        '/usr/lib64/hello/libhello2.so': {'content-path': 'files/shlib_policy/libhello2.so'},
        '/usr/lib64/libhello.so': {'content-path': 'files/shlib_policy/libhello.so'},
        '/usr/lib64/libhello2.so': {'content-path': 'files/shlib_policy/libhello2.so'}
    },
    header={
        'requires': [
            'libc.so.6()(64bit)',
            'libc.so.6(GLIBC_2.2.5)(64bit)',
            'libsparta.so.2',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1'
        ]
    }
)

SHLIBPOLICY3 = get_tested_mock_package(
    name='libslp1234',
    files={
        '/usr/lib64/hello': {'is_dir': True},
        '/usr/lib64/hello/libhello2.so': {'content-path': 'files/shlib_policy/libhello2.so'},
        '/usr/lib64/libhello.so': {'content-path': 'files/shlib_policy/libhello.so'},
        '/usr/lib64/libhello2.so': {'content-path': 'files/shlib_policy/libhello2.so'}
    },
    header={
        'requires': [
            'libc.so.6()(64bit)',
            'libc.so.6(GLIBC_2.2.5)(64bit)',
            'libsparta.so.2 = 1.23',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1'
        ]
    }
)
