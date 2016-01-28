import os

import BinariesCheck
import Testing


class Tools(object):
    '''Class providing basic tools for other classes'''

    def _rpm_test_output(self, rpm):
        '''Wrapper that checks RPM package and returns output'''
        with Testing.getTestedPackage(rpm) as pkg:
            Testing.startTest()
            BinariesCheck.check.check(pkg)
            return Testing.getOutput()


class TestForbiddenCCalls(Tools):

    def test_forbidden_c_calls(self):
        for package in ['cyrus-imapd', 'dovecot']:
            out = self._rpm_test_output(os.path.join('binary', package))
            assert 'crypto-policy-non-compliance' in "\n".join(out)

    def test_waived_forbidden_c_calls(self):
        for package in ['ngircd']:
            out = self._rpm_test_output(os.path.join('binary', package))
            assert 'crypto-policy-non-compliance' not in "\n".join(out)

# ex: ts=4 sw=4 et
