import pytest
from rpmlint.checks.SourceCheck import SourceCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def sourcescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SourceCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['source/wrongsrc'])
def test_extension_and_permissions(tmpdir, package, sourcescheck):
    output, test = sourcescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    assert len(output.results) == 1

    assert 'inconsistent-file-extension' in out
    assert 'name extension indicates a different compression format' in out

    assert 'strange-permission' not in out
    assert 'a file should have' not in out


@pytest.mark.parametrize('package', ['source/not-compressed-multi-spec'])
def test_compression_and_multispec(tmpdir, package, sourcescheck):
    output, test = sourcescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    assert 'source-not-compressed' in out
    assert 'source archive or file in your package is not compressed' in out

    assert 'multiple-specfiles' in out
    assert 'package contains multiple spec files' in out
