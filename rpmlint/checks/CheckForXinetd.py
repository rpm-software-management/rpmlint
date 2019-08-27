from rpmlint.checks.AbstractCheck import AbstractCheck


class CheckForXinetd(AbstractCheck):
    def check(self, pkg):
        if pkg.isSource():
            return

        for req in pkg.requires() + pkg.prereq():
            if req[0] == 'xinetd':
                self.output.add_info('E', pkg, 'obsolete-xinetd-requirement')
