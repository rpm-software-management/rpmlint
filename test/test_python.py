import pytest
from rpmlint.checks.PythonCheck import PythonCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def pythoncheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = PythonCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-doc-in-package'])
def test_python_doc_in_package(tmpdir, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: python-doc-in-package /usr/lib/python2.7/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib/python2.7/site-packages/python-mypackage/docs' in out
    assert 'W: python-doc-in-package /usr/lib/python3.8/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib/python3.8/site-packages/python-mypackage/docs' in out
    assert 'W: python-doc-in-package /usr/lib64/python2.7/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib64/python2.7/site-packages/python-mypackage/docs' in out
    assert 'W: python-doc-in-package /usr/lib64/python3.8/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib64/python3.8/site-packages/python-mypackage/docs' in out


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-tests-in-package'])
def test_python_tests_in_package(tmpdir, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: python-tests-in-package /usr/lib/python2.7/site-packages/python-mypackage/test' in out
    assert 'W: python-tests-in-package /usr/lib/python2.7/site-packages/python-mypackage/tests' in out
    assert 'W: python-tests-in-package /usr/lib/python3.8/site-packages/python-mypackage/test' in out
    assert 'W: python-tests-in-package /usr/lib/python3.8/site-packages/python-mypackage/tests' in out
    assert 'W: python-tests-in-package /usr/lib64/python2.7/site-packages/python-mypackage/test' in out
    assert 'W: python-tests-in-package /usr/lib64/python2.7/site-packages/python-mypackage/tests' in out
    assert 'W: python-tests-in-package /usr/lib64/python3.8/site-packages/python-mypackage/test' in out
    assert 'W: python-tests-in-package /usr/lib64/python3.8/site-packages/python-mypackage/tests' in out


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-egg-info-distutils-style'])
def test_python_distutils_egg_info(tmpdir, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: python-egg-info-distutils-style /usr/lib/python2.7/site-packages/mydistutilspackage.egg-info' in out
    assert 'E: python-egg-info-distutils-style /usr/lib/python3.8/site-packages/mydistutilspackage.egg-info' in out
    assert 'E: python-egg-info-distutils-style /usr/lib64/python2.7/site-packages/mydistutilspackage.egg-info' in out
    assert 'E: python-egg-info-distutils-style /usr/lib64/python3.8/site-packages/mydistutilspackage.egg-info' in out


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-doc-in-site-packages'])
def test_python_doc_in_site_packages(tmpdir, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: python-doc-in-site-packages /usr/lib/python2.7/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib/python2.7/site-packages/docs' in out
    assert 'E: python-doc-in-site-packages /usr/lib/python3.8/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib/python3.8/site-packages/docs' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python2.7/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python2.7/site-packages/docs' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python3.8/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python3.8/site-packages/docs' in out


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-src-in-site-packages'])
def test_python_src_in_site_packages(tmpdir, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: python-src-in-site-packages /usr/lib/python2.7/site-packages/src' in out
    assert 'E: python-src-in-site-packages /usr/lib/python3.8/site-packages/src' in out
    assert 'E: python-src-in-site-packages /usr/lib64/python2.7/site-packages/src' in out
    assert 'E: python-src-in-site-packages /usr/lib64/python3.8/site-packages/src' in out


@pytest.mark.parametrize('package', ['binary/pythoncheck-python-tests-in-site-packages'])
def test_python_tests_in_site_packages(tmpdir, package, pythoncheck):
    output, test = pythoncheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: python-tests-in-site-packages /usr/lib/python2.7/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib/python2.7/site-packages/tests' in out
    assert 'E: python-tests-in-site-packages /usr/lib/python3.8/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib/python3.8/site-packages/tests' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python2.7/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python2.7/site-packages/tests' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python3.8/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python3.8/site-packages/tests' in out
