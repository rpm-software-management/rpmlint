import pytest
from rpmlint.checks.DBusPolicyCheck import DBusPolicyCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def dbuspolicycheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = DBusPolicyCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/dbusrule'])
def test_dbus_policy(tmpdir, package, dbuspolicycheck):
    output, test = dbuspolicycheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: dbus-parsing-exception raised an exception: no element found: line 1, column 0 /etc/dbus-1/system.d/noxml.conf' in out
    assert 'E: dbus-policy-allow-without-destination <allow send_interface="org.freedesktop.NetworkManager.PPP"/>' in out
    assert 'W: dbus-policy-allow-receive <allow receive_sender="foo"/>' in out
    assert 'E: dbus-policy-deny-without-destination <deny send_interface="org.freedesktop.NetworkManager.Settings" send_member="ReloadConnections"/>' in out
    assert 'E: communication not allowed /etc/dbus-1/system.d/org.freedesktop.NetworkManager2.conf' in out
