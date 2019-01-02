import os

import BinariesCheck
import Testing


class TestForbiddenCCalls(Testing.OutputTest):

    @classmethod
    def setup_class(cls):
        cls.check = BinariesCheck.check.check

    def test_forbidden_c_calls(self):
        for package in ['cyrus-imapd', 'dovecot']:
            out = self._rpm_test_output(os.path.join('binary', package))
            assert 'crypto-policy-non-compliance' in "\n".join(out)

    def test_waived_forbidden_c_calls(self):
        for package in ['ngircd']:
            out = self._rpm_test_output(os.path.join('binary', package))
            assert 'crypto-policy-non-compliance' not in "\n".join(out)

    def test_lto_bytecode(self):
        for package in ['libreiserfscore-devel']:
            out = self._rpm_test_output(os.path.join('binary', package))
            assert 'lto-bytecode' in "\n".join(out)
