import pytest
from rpmlint.checks.LSBCheck import LSBCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def lsbcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = LSBCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/fPing'])
def test_LSB_compliance(tmpdir, package, lsbcheck):
    """
    Check that the package name, version and release number are LSB compliant.
    """
    output, test = lsbcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    # Check invalid package name
    assert 'non-lsb-compliant-package-name' in out
    assert 'package name contains an illegal character' in out

    # Check invalid package version
    assert 'non-lsb-compliant-version' in out
    assert 'version number contains an illegal character' in out

    # Check invalid package release
    assert 'non-lsb-compliant-release' in out
    assert 'release number contains an illegal character' in out
