from Testing import get_tested_mock_package


DbusRulePackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/etc/dbus-1/system.d/noxml.conf': {},
        '/etc/dbus-1/system.d/org.freedesktop.NetworkManager.conf': {
            'content-path': 'files/systemd/org.freedesktop.NetworkManager.conf',
        },
        '/etc/dbus-1/system.d/org.freedesktop.NetworkManager2.conf': {
            'content-path': 'files/systemd/org.freedesktop.NetworkManager2.conf',
        },
    },
)
