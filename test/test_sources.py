import pytest
from rpmlint.checks.SourceCheck import SourceCheck
from rpmlint.Filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def sourcescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SourceCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['source/wrongsrc'])
def test_inconsistent_file_extension(tmpdir, package):
    output, test = sourcescheck()
    test.check(get_tested_package(package, tmpdir))
    assert len(output.results) == 3
    out = output.print_results(output.results)
    assert 'inconsistent-file-extension' in out
    assert 'a file should have' in out
