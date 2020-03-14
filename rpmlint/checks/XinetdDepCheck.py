from rpmlint.checks.AbstractCheck import AbstractCheck


class XinetdDepCheck(AbstractCheck):
    def check(self, pkg):
        if pkg.is_source:
            return

        for req in pkg.requires + pkg.prereq:
            if req[0] == 'xinetd':
                self.output.add_info('E', pkg, 'obsolete-xinetd-requirement')
