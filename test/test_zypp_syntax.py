from mockdata.mock_zypp_syntax import (
    SyntaxAndPackage,
    SyntaxPackageandPackage,
)
import pytest
from rpmlint.checks.ZyppSyntaxCheck import ZyppSyntaxCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def zyppsyntaxcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ZyppSyntaxCheck(CONFIG, output)
    return output, test


@pytest.fixture
def output(zyppsyntaxcheck):
    output, _test = zyppsyntaxcheck
    yield output


@pytest.fixture
def test(zyppsyntaxcheck):
    _output, test = zyppsyntaxcheck
    yield test


@pytest.mark.parametrize('package', [SyntaxPackageandPackage])
def test_packageand(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'suse-zypp-packageand packageand(c:d)' in out
    assert 'suse-zypp-packageand packageand(a:b)' in out
    assert '(a and b)' not in out
    assert 'bee' not in out
    assert 'suse-zypp-otherproviders otherproviders(yast2_theme)' in out


@pytest.mark.parametrize('package', [SyntaxAndPackage])
def test_packageand_ok(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'suse-zypp-packageand' not in out
    assert 'suse-zypp-otherproviders' not in out
