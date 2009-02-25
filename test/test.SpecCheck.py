# -*- coding: utf-8 -*-

import re
import unittest
import Testing
import SpecCheck

class TestSpecCheck(unittest.TestCase):
    def setUp(self):
        self.pkg = Testing.getTestedSpecPackage('SpecCheck')
        Testing.startTest()
    def testcheck(self):
        SpecCheck.check.check_spec(self.pkg, self.pkg.name)
        out = "\n".join(Testing.getOutput())
        self.assertTrue(re.search("patch-not-applied Patch3", out));
        self.assertFalse(re.search("patch-not-applied Patch\\b", out));
        self.assertFalse(re.search("patch-not-applied Patch[0124]", out));
        self.assertFalse(re.search("libdir-macro-in-noarch-package", out));

if __name__ == '__main__':
    unittest.main()
