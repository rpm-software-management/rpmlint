import pytest
from rpmlint.checks.SysVInitOnSystemdCheck import SysVInitOnSystemdCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def sysvcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SysVInitOnSystemdCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/init'])
def test_sysv_init_on_systemd_check(tmpdir, package, sysvcheck):
    output, test = sysvcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: obsolete-insserv-requirement' in out
    assert 'E: deprecated-init-script weekly.script' in out
    assert 'E: deprecated-boot-script boot.script' in out


@pytest.mark.parametrize('package', ['binary/rc-links'])
def test_overshadowing_of_initscript(tmpdir, package, sysvcheck):
    output, test = sysvcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: systemd-shadowed-initscript bar' in out
