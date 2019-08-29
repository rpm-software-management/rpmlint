import pytest
from rpmlint.checks.IconSizesCheck import IconSizesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def iconsizescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = IconSizesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/tasque'])
def test_icon_sizes(tmpdir, package, iconsizescheck):
    output, test = iconsizescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: wrong-icon-size /usr/share/tasque/icons/hicolor/16x16/status/tasque-note.png expected: 16x16 actual: 22x22' in out
