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


@pytest.mark.parametrize('package', ['binary/doc-file-dependency'])
def test_doc_file_dep(tmpdir, package, doccheck):
    output, test = doccheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: doc-file-dependency' in out
    assert 'W: install-file-in-docs' not in out


@pytest.mark.parametrize('package', ['binary/install-file-in-docs'])
def test_install_file_in_docs(tmpdir, package, doccheck):
    output, test = doccheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: install-file-in-docs' in out
    assert 'E: executable-docs' not in out
    assert 'W: package-with-huge-docs: 100%' not in out
    assert 'W: doc-file-dependency' not in out
