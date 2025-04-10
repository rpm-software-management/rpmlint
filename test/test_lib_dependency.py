from mockdata.mock_lib_dependency import LIBDEPENDENCY, LIBDEPENDENCY2
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


@pytest.mark.parametrize('package', [LIBDEPENDENCY])
def test_shlib2_devel(package, libdependencycheck):
    output, test = libdependencycheck
    test.check(package)
    test.after_checks()
    out = output.print_results(output.results)
    print(out)
    assert 'E: no-library-dependency-for /usr/lib/libfoo.so.1' in out


# TODO: Check out this test. It seems to do nothing
@pytest.mark.parametrize('package', [LIBDEPENDENCY2])
def test_missing_depency_on(package, libdependencycheck):
    output, test = libdependencycheck
    test.check(package)
    test.after_checks()
    out = output.print_results(output.results)
    assert 'W: missing-dependency-on' not in out
