import pytest
from rpmlint.checks.PkgConfigCheck import PkgConfigCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def pkgconfigcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = PkgConfigCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/pc'])
def test_pkg_config(tmpdir, package, pkgconfigcheck):
    output, test = pkgconfigcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: invalid-pkgconfig-file /tmp/pkgconfig/xcb.pc' in out
    assert 'E: pkgconfig-invalid-libs-dir /tmp/pkgconfig/xcb.pc Libs: -L/usr/lib' in out
