from rpmlint.checks.AbstractCheck import AbstractCheck


class DBusServicesCheck(AbstractCheck):
    _dbus_system_paths = [
        '/usr/share/dbus-1/system-services/',
        '/usr/share/dbus-1/system.d/',
        '/etc/dbus-1/system.d/'
    ]

    def __init__(self, config, output):
        super().__init__(config, output)
        self.services_whitelist = config.configuration['DBUSServices']['WhiteList']

    def check(self, pkg):
        if pkg.is_source:
            return

        for f in pkg.files:
            for p in self._dbus_system_paths:
                if f.startswith(p):

                    if f in pkg.ghost_files:
                        self.output.add_info('E', pkg, 'suse-dbus-ghost-service', f)
                        continue

                    bn = f[len(p):]
                    if bn not in self.services_whitelist:
                        self.output.add_info('E', pkg, 'suse-dbus-unauthorized-service', f)
