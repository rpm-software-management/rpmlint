import pytest
from rpmlint.checks.ExecDocCheck import ExecDocCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def execdoccheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = ExecDocCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/mydoc'])
def test_bashisms(tmpdir, package, execdoccheck):
    output, test = execdoccheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: executable-docs /usr/share/doc/packages/mydoc/doc.html' in out
    assert 'E: executable-docs /usr/share/doc/packages/mydoc/README' in out
    assert 'W: package-with-huge-docs: 100%' in out
