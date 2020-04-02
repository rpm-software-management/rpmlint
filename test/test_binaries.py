import pytest
from rpmlint.checks.BinariesCheck import BinariesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package, IS_X86_64


@pytest.fixture(scope='function', autouse=True)
def binariescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/crypto-policy'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_forbidden_c_calls(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'crypto-policy-non-compliance-openssl /usr/lib/cyrus-imapd/arbitron SSL_CTX_set_cipher_list' in out
    assert 'crypto-policy-non-compliance-openssl /usr/lib64/dovecot/libssl_iostream_openssl.so SSL_CTX_set_cipher_list' in out


@pytest.mark.parametrize('package', ['binary/ngircd'])
def test_waived_forbidden_c_calls(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'crypto-policy-non-compliance' not in out


@pytest.mark.parametrize('package', ['binary/libreiserfscore-devel'])
def test_lto_bytecode(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'lto-bytecode' in out


@pytest.mark.parametrize('package', ['binary/lto-text'])
def test_lto_archive_text(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'lto-no-text-in-archive' in out


@pytest.mark.parametrize('package', ['binary/ghc'])
def test_lto_ghc_archive(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'lto-no-text-in-archive' not in out


@pytest.mark.parametrize('package', ['binary/libtool-wrapper'])
def test_libtool_wrapper(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: libtool-wrapper-in-package' in out
    assert 'W: unstripped-binary-or-object' in out
    assert 'E: arch-dependent-file-in-usr-share' in out
    assert 'W: unstripped-binary-or-object /bin/main' in out
    assert 'W: position-independent-executable-suggested /usr/share/main' in out


@pytest.mark.parametrize('package', ['binary/noarch'])
def test_no_arch_issues(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: arch-independent-package-contains-binary-or-object /bin/main' in out
    assert 'E: noarch-with-lib64' in out


@pytest.mark.parametrize('package', ['binary/libnoexec'])
def test_shlib_with_no_exec(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: shared-library-not-executable /lib64/libfoo.so' not in out


@pytest.mark.parametrize('package', ['binary/glibc'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_shlib_with_no_exec_glibc(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: shared-library-not-executable /lib64/libpthread.so' in out


@pytest.mark.parametrize('package', ['binary/bcc-lua'])
def test_position_independent_executable(tmpdir, package, binariescheck):
    CONFIG.configuration['PieExecutables'] = ['.*']
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: non-position-independent-executable /usr/bin/bcc-lua' in out


@pytest.mark.parametrize('package', ['binary/only-non-binary-in-usr-lib'])
def test_only_non_binary_in_usr_lib(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
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
def test_only_non_binary_in_usr_lib_exception(tmpdir, package, binariescheck):
    CONFIG.configuration['UsrLibBinaryException'] = '^/usr/lib(64)?/python'
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: only-non-binary-in-usr-lib' not in out


@pytest.mark.parametrize('package', ['binary/no-binary'])
def test_no_binary(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: no-binary' in out
    # no .la file or binary there
    assert 'E: invalid-la-file' not in out
    assert 'E: binary-in-etc' not in out


@pytest.mark.parametrize('package', ['binary/invalid-la-file'])
def test_invalid_la_file(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: invalid-la-file' in out
    # no /usr/share dir there
    assert 'E: arch-dependent-file-in-usr-share' not in out


@pytest.mark.parametrize('package', ['binary/binary-in-etc'])
def test_binary_in_etc(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: binary-in-etc' in out
    # it's not a library package
    assert 'E: executable-in-library-package' not in out


@pytest.mark.parametrize('package', ['binary/non-position-independent-exec'])
def test_non_position_independent_sugg(tmpdir, package, binariescheck):
    # reset PieExecutable option
    CONFIG.configuration['PieExecutables'] = []
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: position-independent-executable-suggested' in out
    # it should throw just a warning as it's not forced by PieExecutables opt
    assert 'E: non-position-independent-executable' not in out


# Force an error by setting PieExecutables option to the no-pie binary
@pytest.mark.parametrize('package', ['binary/non-position-independent-exec'])
def test_non_position_independent(tmpdir, package, binariescheck):
    CONFIG.configuration['PieExecutables'] = ['sparta', 'hello']
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: non-position-independent-executable' in out
    # It should throw just the error, not warning
    assert 'W: position-independent-executable-suggested' not in out


# libtest package
@pytest.mark.parametrize('package', ['binary/libtest'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_library(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: executable-in-library-package' in out
    assert 'W: no-soname' in out
    # there is no soname here so it can't be invalid
    assert 'E: invalid-soname' not in out


# invalid-soname test package
@pytest.mark.parametrize('package', ['binary/libtest1'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_shared_library1(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: invalid-soname' in out
    # there is an invalid soname here, so no "no-soname" error
    assert 'W: no-soname' not in out


# shlib-policy-name-error test package
@pytest.mark.parametrize('package', ['binary/libtest2'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_shared_library2(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
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
def test_invalid_ldconfig_symlink(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: invalid-ldconfig-symlink' in out
    # executable doesn't call mktemp, setuid or gethostbyname
    assert 'E: call-to-mktemp' not in out
    assert 'E: missing-call-to-setgroups-before-setuid' not in out
    assert 'W: binary-or-shlib-calls-gethostbyname' not in out
    # it's not statically linked either
    assert 'E: statically-linked-binary' not in out


@pytest.mark.parametrize('package', ['binary/multiple_errors'])
@pytest.mark.skipif(not IS_X86_64, reason='x86-64 only')
def test_multiple_errors(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: call-to-mktemp' in out
    assert 'E: missing-call-to-setgroups-before-setuid' in out
    assert 'W: binary-or-shlib-calls-gethostbyname' in out


@pytest.mark.parametrize('package', ['binary/dependency-info'])
def test_dependency_information(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: shared-library-without-dependency-information /usr/lib64/ruby/enc/gb2312.so' in out
    assert 'W: library-not-linked-against-libc /usr/lib64/ruby/continuation.so' in out
