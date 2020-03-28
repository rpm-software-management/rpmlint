import pytest
from rpmlint.checks.ZyppSyntaxCheck import ZyppSyntaxCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def zyppsyntaxcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ZyppSyntaxCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/packageand'])
def test_packageand(tmpdir, package, zyppsyntaxcheck):
    output, test = zyppsyntaxcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'suse-zypp-packageand packageand(c:d)' in out
    assert 'suse-zypp-packageand packageand(a:b)' in out
    assert '(a and b)' not in out
    assert 'bee' not in out
    assert 'suse-zypp-otherproviders otherproviders(yast2_theme)' in out
