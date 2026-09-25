import os
import subprocess
import unittest.mock as mock

import pytest
import rpm
from rpmlint.pkg import parse_deps, Pkg, rangeCompare

from Testing import build_tiny_rpm


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


@pytest.mark.skipif(os.getuid() == 0, reason='Root has full permission')
def test_extract_fail(tmp_path):
    """
    Check that rpm2cpio fails to extract this package because it has no
    permissions to some files.
    """
    rpm_path = build_tiny_rpm(
        tmp_path,
        'noperm-test',
        install_script='mkdir -p %{buildroot}/usr/share/doc/noperm-test\n'
                       'echo data > %{buildroot}/usr/share/doc/noperm-test/file.txt',
        # record the directory without the search bit, the buildroot itself
        # stays readable so rpmbuild can package it as non-root
        files_list='%attr(644,root,root) /usr/share/doc/noperm-test',
    )

    with mock.patch('shutil.which') as mock_which:
        mock_which.return_value = None
        # the package cannot be extracted using rpm2cpio because it contains a directory without 'x' permission
        with pytest.raises(subprocess.CalledProcessError) as exc:
            Pkg(rpm_path, tmp_path)
        mock_which.assert_called_once_with('rpm2archive')
        # check that it was rpm2cpio what failed
        assert exc.match(r'rpm2cpio .*')
