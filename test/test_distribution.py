import os

import DistributionCheck
import Testing


class Tools(object):
    '''Class providing basic tools for other classes'''

    def _rpm_test_output(self, rpm):
        '''Wrapper that checks RPM package and returns output'''
        with Testing.getTestedPackage(rpm) as pkg:
            Testing.startTest()
            DistributionCheck.check.check(pkg)
            return Testing.getOutput()


class TestDistribution(Tools):

    def test_distribution_tags(self):
        for package in ['ngircd']:
            out = self._rpm_test_output(os.path.join('binary', package))
            assert 'invalid-distribution' not in "\n".join(out)
            assert 'invalid-vendor' not in "\n".join(out)
