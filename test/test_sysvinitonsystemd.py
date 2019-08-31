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
    assert 'E: deprecated-init-script /etc/init.d/weekly.script' in out
    assert 'E: deprecated-boot-script /etc/init.d/boot.script' in out
