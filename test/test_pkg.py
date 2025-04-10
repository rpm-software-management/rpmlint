import os
import subprocess
import unittest.mock as mock

import pytest
import rpm
from rpmlint.pkg import parse_deps, rangeCompare

from Testing import get_tested_package


def test_parse_deps():
    for (arg, exp) in (
        ('a, b < 1.0 c = 5:2.0-3 d',
         [('a', 0, (None, None, None)),
          ('b', rpm.RPMSENSE_LESS, (None, '1.0', None)),
          ('c', rpm.RPMSENSE_EQUAL, (5, '2.0', '3')),
          ('d', 0, (None, None, None))]),
    ):
        assert parse_deps(arg) == exp


def test_range_compare():
    for (req, prov) in (
        (('foo', rpm.RPMSENSE_LESS, (None, '1.0', None)),
         ('foo', rpm.RPMSENSE_EQUAL, (1, '0.5', None))),
    ):
        assert not rangeCompare(req, prov)


@pytest.mark.parametrize('package', ['binary/python311-pytest-xprocess'])
@pytest.mark.skipif(os.getuid() == 0, reason='Root has full permission')
def test_extract_fail(package, tmp_path):
    """
    Check that rpm2cpio fails to extract this package because it has no
    permissions to some files.
    """

    with mock.patch('shutil.which') as mock_which:
        mock_which.return_value = None
        # the package cannot be extracted using rpm2cpio because it contains a directory without 'x' permission
        with pytest.raises(subprocess.CalledProcessError) as exc:
            get_tested_package(package, tmp_path)
        mock_which.assert_called_once_with('rpm2archive')
        # check that it was rpm2cpio what failed
        assert exc.match(r'rpm2cpio .*')
