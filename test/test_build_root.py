import pytest
from rpmlint.checks.BuildRootCheck import BuildRootCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def buildrootcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = BuildRootCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/buildroot'])
def test_build_root(tmpdir, package, buildrootcheck):
    output, test = buildrootcheck
    test.prepare_regex('/home/marxin/rpmbuild/BUILDROOT/%{NAME}-%{VERSION}-%{RELEASE}.x86_64')
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: file-contains-buildroot /bin/trace' in out
