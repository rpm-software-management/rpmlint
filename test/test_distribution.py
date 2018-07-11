import os

from rpmlint import DistributionCheck

import Testing


class TestDistribution(Testing.OutputTest):

    @classmethod
    def setup_class(cls):
        cls.check = DistributionCheck.check.check

    def test_distribution_tags(self):
        for package in ['ngircd']:
            out = self._rpm_test_output(os.path.join('binary', package))
            assert 'invalid-distribution' not in "\n".join(out)
            assert 'invalid-vendor' not in "\n".join(out)
