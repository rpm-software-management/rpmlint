import pytest
from rpmlint.checks.SystemdInstallCheck import SystemdInstallCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def systemdinstallcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SystemdInstallCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/dnf-automatic'])
def test_bashisms(tmpdir, package, systemdinstallcheck):
    output, test = systemdinstallcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)

    for scriptlet_type in ['add_pre', 'add_post', 'del_preun', 'del_postun']:
        message = f'W: systemd-service-without-service_{scriptlet_type} dnf-automatic-download.service'
        assert message in out
