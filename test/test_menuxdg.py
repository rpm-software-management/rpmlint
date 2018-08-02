import pytest
from rpmlint.Filter import Filter
from rpmlint.MenuXDGCheck import MenuXDGCheck

from Testing import CONFIG, get_tested_package


@pytest.mark.parametrize('package', ['binary/menuxdg1'])
def test_raises_parse_error(package):
    CONFIG.info = True
    output = Filter(CONFIG)
    test = MenuXDGCheck(CONFIG, output)
    test.check(get_tested_package(package))
    assert len(output.results) == 4
    out = output.print_results(output.results)
    assert 'contains parsing error' in out
    assert ' invalid-desktopfile ' in out
    assert 'check with desktop-file-validate' in out
