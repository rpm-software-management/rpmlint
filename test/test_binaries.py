from mockdata.mock_binaries import (
    BccLuaPackage,
    BinaryInEtcPackage,
    CryptoPolicyPackage,
    GhcPackage,
    GlibcPackage,
    InvalidLaFilePackage,
    LibnoexecPackage,
    Libtest1Package,
    Libtest2Package,
    Libtest3Package,
    Libtest4Package,
    LibtestPackage,
    LibtoolWrapperPackage,
    LtoTextPackage,
    MultipleErrorsPackage,
    NgircdPackage,
    NoarchPackage,
    NoBinaryPackage,
    NonPositionIndependentExecPackage,
    OnlyNonBinaryInUsrLibExceptionPackage,
    OnlyNonBinaryInUsrLibPackage,
)
from mockdata.mock_pkgconfig import LibReiserFSCoreDevelPackage
import pytest
from rpmlint.checks.BinariesCheck import BinariesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, Config, get_tested_mock_package, IS_X86_64, TEST_CONFIG


@pytest.fixture(scope='function', autouse=True)
def binariescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [CryptoPolicyPackage])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_forbidden_c_calls(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'crypto-policy-non-compliance-openssl /usr/lib/cyrus-imapd/arbitron SSL_CTX_set_cipher_list' in out
    assert 'crypto-policy-non-compliance-openssl /usr/lib64/dovecot/libssl_iostream_openssl.so SSL_CTX_set_cipher_list' in out


@pytest.mark.parametrize('package', [NgircdPackage])
def test_waived_forbidden_c_calls(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'crypto-policy-non-compliance' not in out


@pytest.mark.parametrize('package', [LibReiserFSCoreDevelPackage])
def test_lto_bytecode(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'lto-bytecode' in out


@pytest.mark.parametrize('package', [LtoTextPackage])
def test_lto_archive_text(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'lto-no-text-in-archive /usr/lib64/libiberty.a' in out
    assert 'lto-no-text-in-archive /usr/lib64/libdl_p.a' not in out


@pytest.mark.parametrize('package', [GhcPackage])
def test_lto_ghc_archive(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'lto-no-text-in-archive' not in out


@pytest.mark.parametrize('package', [LibtoolWrapperPackage])
def test_libtool_wrapper(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: libtool-wrapper-in-package' in out
    assert 'W: unstripped-binary-or-object' in out
    assert 'E: arch-dependent-file-in-usr-share' in out
    assert 'W: unstripped-binary-or-object /bin/main' in out
    assert 'W: position-independent-executable-suggested /usr/share/main' in out


@pytest.mark.parametrize('package', [NoarchPackage])
def test_no_arch_issues(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: arch-independent-package-contains-binary-or-object /bin/main' in out
    assert 'E: noarch-with-lib64' in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        lazyload=True,
        files={'/opt/ebpf.o': {'content-path': 'files/ebpf.o', 'create_dirs': True}},
        header={'ARCH': 'noarch'},
    ),
    get_tested_mock_package(
        lazyload=True,
        files={'/opt/python-flit-metadata.txt': {'content-path': 'files/python-flit-metadata.txt', 'create_dirs': True}},
        header={'ARCH': 'noarch'},
    ),
    get_tested_mock_package(
        lazyload=True,
        files={'/opt/x86_64.o': {'content-path': 'files/x86_64.o', 'create_dirs': True}},
        header={'ARCH': 'x86-64'},
    ),
    get_tested_mock_package(
        lazyload=True,
        files={'/opt/aarch64.o': {'content-path': 'files/aarch64.o', 'create_dirs': True}},
        header={'ARCH': 'aarch64'},
    ),
])
def test_no_arch_eBPF(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: arch-independent-package-contains-binary-or-object' not in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        lazyload=True,
        files={'/opt/x86_64.o': {'content-path': 'files/x86_64.o', 'create_dirs': True}},
        header={'ARCH': 'noarch'},
    ),
    get_tested_mock_package(
        lazyload=True,
        files={'/opt/aarch64.o': {'content-path': 'files/aarch64.o', 'create_dirs': True}},
        header={'ARCH': 'noarch'},
    ),
])
def test_no_arch_error(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: arch-independent-package-contains-binary-or-object' in out


@pytest.mark.parametrize('package', [LibnoexecPackage])
def test_shlib_with_no_exec(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: shared-library-not-executable /lib64/libfoo.so' not in out


@pytest.mark.parametrize('package', [GlibcPackage])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_shlib_with_no_exec_glibc(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: shared-library-not-executable /lib64/libpthread.so' in out
    assert 'missing-hash-section' not in out
    assert 'missing-gnu-hash-section' not in out


@pytest.mark.parametrize('package', [BccLuaPackage])
def test_position_independent_executable(package, binariescheck):
    CONFIG.configuration['PieExecutables'] = ['.*']
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: non-position-independent-executable /usr/bin/bcc-lua' in out


@pytest.mark.parametrize('package', [OnlyNonBinaryInUsrLibPackage])
def test_only_non_binary_in_usr_lib(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: only-non-binary-in-usr-lib' in out
    # there is a file in /usr/lib64, so no error
    assert 'E: no-binary' not in out
    # we have no 'noarch' or wrapper here
    assert 'E: noarch-with-lib64' not in out
    assert 'E: arch-independent-package-contains-binary-or-object' not in out
    assert 'E: libtool-wrapper-in-package' not in out


# In general we want to throw a warning if we have only non-binary files in
# the /usr/lib. But we can allow non-binaries via UsrLibBinaryException config
# option. These files will be considered binaries and no warning should be
# thrown.
@pytest.mark.parametrize('package', [OnlyNonBinaryInUsrLibExceptionPackage])
def test_only_non_binary_in_usr_lib_exception(package, binariescheck):
    config = Config(TEST_CONFIG)
    config.configuration['UsrLibBinaryException'] = '^/usr/lib(64)?/python'
    output = Filter(config)
    test = BinariesCheck(config, output)
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: only-non-binary-in-usr-lib' not in out


@pytest.mark.parametrize('package', [NoBinaryPackage])
def test_no_binary(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: no-binary' in out
    # no .la file or binary there
    assert 'E: invalid-la-file' not in out
    assert 'E: binary-in-etc' not in out


@pytest.mark.parametrize('package', [InvalidLaFilePackage])
def test_invalid_la_file(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: invalid-la-file' in out
    # no /usr/share dir there
    assert 'E: arch-dependent-file-in-usr-share' not in out


@pytest.mark.parametrize('package', [BinaryInEtcPackage])
def test_binary_in_etc(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: binary-in-etc' in out
    # it's not a library package
    assert 'E: executable-in-library-package' not in out


@pytest.mark.parametrize('package', [NonPositionIndependentExecPackage])
def test_non_position_independent_sugg(package, binariescheck):
    # reset PieExecutable option
    CONFIG.configuration['PieExecutables'] = []
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: position-independent-executable-suggested' in out
    # it should throw just a warning as it's not forced by PieExecutables opt
    assert 'E: non-position-independent-executable' not in out


# Force an error by setting PieExecutables option to the no-pie binary
@pytest.mark.parametrize('package', [NonPositionIndependentExecPackage])
def test_non_position_independent(package, binariescheck):
    CONFIG.configuration['PieExecutables'] = ['sparta', '.*hello']
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: non-position-independent-executable' in out
    # It should throw just the error, not warning
    assert 'W: position-independent-executable-suggested' not in out


# libtest package
@pytest.mark.parametrize('package', [LibtestPackage])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_library(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: executable-in-library-package' in out
    assert 'W: no-soname' in out
    # there is no soname here so it can't be invalid
    assert 'E: invalid-soname' not in out


# invalid-soname test package
@pytest.mark.parametrize('package', [Libtest1Package])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_shared_library1(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: invalid-soname' in out
    # there is an invalid soname here, so no "no-soname" error
    assert 'W: no-soname' not in out


# shlib-policy-name-error test package
@pytest.mark.parametrize('package', [Libtest2Package])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_shared_library2(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: shlib-policy-name-error' in out
    # it doesn't call /sbin/ldconfig
    assert 'E: no-ldconfig-symlink' in out
    # no ldconfig is not invalid
    assert 'E: invalid-ldconfig-symlink' not in out
    # the soname is set
    assert 'W: no-soname' not in out


# invalid-ldconfig-symlink test package
@pytest.mark.parametrize('package', [Libtest3Package])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_invalid_ldconfig_symlink(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: invalid-ldconfig-symlink' in out
    # executable doesn't call mktemp, setuid or gethostbyname
    assert 'E: call-to-mktemp' not in out
    assert 'E: missing-call-to-setgroups-before-setuid' not in out
    assert 'W: binary-or-shlib-calls-gethostbyname' not in out
    # it's not statically linked either
    assert 'E: statically-linked-binary' not in out


# valid symlink should not report invalid-ldconfig-symlink
@pytest.mark.parametrize('package', [Libtest4Package])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_not_valid_ldconfig_symlink(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: invalid-ldconfig-symlink' not in out


@pytest.mark.parametrize('package', [MultipleErrorsPackage])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_multiple_errors(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: call-to-mktemp' in out
    assert 'E: missing-call-to-setgroups-before-setuid' in out
    assert 'W: binary-or-shlib-calls-gethostbyname' in out


@pytest.mark.parametrize('package', [LibtestPackage])
def test_patchable_function_entry_archive(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: patchable-function-entry-in-archive /usr/lib64/libhello.a' in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(files=['/usr/lib/systemd/system/yast-timesync.service']),
])
def test_systemd_unit_file(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'only-non-binary-in-usr-lib' not in out
