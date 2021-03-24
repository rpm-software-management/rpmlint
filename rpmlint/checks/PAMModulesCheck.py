import re

from rpmlint.checks.AbstractCheck import AbstractCheck


class PAMModulesCheck(AbstractCheck):
    pam_module_re = re.compile(r'^(?:/usr)?/lib(?:64)?/security/([^/]+\.so)$')

    def __init__(self, config, output):
        super().__init__(config, output)
        self.pam_authorized_modules = config.configuration['PAMAuthorizedModules']

    def check(self, pkg):
        if pkg.is_source:
            return

        for f in pkg.files:
            if f in pkg.ghost_files:
                continue

            m = self.pam_module_re.match(f)
            if m:
                bn = m.groups()[0]
                if bn not in self.pam_authorized_modules:
                    self.output.add_info('E', pkg, 'pam-unauthorized-module', bn)
