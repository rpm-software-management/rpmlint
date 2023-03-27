import pytest
from rpmlint.checks.LibraryDependencyCheck import LibraryDependencyCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def libdependencycheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = LibraryDependencyCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/shlib2-devel'])
def test_shlib2_devel(tmp_path, package, libdependencycheck):
    output, test = libdependencycheck
    test.check(get_tested_package(package, tmp_path))
    test.after_checks()
    out = output.print_results(output.results)
    assert 'E: no-library-dependency-for /usr/lib/libfoo.so.1' in out
