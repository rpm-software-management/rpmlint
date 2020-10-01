import pytest
from rpmlint.checks.CheckDBUSServices import DBUSServiceCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def dbusservicescheck(tmpdir):
    CONFIG.info = True
    CONFIG.configuration['DBUSServices.WhiteList'] = ('1', '2', '3')

    output = Filter(CONFIG)
    test = DBUSServiceCheck(CONFIG, output)

    return output, test


@pytest.mark.parametrize('package', ['binary/dbus_svc'])
def test_dbus_services(tmpdir, package, dbusservicescheck):
    output, test = dbusservicescheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    # these are allowed and should NOT produce errors
    assert 'dbus-unauthorized-service /usr/share/dbus-1/system-services/1' not in out
    assert 'dbus-unauthorized-service /usr/share/dbus-1/system.d/2' not in out
    assert 'dbus-unauthorized-service /etc/dbus-1/system.d/3' not in out
    # these are not allowed and should produce errors
    assert 'dbus-unauthorized-service /usr/share/dbus-1/system-services/a' in out
    assert 'dbus-unauthorized-service /usr/share/dbus-1/system.d/b' in out
    assert 'dbus-unauthorized-service /etc/dbus-1/system.d/c' in out
