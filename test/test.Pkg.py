# -*- coding: utf-8 -*-

import rpm
import unittest
import Testing
import Pkg

class TestPkg(unittest.TestCase):
    def setUp(self):
        Testing.startTest()

    def test_parse_deps(self):
        for (arg, exp) in (
            ("a, b < 1.0 c = 5:2.0-3 d",
             [("a", 0, (None, None, None)),
              ("b", rpm.RPMSENSE_LESS, (None, "1.0", None)),
              ("c", rpm.RPMSENSE_EQUAL, ("5", "2.0", "3")),
              ("d", 0, (None, None, None))]),
            ):
            self.assertEqual(Pkg.parse_deps(arg), exp)

    def test_rangeCompare(self):
        for (req, prov) in (
            (("foo", rpm.RPMSENSE_LESS, (None, "1.0", None)),
             ("foo", rpm.RPMSENSE_EQUAL, ("1", "0.5", None))),
            ):
            self.assertFalse(Pkg.rangeCompare(req, prov))

if __name__ == '__main__':
    unittest.main()
