# -*- coding: utf-8 -*-

import unittest

from DocFilesCheck import _stripVersionedDeps
import Testing


class DocFilesCheck(unittest.TestCase):
    def setUp(self):
        Testing.startTest()
    def testcheck(self):
        for (arg, exp) in ((['a'],['a']),
                           ([], []),
                           (['a', 'b'], ['a', 'b']),
                           (['a', 'b', 'c', 'd'], ['a', 'b', 'c', 'd']),
                           (['a', '>', '0'], ['a']),
                           (['a', '>', '0', 'b'], ['a', 'b']),
                           (['a', '>', '0', 'b', '>', '0'], ['a', 'b']),
                           ):
            self.assertEqual(_stripVersionedDeps(arg), exp)

if __name__ == '__main__':
    unittest.main()
