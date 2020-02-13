from pathlib import Path

from rpmlint.checks.AbstractCheck import AbstractCheck


class SysVInitOnSystemdCheck(AbstractCheck):
    def __init__(self, config, output):
        super().__init__(config, output)
        self.initscripts = set()
        self.bootscripts = set()
        self.systemdscripts = set()

    def check(self, pkg):
        if pkg.is_source:
            return

        self._find_services_and_scripts(pkg)

        for req in pkg.requires + pkg.prereq:
            if req[0] == 'insserv':
                self.output.add_info('E', pkg, 'obsolete-insserv-requirement')

        for filename in self.bootscripts:
            self.output.add_info('E', pkg, 'deprecated-boot-script', filename)
        for filename in self.initscripts:
            self.output.add_info('E', pkg, 'deprecated-init-script', filename)
        for filename in self.initscripts:
            if filename in self.systemdscripts:
                self.output.add_info('E', pkg, 'systemd-shadowed-initscript', filename)

    def _find_services_and_scripts(self, pkg):
        # Find all regular systemd services and initscripts
        for filename, _pkgfile in pkg.files.items():
            if filename in pkg.ghost_files:
                continue

            if filename.startswith('/usr/lib/systemd/system/'):
                basename = Path(filename).name
                # @ means it is socket service which is not what we look for
                if '@' in filename:
                    continue
                if filename.endswith('.service') or filename.endswith('.target'):
                    self.systemdscripts.add(basename.rpartition('.')[0])

            if filename.startswith('/etc/init.d/') or filename.startswith('/etc/rc.d/init.d'):
                basename = Path(filename).name
                if basename.startswith('boot.'):
                    self.bootscripts.add(basename)
                elif not basename.startswith('rc'):
                    self.initscripts.add(basename)
