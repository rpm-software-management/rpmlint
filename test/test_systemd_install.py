import pytest
from rpmlint.checks.SystemdInstallCheck import SystemdInstallCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package, IS_FEDORA_RELEASE


@pytest.fixture(scope='function', autouse=True)
def systemdinstallcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SystemdInstallCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/dnf-automatic'])
@pytest.mark.skipif(IS_FEDORA_RELEASE, reason='Fedora does not define %{_unitdir} rpm macro')
def test_bashisms(tmp_path, package, systemdinstallcheck):
    output, test = systemdinstallcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)

    for scriptlet_type in ['add_pre', 'add_post', 'del_preun', 'del_postun']:
        message = f'systemd-service-without-service_{scriptlet_type} dnf-automatic-download.service'
        assert message in out


@pytest.mark.parametrize('package', ['binary/sarg', 'binary/nvme-cli'])
@pytest.mark.skipif(IS_FEDORA_RELEASE, reason='Fedora does not define %{_unitdir} rpm macro')
def test_systemd_service_preun(tmp_path, package, systemdinstallcheck):
    output, test = systemdinstallcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)

    for scriptlet_type in ['add_pre', 'add_post', 'del_preun', 'del_postun']:
        message = f'systemd-service-without-service_{scriptlet_type}'
        assert message not in out
