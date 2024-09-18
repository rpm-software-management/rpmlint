from Testing import get_tested_mock_package

DBUSPOLICY = get_tested_mock_package(
files={
'/etc/dbus-1/system.d/noxml.conf': {
'content': '',
},
'/etc/dbus-1/system.d/org.freedesktop.NetworkManager.conf': {
'content': """
<busconfig>
<policy user="root">
<allow send_interface="org.freedesktop.NetworkManager.PPP"/>
<allow receive_sender="foo"/>
</policy>
<policy>
<deny send_interface="org.freedesktop.NetworkManager.Settings" send_member="ReloadConnections"/>
</policy>
</busconfig>
""",
},
'/etc/dbus-1/system.d/org.freedesktop.NetworkManager2.conf': {
'content': """
<busconfig>
<policy user="root">
<!-- No allow policies -->
</policy>
</busconfig>
""",
}})
