import pytest
from rpmlint.checks.DocCheck import DocCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def doccheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = DocCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/mydoc'])
def test_doccheck(tmpdir, package, doccheck):
    output, test = doccheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: executable-docs /usr/share/doc/packages/mydoc/doc.html' in out
    assert 'E: executable-docs /usr/share/doc/packages/mydoc/README' in out
    assert 'W: package-with-huge-docs: 100%' in out
