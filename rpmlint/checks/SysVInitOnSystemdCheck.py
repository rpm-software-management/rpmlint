from pathlib import Path

from rpmlint.checks.AbstractCheck import AbstractCheck


class SysVInitOnSystemdCheck(AbstractCheck):
    def check(self, pkg):
        if pkg.isSource():
            return

        for req in pkg.requires() + pkg.prereq():
            if req[0] == 'insserv':
                self.output.add_info('E', pkg, 'obsolete-insserv-requirement')

        for filename in pkg.files():
            if filename.startswith('/etc/init.d') or filename.startswith('/etc/rc.d/init.d'):
                if Path(filename).name.startswith('boot.'):
                    self.output.add_info('E', pkg, 'deprecated-boot-script', filename)
                else:
                    self.output.add_info('E', pkg, 'deprecated-init-script', filename)
