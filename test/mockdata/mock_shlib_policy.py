from Testing import get_tested_mock_package


Libtest1Package = get_tested_mock_package(
    lazyload=True,
    name='libtest1',
    files={
        '/usr/lib64/libtest.so.1.5.0': {
            # SONAME: libtest.so.1x
            'content-path': 'files/shlib_policy/libtest.so.1.5.0',
        }
    },
    header={
        'requires': [
            '/sbin/ldconfig',
            'libc.so.6()(64bit)',
            'libc.so.6(GLIBC_2.2.5)(64bit)',
        ]
    }
)


LibslpMissingSuffixPackage = get_tested_mock_package(
    lazyload=True,
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
            # Excessive dependency
            'libsparta.so.2',
        ]
    }
)


Libslp1234Package = get_tested_mock_package(
    lazyload=True,
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
            # Fixed shlib dependency
            'libsparta.so.2 = 1.23',
        ]
    }
)
