# -*- coding: utf-8 -*-

import re
import unittest

import SpecCheck
import Testing


class TestCheckInclude(unittest.TestCase):

    def setUp(self):
        self.pkg = Testing.getTestedPackage('source/CheckInclude')
        Testing.startTest()

    def testcheck(self):
        SpecCheck.check.check_source(self.pkg)
        out = "\n".join(Testing.getOutput())
        self.assertFalse(re.search(r" E: specfile-error error: query of specfile .*\.spec failed, can't parse", out))


if __name__ == '__main__':
    unittest.main()
