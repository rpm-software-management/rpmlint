import os

import pytest
from rpmlint.checks.SCLCheck import SCLCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package, get_tested_spec_package


@pytest.fixture(scope='function', autouse=True)
def sclcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SCLCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['spec/SpecCheck'])
def test_nonscl_spec_silent(package):
    """SCL check on non-SCL spec has to be silent"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert not out


@pytest.mark.parametrize('package', ['binary/python3-power'])
def test_nonscl_binary_silent(tmpdir, package):
    """SCL check on non-SCL spec has to be silent"""
    output, test = sclcheck()
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert not out


@pytest.mark.parametrize('package', ['nodejs010-1', 'nodejs010-nodejs-0.10.3',
                                     'nodejs010-nodejs-forever'])
def test_scl_source_rpm(tmpdir, package):
    """
    A bunch of testing source RPM packages using SCL
    Assuming they are all OK and except silent output
    While adding more checks, this might change
    """
    output, test = sclcheck()
    test.check(get_tested_package(os.path.join('source', package), tmpdir))
    out = output.print_results(output.results)
    assert not out


@pytest.mark.parametrize('package', ['nodejs010-runtime', 'nodejs010-nodejs-0.10.3',
                                     'nodejs010-nodejs-oauth'])
def test_scl_binary_rpm(tmpdir, package):
    """
    A bunch of testing binary RPM packages using SCL
    Assuming they are all OK and except silent output
    While adding more checks, this might change
    """
    output, test = sclcheck()
    test.check(get_tested_package(os.path.join('binary', package), tmpdir))
    out = output.print_results(output.results)
    assert not out


@pytest.mark.parametrize('package', ['spec/nodejs-good', 'spec/nodejs010'])
def test_correct_spec(package):
    """Tests probably correct nodejs.spec and nodejs010.spec"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert not out


@pytest.mark.parametrize('package', ['spec/nodejs-undeclared', 'spec/nodejs010-undeclared'])
def test_undeclared(package):
    """Tests SCL specs without %scl definition or %scl_package calls"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'undeclared-scl' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-nobuild'])
def test_nobuild(package):
    """Tests SCL metapackage without build subpackage"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'no-build-in-scl-metapackage' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-noruntime'])
def test_noruntime(package):
    """Tests SCL metapackage without runtime subpackage"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'no-runtime-in-scl-metapackage' in out
    assert 'scl-main-metapackage-contains-files' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-missing-requires'])
def test_missing_requires(package):
    """Tests SCL metapackage without scl-utils-build (B)Rs"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'scl-metapackage-without-scl-utils-build-br' in out
    assert 'scl-build-without-requiring-scl-utils-build' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-alien-subpackage', 'spec/nodejs010-alien-subpackage-n'])
def test_alien_subpackage(package):
    """Tests SCL metapackage with extra subpackage"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'weird-subpackage-in-scl-metapackage' in out
    assert 'hehe' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-nosclinstall'])
def test_nosclinstall(package):
    """Tests SCL metapackage that doesn't call %scl_install"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'scl-metapackage-without-%scl_install' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-noarch-libdir'])
def test_noarch(package):
    """Tests noarch SCL metapackages (not) containing %{_libdir}"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'noarch-scl-metapackage-with-libdir' in out


@pytest.mark.parametrize('package', ['spec/nodejs010-badfiles'])
def test_badfiles(package):
    """Tests SCL metapackage %files section checks"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'scl-main-metapackage-contains-files' in out
    assert 'scl-runtime-package-without-%scl_files' in out
    assert 'scl-build-package-without-rpm-macros' in out


@pytest.mark.parametrize('package', ['spec/nodejs-no-pkg_name'])
def test_no_pkg_name(package):
    """Tests SCL spec without pkg_name definition"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'missing-pkg_name-definition' in out


@pytest.mark.parametrize('package', ['spec/nodejs-name-without-prefix'])
def test_name_without_prefix(package):
    """Tests SCL spec without prefixed name"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'name-without-scl-prefix' in out


@pytest.mark.parametrize('package', ['spec/nodejs-name-with-noncondition-prefix'])
def test_name_with_prefix_without_condition(package):
    """
    Tests SCL spec with prefixed name without condition in scl_prefix macro
    """
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'scl-prefix-without-condition' in out


@pytest.mark.parametrize('package', ['spec/nodejs-conflicts-without-prefix'])
def test_conflicts_without_prefix(package):
    """Tests SCL spec with nonprefixed conflicts"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'obsoletes-or-conflicts-without-scl-prefix' in out


@pytest.mark.parametrize('package', ['spec/nodejs-provides-without-prefix'])
def test_provides_without_prefix(package):
    """Tests SCL spec with nonprefixed provides"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'provides-without-scl-prefix' in out


@pytest.mark.parametrize('package', ['spec/nodejs-norequire'])
def test_main_package_without_scl_require(package):
    """
    Tests SCL spec where the main package doesn't require anything
    from collection
    """
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'doesnt-require-scl-runtime-or-other-scl-package' in out


@pytest.mark.parametrize('package', ['spec/nodejs-n-noprefix'])
def test_n_supbackage_without_prefix(package):
    """
    Tests SCL spec where a subpackage uses -n and doesn't start with
    SCL prefix
    """
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'subpackage-with-n-without-scl-prefix' in out


@pytest.mark.parametrize('package', ['spec/nodejs-setup-no-n'])
def test_setup_without_n(package):
    """Tests SCL spec where setup doesn't use -n option"""
    output, test = sclcheck()
    pkg = get_tested_spec_package(package)
    test.check_spec(pkg, pkg.name)
    out = output.print_results(output.results)
    assert 'scl-setup-without-n' in out


@pytest.mark.parametrize('package', ['binary/nodejs110-nodejs-oauth'])
def test_scl_name_screwed_up(tmpdir, package):
    """
    SCL check on SCL package that differs it's name from scl tree folder
    """
    output, test = sclcheck()
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'scl-name-screwed-up' in out


@pytest.mark.parametrize('package', ['binary/outside-nodejs010-nodejs-oauth'])
def test_scl_forbidden_folders(tmpdir, package):
    """SCL check on SCL package that has files in forbidden folders"""
    output, test = sclcheck()
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'file-outside-of-scl-tree' in out


@pytest.mark.parametrize('package', ['binary/macros-nodejs010-nodejs-oauth'])
def test_scl_macros_outside_of_build(tmpdir, package):
    """SCL check on SCL package that has files in forbidden folders"""
    output, test = sclcheck()
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'scl-rpm-macros-outside-of-build' in out
