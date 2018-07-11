import os

import pytest
from rpmlint import SourceCheck

from Testing import getTestedPackage


@pytest.mark.parametrize('package', ['wrongsrc'])
def test_inconsistent_file_extension(capsys, package):
    SourceCheck.check.check(getTestedPackage(os.path.join('source', package)))
    out, err = capsys.readouterr()
    assert 'inconsistent-file-extension' in out
