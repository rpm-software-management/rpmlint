# -*- coding: utf-8 -*-

import unittest
import Testing
import PamCheck
# FIXME harcode

class TestPamCheck(unittest.TestCase):
    def setUp(self):
        self.pkg = Testing.getTestedPackage('PamCheck')
        Testing.startTest()
    def tearDown(self):
        self.pkg.cleanup()
    def testcheck(self):
        PamCheck.check.check(self.pkg)
        self.assertEqual( Testing.getOutput(), ['PamCheck.i586: E: use-old-pam-stack /etc/pam.d/PamCheck (line 1)'])

# enjoy \o/
if __name__ == '__main__':
    unittest.main()

#print Testing.getOutput()
