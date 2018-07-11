from rpmlint import SpecCheck

from Testing import getTestedPackage


def test_check_include(capsys):
    SpecCheck.check.check_source(getTestedPackage('source/CheckInclude'))
    out, err = capsys.readouterr()
    assert 'E: specfile-error error: query of specfile' not in out
