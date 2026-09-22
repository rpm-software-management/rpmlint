"""
In-memory representation of (RPM) packages for rpmlint checks.

This package is a split of the former monolithic ``rpmlint/pkg.py``;
everything is re-exported here so ``from rpmlint.pkg import Pkg``
and friends keep working unchanged.
"""

from rpmlint.pkg.base import AbstractPkg
from rpmlint.pkg.fake import FakeHeader, FakePkg
from rpmlint.pkg.rpm import get_installed_pkgs, InstalledPkg, Pkg
from rpmlint.pkg.utils import (catcmd, compareEVR, compression_algorithm,
                               DepInfo, formatRequire, get_magic,
                               has_forbidden_controlchars, has_magic, is_utf8,
                               is_utf8_bytestr, parse_deps, PREREQ_FLAG,
                               rangeCompare, RPM_SCRIPTLETS, SCRIPT_TAGS,
                               stringToVersion, versionToString)

__all__ = [
    'AbstractPkg',
    'DepInfo',
    'FakeHeader',
    'FakePkg',
    'InstalledPkg',
    'PREREQ_FLAG',
    'Pkg',
    'RPM_SCRIPTLETS',
    'SCRIPT_TAGS',
    'catcmd',
    'compareEVR',
    'compression_algorithm',
    'formatRequire',
    'get_installed_pkgs',
    'get_magic',
    'has_forbidden_controlchars',
    'has_magic',
    'is_utf8',
    'is_utf8_bytestr',
    'parse_deps',
    'rangeCompare',
    'stringToVersion',
    'versionToString',
]
