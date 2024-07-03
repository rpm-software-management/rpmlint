from mockdata.mock_python import (
    IPythonMissingRequirePackage,
    PythonDocFolderPackage,
    PythonDocModulePackage,
    PythonEggInfoFileackage,
    PythonFlitFedoraMockPackage,
    PythonFlitLeftoverRequirePackage,
    PythonFlitMissingRequirePackage,
    PythonFlitMockPackage,
    PythonIcecreamLeftoverRequirePackage,
    PythonIcecreamMissingRequirePackage,
    PythonIcecreamPackage,
    PythonJupyterEventsMockPackage,
    PythonJupyterServerFileidMockPackage,
    PythonMultiplePYCMockPackage,
    PythonScikitBuildMockPackage,
    PythonSinglePYCMockPackage,
)
import pytest
from rpmlint.checks.PythonCheck import PythonCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


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


@pytest.mark.parametrize('package', [PythonDocFolderPackage])
def test_python_doc_in_package(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-doc-in-package /usr/lib/python2.7/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib/python2.7/site-packages/python-mypackage/docs' in out
    assert 'W: python-doc-in-package /usr/lib/python3.10/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib/python3.10/site-packages/python-mypackage/docs' in out
    assert 'W: python-doc-in-package /usr/lib64/python2.7/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib64/python2.7/site-packages/python-mypackage/docs' in out
    assert 'W: python-doc-in-package /usr/lib64/python3.10/site-packages/python-mypackage/doc' in out
    assert 'W: python-doc-in-package /usr/lib64/python3.10/site-packages/python-mypackage/docs' in out


@pytest.mark.parametrize('package', [PythonDocModulePackage])
def test_python_doc_module_in_package(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-doc-in-package /usr/lib/python2.7/site-packages/python-mypackage/doc' not in out
    assert 'W: python-doc-in-package /usr/lib/python2.7/site-packages/python-mypackage/docs' not in out
    assert 'W: python-doc-in-package /usr/lib/python3.10/site-packages/python-mypackage/doc' not in out
    assert 'W: python-doc-in-package /usr/lib/python3.10/site-packages/python-mypackage/docs' not in out
    assert 'W: python-doc-in-package /usr/lib64/python2.7/site-packages/python-mypackage/doc' not in out
    assert 'W: python-doc-in-package /usr/lib64/python2.7/site-packages/python-mypackage/docs' not in out
    assert 'W: python-doc-in-package /usr/lib64/python3.10/site-packages/python-mypackage/doc' not in out
    assert 'W: python-doc-in-package /usr/lib64/python3.10/site-packages/python-mypackage/docs' not in out


@pytest.mark.parametrize('package', [PythonEggInfoFileackage])
def test_python_distutils_egg_info(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: python-egg-info-distutils-style /usr/lib/python2.7/site-packages/mydistutilspackage.egg-info' in out
    assert 'E: python-egg-info-distutils-style /usr/lib/python3.10/site-packages/mydistutilspackage.egg-info' in out
    assert 'E: python-egg-info-distutils-style /usr/lib64/python2.7/site-packages/mydistutilspackage.egg-info' in out
    assert 'E: python-egg-info-distutils-style /usr/lib64/python3.10/site-packages/mydistutilspackage.egg-info' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files=[
        '/usr/lib/python2.7/site-packages/doc',
        '/usr/lib/python2.7/site-packages/docs',
        '/usr/lib/python3.10/site-packages/doc',
        '/usr/lib/python3.10/site-packages/docs',
        '/usr/lib64/python2.7/site-packages/doc',
        '/usr/lib64/python2.7/site-packages/docs',
        '/usr/lib64/python3.10/site-packages/doc',
        '/usr/lib64/python3.10/site-packages/docs',
    ]
)])
def test_python_doc_in_site_packages(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: python-doc-in-site-packages /usr/lib/python2.7/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib/python2.7/site-packages/docs' in out
    assert 'E: python-doc-in-site-packages /usr/lib/python3.10/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib/python3.10/site-packages/docs' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python2.7/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python2.7/site-packages/docs' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python3.10/site-packages/doc' in out
    assert 'E: python-doc-in-site-packages /usr/lib64/python3.10/site-packages/docs' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files=[
        '/usr/lib/python2.7/site-packages/src',
        '/usr/lib/python3.10/site-packages/src',
        '/usr/lib64/python2.7/site-packages/src',
        '/usr/lib64/python3.10/site-packages/src',
    ]
)])
def test_python_src_in_site_packages(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: python-src-in-site-packages /usr/lib/python2.7/site-packages/src' in out
    assert 'E: python-src-in-site-packages /usr/lib/python3.10/site-packages/src' in out
    assert 'E: python-src-in-site-packages /usr/lib64/python2.7/site-packages/src' in out
    assert 'E: python-src-in-site-packages /usr/lib64/python3.10/site-packages/src' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files=[
        '/usr/lib/python2.7/site-packages/test',
        '/usr/lib/python2.7/site-packages/tests',
        '/usr/lib/python3.10/site-packages/test',
        '/usr/lib/python3.10/site-packages/tests',
        '/usr/lib64/python2.7/site-packages/test',
        '/usr/lib64/python2.7/site-packages/tests',
        '/usr/lib64/python3.10/site-packages/test',
        '/usr/lib64/python3.10/site-packages/tests',
    ]
)])
def test_python_tests_in_site_packages(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: python-tests-in-site-packages /usr/lib/python2.7/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib/python2.7/site-packages/tests' in out
    assert 'E: python-tests-in-site-packages /usr/lib/python3.10/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib/python3.10/site-packages/tests' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python2.7/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python2.7/site-packages/tests' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python3.10/site-packages/test' in out
    assert 'E: python-tests-in-site-packages /usr/lib64/python3.10/site-packages/tests' in out


@pytest.mark.parametrize('package', [PythonFlitMockPackage,
                                     PythonJupyterServerFileidMockPackage,
                                     PythonJupyterEventsMockPackage,
                                     PythonScikitBuildMockPackage,
                                     PythonFlitFedoraMockPackage,])
def test_python_dependencies_metadata(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-missing-require' not in out
    assert 'W: python-leftover-require' not in out


@pytest.mark.parametrize('package', [PythonIcecreamPackage])
def test_python_dependencies_requires(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-missing-require' not in out
    assert 'W: python-leftover-require' not in out


@pytest.mark.parametrize('package', [PythonIcecreamMissingRequirePackage])
def test_python_dependencies_missing_requires(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-missing-require' in out


@pytest.mark.parametrize('package', [PythonFlitMissingRequirePackage])
def test_python_dependencies_missing_metadata(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-missing-require' in out


@pytest.mark.parametrize('package', [
    PythonIcecreamLeftoverRequirePackage,
    PythonFlitLeftoverRequirePackage,
])
def test_python_dependencies_leftover(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-leftover-require' in out


@pytest.mark.parametrize('package', [PythonMultiplePYCMockPackage])
def test_python_pyc_multiple_versions(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-pyc-multiple-versions expected: 310' in out


@pytest.mark.parametrize('package', [PythonSinglePYCMockPackage])
def test_python_pyc_single_version(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-pyc-multiple-versions' not in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(files=['/usr/share/doc/packages/python-blinker-doc/.doctrees']),
    get_tested_mock_package(files=['/usr/lib/python3.11/site-packages/python-blinker/.doctrees']),
])
def test_python_sphinx_doctrees_leftover_warn(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-sphinx-doctrees-leftover' in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(files=['/usr/lib/python3.11/site-packages/python-blinker/doctrees.py']),
    get_tested_mock_package(files=['/usr/share/doc/packages/python-blinker-doc/doctrees']),
    get_tested_mock_package(files=['/usr/share/doc/packages/python-blinker-doc/.doctrees.html']),
])
def test_python_sphinx_doctrees_leftover_nowarn(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-sphinx-doctrees-leftover' not in out


@pytest.mark.parametrize('package', [IPythonMissingRequirePackage])
def test_python_dependencies_ipython(package, test, output):
    test.check(package)
    out = output.print_results(output.results)

    requirements = [
        'backcall',
        'decorator',
        'jedi',
        'matplotlib-inline',
        'pickleshare',
        'prompt_toolkit',
        'pygments',
        'stack_data',
        'traitlets',
    ]

    for req in requirements:
        assert f'W: python-missing-require {req}' in out

    # typing_extensions is in section [:python_version < "3.10"]
    assert 'W: python-missing-require typing_extensions' not in out

    # req312 is in section [:python_version > "3.11"]
    assert 'W: python-missing-require req312' in out

    # leftover is in section [:python_version < "3.10"]
    assert 'W: python-leftover-require python-leftover' in out
    assert 'W: python-leftover-require python-no-leftover' not in out
