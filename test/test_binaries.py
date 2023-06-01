import pytest
from rpmlint.checks.BinariesCheck import BinariesCheck
from rpmlint.filter import Filter
from rpmlint.pkg import FakePkg

from Testing import CONFIG, Config, get_tested_package, get_tested_mock_package, IS_X86_64, TEST_CONFIG


@pytest.fixture(scope='function', autouse=True)
def binariescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/crypto-policy'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_forbidden_c_calls(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'crypto-policy-non-compliance-openssl /usr/lib/cyrus-imapd/arbitron SSL_CTX_set_cipher_list' in out
    assert 'crypto-policy-non-compliance-openssl /usr/lib64/dovecot/libssl_iostream_openssl.so SSL_CTX_set_cipher_list' in out


@pytest.mark.parametrize('package', ['binary/ngircd'])
def test_waived_forbidden_c_calls(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'crypto-policy-non-compliance' not in out


@pytest.mark.parametrize('package', ['binary/libreiserfscore-devel'])
def test_lto_bytecode(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'lto-bytecode' in out


@pytest.mark.parametrize('package', ['binary/lto-text'])
def test_lto_archive_text(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'lto-no-text-in-archive /usr/lib64/libiberty.a' in out
    assert 'lto-no-text-in-archive /usr/lib64/libdl_p.a' not in out


@pytest.mark.parametrize('package', ['binary/ghc'])
def test_lto_ghc_archive(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'lto-no-text-in-archive' not in out


@pytest.mark.parametrize('package', ['binary/libtool-wrapper'])
def test_libtool_wrapper(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: libtool-wrapper-in-package' in out
    assert 'W: unstripped-binary-or-object' in out
    assert 'E: arch-dependent-file-in-usr-share' in out
    assert 'W: unstripped-binary-or-object /bin/main' in out
    assert 'W: position-independent-executable-suggested /usr/share/main' in out


@pytest.mark.parametrize('package', ['binary/noarch'])
def test_no_arch_issues(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: arch-independent-package-contains-binary-or-object /bin/main' in out
    assert 'E: noarch-with-lib64' in out


@pytest.mark.parametrize('package', ['binary/libnoexec'])
def test_shlib_with_no_exec(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: shared-library-not-executable /lib64/libfoo.so' not in out


@pytest.mark.parametrize('package', ['binary/glibc'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_shlib_with_no_exec_glibc(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: shared-library-not-executable /lib64/libpthread.so' in out
    assert 'missing-hash-section' not in out
    assert 'missing-gnu-hash-section' not in out


@pytest.mark.parametrize('package', ['binary/bcc-lua'])
def test_position_independent_executable(tmp_path, package, binariescheck):
    CONFIG.configuration['PieExecutables'] = ['.*']
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: non-position-independent-executable /usr/bin/bcc-lua' in out


@pytest.mark.parametrize('package', ['binary/only-non-binary-in-usr-lib'])
def test_only_non_binary_in_usr_lib(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
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
@pytest.mark.parametrize('package',
                         ['binary/only-non-binary-in-usr-lib_exception'])
def test_only_non_binary_in_usr_lib_exception(tmp_path, package, binariescheck):
    config = Config(TEST_CONFIG)
    config.configuration['UsrLibBinaryException'] = '^/usr/lib(64)?/python'
    output = Filter(config)
    test = BinariesCheck(config, output)
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'W: only-non-binary-in-usr-lib' not in out


@pytest.mark.parametrize('package', ['binary/no-binary'])
def test_no_binary(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: no-binary' in out
    # no .la file or binary there
    assert 'E: invalid-la-file' not in out
    assert 'E: binary-in-etc' not in out


@pytest.mark.parametrize('package', ['binary/invalid-la-file'])
def test_invalid_la_file(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: invalid-la-file' in out
    # no /usr/share dir there
    assert 'E: arch-dependent-file-in-usr-share' not in out


@pytest.mark.parametrize('package', ['binary/binary-in-etc'])
def test_binary_in_etc(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: binary-in-etc' in out
    # it's not a library package
    assert 'E: executable-in-library-package' not in out


@pytest.mark.parametrize('package', ['binary/non-position-independent-exec'])
def test_non_position_independent_sugg(tmp_path, package, binariescheck):
    # reset PieExecutable option
    CONFIG.configuration['PieExecutables'] = []
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'W: position-independent-executable-suggested' in out
    # it should throw just a warning as it's not forced by PieExecutables opt
    assert 'E: non-position-independent-executable' not in out


# Force an error by setting PieExecutables option to the no-pie binary
@pytest.mark.parametrize('package', ['binary/non-position-independent-exec'])
def test_non_position_independent(tmp_path, package, binariescheck):
    CONFIG.configuration['PieExecutables'] = ['sparta', '.*hello']
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: non-position-independent-executable' in out
    # It should throw just the error, not warning
    assert 'W: position-independent-executable-suggested' not in out


# libtest package
@pytest.mark.parametrize('package', ['binary/libtest'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_library(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: executable-in-library-package' in out
    assert 'W: no-soname' in out
    # there is no soname here so it can't be invalid
    assert 'E: invalid-soname' not in out


# invalid-soname test package
@pytest.mark.parametrize('package', ['binary/libtest1'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_shared_library1(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: invalid-soname' in out
    # there is an invalid soname here, so no "no-soname" error
    assert 'W: no-soname' not in out


# shlib-policy-name-error test package
@pytest.mark.parametrize('package', ['binary/libtest2'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_shared_library2(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: shlib-policy-name-error' in out
    # it doesn't call /sbin/ldconfig
    assert 'E: no-ldconfig-symlink' in out
    # no ldconfig is not invalid
    assert 'E: invalid-ldconfig-symlink' not in out
    # the soname is set
    assert 'W: no-soname' not in out


# invalid-ldconfig-symlink test package
@pytest.mark.parametrize('package', ['binary/libtest3'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_invalid_ldconfig_symlink(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: invalid-ldconfig-symlink' in out
    # executable doesn't call mktemp, setuid or gethostbyname
    assert 'E: call-to-mktemp' not in out
    assert 'E: missing-call-to-setgroups-before-setuid' not in out
    assert 'W: binary-or-shlib-calls-gethostbyname' not in out
    # it's not statically linked either
    assert 'E: statically-linked-binary' not in out


# valid symlink should not report invalid-ldconfig-symlink
@pytest.mark.parametrize('package', ['binary/libtest4'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_not_valid_ldconfig_symlink(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: invalid-ldconfig-symlink' not in out


@pytest.mark.parametrize('package', ['binary/multiple_errors'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_multiple_errors(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: call-to-mktemp' in out
    assert 'E: missing-call-to-setgroups-before-setuid' in out
    assert 'W: binary-or-shlib-calls-gethostbyname' in out


@pytest.mark.parametrize('package', ['binary/libtest'])
def test_patchable_function_entry_archive(tmp_path, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: patchable-function-entry-in-archive /usr/lib64/libhello.a' in out

@pytest.mark.parametrize('package', [
    get_tested_mock_package(files={
        '/usr/lib/systemd/system/yast-timesync.service': { 'content': '' }
    })
])
def test_systemd_unit_file(package, binariescheck):
    output, test = binariescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'only-non-binary-in-usr-lib' not in out
