from mockdata.mock_i18n import InvalidI18NPackage, I18NPackage
import pytest
from rpmlint.checks.I18NCheck import I18NCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def i18ncheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = I18NCheck(CONFIG, output)
    yield output, test


@pytest.fixture
def output(i18ncheck):
    output, _test = i18ncheck
    yield output


@pytest.fixture
def test(i18ncheck):
    _output, test = i18ncheck
    yield test


@pytest.mark.parametrize('package', [InvalidI18NPackage])
def test_i18n_invalid_lang(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: invalid-lc-messages-dir /usr/share/locale/xx_ES/LC_MESSAGES/goodvibes.mo' in out
    assert 'E: invalid-lc-messages-dir /usr/share/locale/es_XX/LC_MESSAGES/goodvibes.mo' in out
    assert 'E: invalid-lc-messages-dir /usr/share/locale/xx/LC_MESSAGES/goodvibes.mo' in out


@pytest.mark.parametrize('package', [I18NPackage])
def test_i18n_valid_lang(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: invalid-lc-messages-dir' not in out
