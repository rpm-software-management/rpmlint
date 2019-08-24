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
