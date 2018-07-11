# -*- coding: utf-8 -*-

import unittest

from rpmlint import PamCheck

import Testing


class TestPamCheck(unittest.TestCase):

    def setUp(self):
        self.pkg = Testing.getTestedPackage('binary/PamCheck')
        Testing.startTest()

    def tearDown(self):
        self.pkg.cleanup()

    def testcheck(self):
        PamCheck.check.check(self.pkg)
        self.assertEqual(Testing.getOutput(),
                         ['PamCheck.i586: E: use-old-pam-stack '
                          '/etc/pam.d/PamCheck (line 1)'])


if __name__ == '__main__':
    unittest.main()
