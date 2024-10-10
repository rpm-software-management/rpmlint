from mockdata.mock_files import Shlib2DevelPackage
import pytest
from rpmlint.checks.LibraryDependencyCheck import LibraryDependencyCheck
from rpmlint.filter import Filter

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def libdependencycheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = LibraryDependencyCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [Shlib2DevelPackage])
def test_shlib2_devel(package, libdependencycheck):
    output, test = libdependencycheck
    test.check(package)
    test.after_checks()
    out = output.print_results(output.results)
    print(out)
    assert 'E: no-library-dependency-for /usr/lib/libfoo.so.1' in out
