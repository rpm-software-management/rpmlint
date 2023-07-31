import pytest
from rpmlint.checks.PythonCheck import PythonCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def pythoncheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = PythonCheck(CONFIG, output)
    yield output, test


@pytest.fixture
def output(pythoncheck):
    output, _test = pythoncheck
    yield output


@pytest.fixture
def test(pythoncheck):
    _output, test = pythoncheck
    yield test


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-doc-in-package'])
def test_python_doc_in_package(tmp_path, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'W: python-doc-in-package /usr/lib/python2.7/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib/python2.7/site-packages/python-mypackage/docs' in out
    assert 'W: python-doc-in-package /usr/lib/python3.10/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib/python3.10/site-packages/python-mypackage/docs' in out
    assert 'W: python-doc-in-package /usr/lib64/python2.7/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib64/python2.7/site-packages/python-mypackage/docs' in out
    assert 'W: python-doc-in-package /usr/lib64/python3.10/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib64/python3.10/site-packages/python-mypackage/docs' in out


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-doc-module-in-package'])
def test_python_doc_module_in_package(tmp_path, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'W: python-doc-in-package /usr/lib/python2.7/site-packages/python-mypackage/doc' not in out
    assert 'W: python-doc-in-package /usr/lib/python2.7/site-packages/python-mypackage/docs' not in out
    assert 'W: python-doc-in-package /usr/lib/python3.10/site-packages/python-mypackage/doc' not in out
    assert 'W: python-doc-in-package /usr/lib/python3.10/site-packages/python-mypackage/docs' not in out
    assert 'W: python-doc-in-package /usr/lib64/python2.7/site-packages/python-mypackage/doc' not in out
    assert 'W: python-doc-in-package /usr/lib64/python2.7/site-packages/python-mypackage/docs' not in out
    assert 'W: python-doc-in-package /usr/lib64/python3.10/site-packages/python-mypackage/doc' not in out
    assert 'W: python-doc-in-package /usr/lib64/python3.10/site-packages/python-mypackage/docs' not in out


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-egg-info-distutils-style'])
def test_python_distutils_egg_info(tmp_path, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: python-egg-info-distutils-style /usr/lib/python2.7/site-packages/mydistutilspackage.egg-info' in out
    assert 'E: python-egg-info-distutils-style /usr/lib/python3.10/site-packages/mydistutilspackage.egg-info' in out
    assert 'E: python-egg-info-distutils-style /usr/lib64/python2.7/site-packages/mydistutilspackage.egg-info' in out
    assert 'E: python-egg-info-distutils-style /usr/lib64/python3.10/site-packages/mydistutilspackage.egg-info' in out


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-doc-in-site-packages'])
def test_python_doc_in_site_packages(tmp_path, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: python-doc-in-site-packages /usr/lib/python2.7/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib/python2.7/site-packages/docs' in out
    assert 'E: python-doc-in-site-packages /usr/lib/python3.10/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib/python3.10/site-packages/docs' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python2.7/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python2.7/site-packages/docs' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python3.10/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python3.10/site-packages/docs' in out


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-src-in-site-packages'])
def test_python_src_in_site_packages(tmp_path, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: python-src-in-site-packages /usr/lib/python2.7/site-packages/src' in out
    assert 'E: python-src-in-site-packages /usr/lib/python3.10/site-packages/src' in out
    assert 'E: python-src-in-site-packages /usr/lib64/python2.7/site-packages/src' in out
    assert 'E: python-src-in-site-packages /usr/lib64/python3.10/site-packages/src' in out


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-tests-in-site-packages'])
def test_python_tests_in_site_packages(tmp_path, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'E: python-tests-in-site-packages /usr/lib/python2.7/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib/python2.7/site-packages/tests' in out
    assert 'E: python-tests-in-site-packages /usr/lib/python3.10/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib/python3.10/site-packages/tests' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python2.7/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python2.7/site-packages/tests' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python3.10/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python3.10/site-packages/tests' in out


@pytest.mark.parametrize('package', [
    'binary/python3-flit-3.8.0',
    'binary/python3-icecream-2.1.3',
    'binary/python310-jupyter-server-fileid-0.9.0',
    'binary/python310-scikit-build-0.17.2',
    'binary/python310-jupyter-events-0.6.3',
])
def test_python_dependencies(tmp_path, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'W: python-missing-require' not in out
    assert 'W: python-leftover-require' not in out


@pytest.mark.parametrize('package', [
    'binary/python3-icecream-missingdeps',
    'binary/python3-flit-missingdeps',
])
def test_python_dependencies_missing(tmp_path, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'W: python-missing-require' in out


@pytest.mark.parametrize('package', [
    'binary/python3-icecream-leftovers',
    'binary/python3-flit-leftovers',
])
def test_python_dependencies_leftover(tmp_path, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'W: python-leftover-require' in out


@pytest.mark.parametrize('package', [
    # Sources can be found at
    # https://build.opensuse.org/package/show/devel:openSUSE:Factory:rpmlint:tests/different-python-pyc
    'binary/python39-blinker-1.6.2',
])
def test_python_pyc_multiple_versions(tmp_path, package, output, test):
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'W: python-pyc-multiple-versions expected: 310' in out


@pytest.mark.parametrize('package', [
    'binary/python3-flit-3.8.0',
    'binary/python3-icecream-2.1.3',
    'binary/python310-jupyter-server-fileid-0.9.0',
    'binary/python310-scikit-build-0.17.2',
    'binary/python310-jupyter-events-0.6.3',
])
def test_python_pyc_single_version(tmp_path, package, output, test):
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)
    assert 'W: python-pyc-multiple-versions' not in out
