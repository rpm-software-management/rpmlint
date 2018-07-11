import os

import pytest
from rpmlint import SCLCheck

from Testing import getTestedPackage, getTestedSpecPackage


@pytest.mark.parametrize('package', ['spec/SpecCheck', 'binary/python3-power'])
def test_nonscl_spec_silent(capsys, package):
    '''SCL check on non-SCL spec has to be silent'''
    pkg = getTestedSpecPackage('spec/SpecCheck')
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert not out


@pytest.mark.parametrize('package', ['nodejs010-1', 'nodejs010-nodejs-0.10.3',
                                     'nodejs010-nodejs-forever'])
def test_scl_source_rpm(capsys, package):
    '''
    A bunch of testing source RPM packages using SCL
    Assuming they are all OK and except silent output
    While adding more checks, this might change
    '''
    SCLCheck.check.check(getTestedPackage(os.path.join('source', package)))
    out, err = capsys.readouterr()
    assert not out


@pytest.mark.parametrize('package', ['nodejs010-runtime', 'nodejs010-nodejs-0.10.3',
                                     'nodejs010-nodejs-oauth'])
def test_scl_binary_rpm(capsys, package):
    '''
    A bunch of testing binary RPM packages using SCL
    Assuming they are all OK and except silent output
    While adding more checks, this might change
    '''
    SCLCheck.check.check(getTestedPackage(os.path.join('binary', package)))
    out, err = capsys.readouterr()
    assert not out


@pytest.mark.parametrize('package', ['spec/nodejs-good', 'spec/nodejs010'])
def test_correct_spec(capsys, package):
    '''Tests probably correct nodejs.spec and nodejs010.spec'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert not out


@pytest.mark.parametrize('package', ['spec/nodejs-undeclared', 'spec/nodejs010-undeclared'])
def test_undeclared(capsys, package):
    '''Tests SCL specs without %scl definition or %scl_package calls'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'undeclared-scl' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-nobuild'])
def test_nobuild(capsys, package):
    '''Tests SCL metapackage without build subpackage'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'no-build-in-scl-metapackage' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-noruntime'])
def test_noruntime(capsys, package):
    '''Tests SCL metapackage without runtime subpackage'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'no-runtime-in-scl-metapackage' in out
    assert 'scl-main-metapackage-contains-files' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-missing-requires'])
def test_missing_requires(capsys, package):
    '''Tests SCL metapackage without scl-utils-build (B)Rs'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'scl-metapackage-without-scl-utils-build-br' in out
    assert 'scl-build-without-requiring-scl-utils-build' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-alien-subpackage', 'spec/nodejs010-alien-subpackage-n'])
def test_alien_subpackage(capsys, package):
    '''Tests SCL metapackage with extra subpackage'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'weird-subpackage-in-scl-metapackage' in out
    assert 'hehe' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-nosclinstall'])
def test_nosclinstall(capsys, package):
    '''Tests SCL metapackage that doesn't call %scl_install'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'scl-metapackage-without-%scl_install' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-noarch-libdir'])
def test_noarch(capsys, package):
    '''Tests noarch SCL metapackages (not) containing %{_libdir}'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'noarch-scl-metapackage-with-libdir' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-badfiles'])
def test_badfiles(capsys, package):
    '''Tests SCL metapackage %files section checks'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'scl-main-metapackage-contains-files' in out
    assert 'scl-runtime-package-without-%scl_files' in out
    assert 'scl-build-package-without-rpm-macros' in out


@pytest.mark.parametrize('package', ['spec/nodejs-no-pkg_name'])
def test_no_pkg_name(capsys, package):
    '''Tests SCL spec without pkg_name definition'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'missing-pkg_name-definition' in out


@pytest.mark.parametrize('package', ['spec/nodejs-name-without-prefix'])
def test_name_without_prefix(capsys, package):
    '''Tests SCL spec without prefixed name'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'name-without-scl-prefix' in out


@pytest.mark.parametrize('package', ['spec/nodejs-name-with-noncondition-prefix'])
def test_name_with_prefix_without_condition(capsys, package):
    '''
    Tests SCL spec with prefixed name without condition in scl_prefix macro
    '''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'scl-prefix-without-condition' in out


@pytest.mark.parametrize('package', ['spec/nodejs-conflicts-without-prefix'])
def test_conflicts_without_prefix(capsys, package):
    '''Tests SCL spec with nonprefixed conflicts'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'obsoletes-or-conflicts-without-scl-prefix' in out


@pytest.mark.parametrize('package', ['spec/nodejs-provides-without-prefix'])
def test_provides_without_prefix(capsys, package):
    '''Tests SCL spec with nonprefixed provides'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'provides-without-scl-prefix' in out


@pytest.mark.parametrize('package', ['spec/nodejs-norequire'])
def test_main_package_without_scl_require(capsys, package):
    '''
    Tests SCL spec where the main package doesn't require anything
    from collection
    '''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'doesnt-require-scl-runtime-or-other-scl-package' in out


@pytest.mark.parametrize('package', ['spec/nodejs-n-noprefix'])
def test_n_supbackage_without_prefix(capsys, package):
    '''
    Tests SCL spec where a subpackage uses -n and doesn't start with
    SCL prefix
    '''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'subpackage-with-n-without-scl-prefix' in out


@pytest.mark.parametrize('package', ['spec/nodejs-setup-no-n'])
def test_setup_without_n(capsys, package):
    '''Tests SCL spec where setup doesn't use -n option'''
    pkg = getTestedSpecPackage(package)
    SCLCheck.check.check_spec(pkg, pkg.name)
    out, err = capsys.readouterr()
    assert 'scl-setup-without-n' in out


@pytest.mark.parametrize('package', ['binary/nodejs110-nodejs-oauth'])
def test_scl_name_screwed_up(capsys, package):
    '''
    SCL check on SCL package that differs it's name from scl tree folder
    '''
    SCLCheck.check.check(getTestedPackage(package))
    out, err = capsys.readouterr()
    assert 'scl-name-screwed-up' in out


@pytest.mark.parametrize('package', ['binary/outside-nodejs010-nodejs-oauth'])
def test_scl_forbidden_folders(capsys, package):
    '''SCL check on SCL package that has files in forbidden folders'''
    SCLCheck.check.check(getTestedPackage(package))
    out, err = capsys.readouterr()
    assert 'file-outside-of-scl-tree' in out


@pytest.mark.parametrize('package', ['binary/macros-nodejs010-nodejs-oauth'])
def test_scl_macros_outside_of_build(capsys, package):
    '''SCL check on SCL package that has files in forbidden folders'''
    SCLCheck.check.check(getTestedPackage(package))
    out, err = capsys.readouterr()
    assert 'scl-rpm-macros-outside-of-build' in out
