# -*- coding: utf-8 -*-

import unittest

import SpecCheck
import Testing


class TestSpecCheck(unittest.TestCase):

    def setUp(self):
        self.pkg = Testing.getTestedSpecPackage('spec/SpecCheck3')
        Testing.startTest()

    def testcheck(self):
        SpecCheck.check.check_spec(self.pkg, self.pkg.name)
        out = "\n".join(Testing.getOutput())
        self.assertFalse("patch-not-applied" in out)

if __name__ == '__main__':
    unittest.main()
