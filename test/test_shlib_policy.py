import stat
import pytest
from rpmlint.checks.SharedLibraryPolicyCheck import SharedLibraryPolicyCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def slpcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SharedLibraryPolicyCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [get_tested_mock_package(
    name='libtest1',
    files={
        '/usr/lib64/libtest.so.1.5.0': {'content-path': 'files/libtest.so.1.5.0'}
    },
    header={
        'requires': [
            '/sbin/ldconfig',
            'libc.so.6()(64bit)',
            'libc.so.6(GLIBC_2.2.5)(64bit)',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        ],
    }
)])
def test_shlib_policy_wrong_name(package, slpcheck):
    output, test = slpcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: shlib-unversioned-lib libtest.so.1x' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    name='libslp-missing-suffix',
    files={
        '/usr/lib64/hello': {'is_dir': True},
        '/usr/lib64/hello/libhello2.so': {},
        '/usr/lib64/libhello.so': {'content-path': 'files/libhello.so'},
        '/usr/lib64/libhello2.so': {'content-path': 'files/libhello2.so'}
    },
    header={
        'requires': [
            'libc.so.6()(64bit)',
            'libc.so.6(GLIBC_2.2.5)(64bit)',
            'libsparta.so.2',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1',
        ]
    }
)])
def test_shlib_policy_missing_suffix(package, slpcheck):
    output, test = slpcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: shlib-policy-excessive-dependency libsparta.so.2' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    name='libslp1234',
    files={
        '/usr/lib64/hello': {'is_dir': True},
        '/usr/lib64/hello/libhello2.so': {'content-path': 'files/libhello2.so'},
        '/usr/lib64/libhello.so': {'content-path': 'files/libhello2.so'},
        '/usr/lib64/libhello2.so': {'content-path': 'files/libhello2.so'}
    },
    header={
        'requires': [
            'libc.so.6()(64bit)',
            'libc.so.6(GLIBC_2.2.5)(64bit)',
            'libsparta.so.2 = 1.23',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1',
        ]
    }
)])
def test_shlib_policy_errors(package, slpcheck):
    output, test = slpcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: shlib-fixed-dependency libsparta.so.2 = 1.23' in out
