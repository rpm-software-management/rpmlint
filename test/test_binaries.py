import pytest
from rpmlint.checks.BinariesCheck import BinariesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def binariescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BinariesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/cyrus-imapd', 'binary/dovecot'])
def test_forbidden_c_calls(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    assert 'crypto-policy-non-compliance' in output.print_results(output.results)


@pytest.mark.parametrize('package', ['binary/ngircd'])
def test_waived_forbidden_c_calls(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    assert 'crypto-policy-non-compliance' not in output.print_results(output.results)


@pytest.mark.parametrize('package', ['binary/libreiserfscore-devel'])
def test_lto_bytecode(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    assert 'lto-bytecode' in output.print_results(output.results)


@pytest.mark.parametrize('package', ['binary/binutils-devel'])
def test_lto_archive_text(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    assert 'lto-no-text-in-archive' in output.print_results(output.results)


@pytest.mark.parametrize('package', ['binary/libtool-wrapper'])
def test_libtool_wrapper(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: libtool-wrapper-in-package' in out
    assert 'W: unstripped-binary-or-object' in out
    assert 'E: arch-dependent-file-in-usr-share' in out
    assert 'W: unstripped-binary-or-object /bin/main' in out
    assert 'E: binary-in-etc /etc/main' in out


@pytest.mark.parametrize('package', ['binary/noarch'])
def test_no_arch_issues(tmpdir, package, binariescheck):
    output, test = binariescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: arch-independent-package-contains-binary-or-object /bin/main' in out
    assert 'E: noarch-with-lib64' in out
