import pytest
from rpmlint.checks.SystemdInstallCheck import SystemdInstallCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def systemdinstallcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SystemdInstallCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/dnf-automatic'])
def test_systemd_service_without_service_macro(tmp_path, package, systemdinstallcheck):
    output, test = systemdinstallcheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)

    for scriptlet_type in ['add_pre', 'add_post', 'del_preun', 'del_postun']:
        message = f'systemd-service-without-service_{scriptlet_type} dnf-automatic-download.service'
        assert message in out


@pytest.mark.parametrize('package,error', [
    (get_tested_mock_package(
        name='greetd',
        files=['/usr/lib/systemd/system/greetd.service'],
        header={
            'PREIN': 'systemd-update-helper mark-install-system-units greetd.service',
            'POSTIN': 'systemd-update-helper install-system-units greetd.service',
            'PREUN': 'systemd-update-helper remove-system-units greetd.service',
            'POSTUN': 'systemd-update-helper mark-restart-system-units greetd.service',
        },
    ), False),
    (get_tested_mock_package(
        name='greetd',
        files=['/usr/lib/systemd/system/greetd.service'],
        header={
            'PREIN': 'systemd-update-helper mark-install-system-units greetd.service',
            'POSTIN': 'systemd-update-helper install-system-units greetd.service',
            'PREUN': 'systemd-update-helper remove-system-units greetd.service',
            'POSTUN': '\n \n:',
        },
    ), False),
    (get_tested_mock_package(
        name='greetd',
        files=['/usr/lib/systemd/system/greetd.service'],
        header={},
    ), True),
    (get_tested_mock_package(
        name='MirrorCache',
        files=[
            '/usr/lib/systemd/system/mirrorcache-backstage-hashes.service',
            '/usr/lib/systemd/system/mirrorcache-backstage.service',
            '/usr/lib/systemd/system/mirrorcache-hypnotoad.service',
            '/usr/lib/systemd/system/mirrorcache-subtree.service',
            '/usr/lib/systemd/system/mirrorcache.service',
        ],
        header={
            'PREUN': '/usr/lib/systemd/systemd-update-helper remove-system-units mirrorcache.service mirrorcache-backstage.service mirrorcache-backstage-hashes.service mirrorcache-subtree.service mirrorcache-hypnotoad.service',
            'PREIN': '/usr/lib/systemd/systemd-update-helper mark-install-system-units mirrorcache.service mirrorcache-backstage.service mirrorcache-backstage-hashes.service mirrorcache-subtree.service mirrorcache-hypnotoad.service',
            'POSTIN': '/usr/lib/systemd/systemd-update-helper install-system-units mirrorcache.service mirrorcache-backstage.service mirrorcache-backstage-hashes.service mirrorcache-subtree.service mirrorcache-hypnotoad.service',
            'POSTUN': """
if [ $1 -ge 1 ] && [ -x /usr/lib/systemd/systemd-update-helper ]; then
    # Package upgrade, not uninstall
    DISABLE_RESTART_ON_UPDATE=no
    [ -e /etc/sysconfig/services ] && . /etc/sysconfig/services || :
    case "$DISABLE_RESTART_ON_UPDATE" in
        yes|1)  ;;
        *)    /usr/lib/systemd/systemd-update-helper mark-restart-system-units mirrorcache.service mirrorcache-backstage.service mirrorcache-backstage-hashes.service mirrorcache-subtree.service || :
    esac
fi

:

""",
        },
    ), False),
])
def test_systemd_service_without_service_macro2(package, error, systemdinstallcheck):
    output, test = systemdinstallcheck
    test.check(package)
    out = output.print_results(output.results)

    for scriptlet_type in ['add_pre', 'add_post', 'del_preun', 'del_postun']:
        message = f'systemd-service-without-service_{scriptlet_type}'
        assert (message in out) == error
