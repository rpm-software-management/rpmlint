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
        self.assertTrue("patch-not-applied Patch3" in out)
        self.assertFalse(re.search("patch-not-applied Patch\\b", out))
        self.assertFalse(re.search("patch-not-applied Patch[01245]", out))
        self.assertTrue("libdir-macro-in-noarch-package" not in out)
        self.assertTrue(len(re.findall("macro-in-comment", out)) == 1)
        self.assertTrue("unversioned-explicit-provides unversioned-provides"
                        in out)
        self.assertTrue("unversioned-explicit-provides versioned-provides"
                        not in out)
        self.assertTrue("unversioned-explicit-obsoletes unversioned-obsoletes"
                        in out)
        self.assertTrue("unversioned-explicit-obsoletes versioned-obsoletes"
                        not in out)

if __name__ == '__main__':
    unittest.main()
