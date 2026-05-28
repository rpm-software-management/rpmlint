from rpmlint.checks.AbstractCheck import AbstractCheck


class SELinuxIndependentModuleCheck(AbstractCheck):
    ALLOWED_IF_DIR = '/usr/share/selinux/devel/include/distributed/'
    SELINUX_MAIN_POLICY_PACKAGES = [
        'selinux-policy-devel',
    ]

    def __init__(self, config, output):
        super().__init__(config, output)

    def __is_independent_module(self, pkg):
        for req in pkg.requires + pkg.prereq:
            if req[0] == 'selinux-policy-base':
                return True
        return False

    def check(self, pkg):
        # Skip source packages
        if pkg.is_source:
            return

        # Skip main policy packages
        if pkg.name in self.SELINUX_MAIN_POLICY_PACKAGES:
            return

        # Skip packages that are not independent modules
        if not self.__is_independent_module(pkg):
            return

        for filename, _ in pkg.files.items():
            if filename.endswith('.if') and not filename.startswith(self.ALLOWED_IF_DIR):
                self.output.add_info('E', pkg, 'selinux-incorrect-if-file-location', filename)
