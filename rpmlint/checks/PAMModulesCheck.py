import re

from rpmlint.checks.AbstractCheck import AbstractCheck


class PAMModulesCheck(AbstractCheck):
    pam_module_re = re.compile(r'^(?:/usr)?/lib(?:64)?/security/([^/]+\.so)$')

    def __init__(self, config, output):
        super().__init__(config, output)
        self.pam_whitelist = config.configuration['PAMModulesWhiteList']

    def check(self, pkg):
        if pkg.isSource():
            return

        files = pkg.files()

        for f in files:
            if f in pkg.ghostFiles():
                continue

            m = self.pam_module_re.match(f)
            if m:
                bn = m.groups()[0]
                if bn not in self.pam_whitelist:
                    self.output.add_info('E', pkg, 'pam-unauthorized-module', bn)
