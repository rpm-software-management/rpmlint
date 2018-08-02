import pytest
from rpmlint.Filter import Filter
from rpmlint.MenuXDGCheck import MenuXDGCheck

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def menuxdgcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = MenuXDGCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/menuxdg1'])
def test_raises_parse_error(tmpdir, package):
    output, test = menuxdgcheck()
    test.check(get_tested_package(package, tmpdir))
    assert len(output.results) == 4
    out = output.print_results(output.results)
    assert 'contains parsing error' in out
    assert ' invalid-desktopfile ' in out
    assert 'check with desktop-file-validate' in out
