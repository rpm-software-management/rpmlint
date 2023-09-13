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


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files=[
        '/usr/lib/python2.7/site-packages/python-mypackage/doc',
        '/usr/lib/python2.7/site-packages/python-mypackage/docs',
        '/usr/lib/python3.10/site-packages/python-mypackage/doc',
        '/usr/lib/python3.10/site-packages/python-mypackage/docs',
        '/usr/lib64/python2.7/site-packages/python-mypackage/doc',
        '/usr/lib64/python2.7/site-packages/python-mypackage/docs',
        '/usr/lib64/python3.10/site-packages/python-mypackage/doc',
        '/usr/lib64/python3.10/site-packages/python-mypackage/docs',
    ]
)])
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


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/lib/python2.7/site-packages/python-mypackage/doc/__init__.py': {'create_dirs': True, 'include_dirs': 2},
        '/usr/lib/python2.7/site-packages/python-mypackage/docs/__init__.py': {'create_dirs': True, 'include_dirs': 1},
        '/usr/lib64/python2.7/site-packages/python-mypackage/doc/__init__.py': {'create_dirs': True, 'include_dirs': 2},
        '/usr/lib64/python2.7/site-packages/python-mypackage/docs/__init__.py': {'create_dirs': True, 'include_dirs': 1},
        '/usr/lib/python3.10/site-packages/python-mypackage/doc/__init__.py': {'create_dirs': True, 'include_dirs': 2},
        '/usr/lib/python3.10/site-packages/python-mypackage/docs/__init__.py': {'create_dirs': True, 'include_dirs': 1},
        '/usr/lib64/python3.10/site-packages/python-mypackage/doc/__init__.py': {'create_dirs': True, 'include_dirs': 2},
        '/usr/lib64/python3.10/site-packages/python-mypackage/docs/__init__.py': {'create_dirs': True, 'include_dirs': 1},
    }
)])
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


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/lib/python2.7/site-packages/mydistutilspackage.egg-info': {'content': 'Metadata-Version: 2.1\nName: pythoncheck'},
        '/usr/lib/python3.10/site-packages/mydistutilspackage.egg-info': {'content': 'Metadata-Version: 2.1\nName: pythoncheck'},
        '/usr/lib64/python2.7/site-packages/mydistutilspackage.egg-info': {'content': 'Metadata-Version: 2.1\nName: pythoncheck'},
        '/usr/lib64/python3.10/site-packages/mydistutilspackage.egg-info': {'content': 'Metadata-Version: 2.1\nName: pythoncheck'},
    },
)])
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


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        files={
            '/usr/lib/python3.10/site-packages/flit-3.8.0.dist-info/METADATA': {
                'content-path': 'files/python-flit-metadata.txt',
                'create_dirs': True,
            },
        },
        header={
            'requires': [
                'python-flit_core',
                'python-requests',
                'python-tomli-w',
                'python310-docutils',
            ],
        },
    ),
    get_tested_mock_package(
        files={
            '/usr/lib/python3.10/site-packages/jupyter_server_fileid-0.9.0.dist-info/METADATA': {
                'content-path': 'files/python-jupyter_server_fileid-metadata.txt',
                'create_dirs': True
            },
        },
        header={
            'requires': [
                'python-jupyter-events',
                'python-click',
                'python-jupyter-server',
            ],
        },
    ),
    get_tested_mock_package(
        files={
            '/usr/lib/python3.10/site-packages/jupyter_events-0.6.3.dist-info/METADATA': {
                'content-path': 'files/python-jupyter-events-metadata.txt',
                'create_dirs': True
            },
        },
        header={
            'requires': [
                'python-jsonschema',
                'python-python-json-logger',
                'python-pyyaml',
                'python-rfc3339-validator',
                'python-rfc3986-validator',
                'python-traitlets',
                'python-click',
                'python-rich',
                'python-jupyterlite-sphinx',
                'python-myst-parser',
                'python-pydata-sphinx-theme',
                'python-sphinxcontrib-spelling',
                'python-click',
                'python-coverage',
                'python-pre-commit',
                'python-pytest-asyncio',
                'python-pytest-console-scripts',
                'python-pytest-cov',
                'python-pytest',
                'python-rich',
            ],
        },
    ),
    get_tested_mock_package(
        files={
            '/usr/lib/python3.10/site-packages/scikit_build-0.17.2.dist-info/METADATA': {
                'content-path': 'files/python-scikit_build-metadata.txt',
                'create_dirs': True
            },
        },
        header={
            'requires': [
                'python-distro',
                'python-packaging',
                'python-setuptools',
                'python-wheel',
                'python-tomli',
            ],
        },
    ),
])
def test_python_dependencies_metadata(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-missing-require' not in out
    assert 'W: python-leftover-require' not in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/lib/python3.10/site-packages/icecream-2.1.3-py3.10.egg-info/requires.txt': {
            'content': """
asttokens>=2.0.1
colorama>=0.3.9
executing>=0.3.1
pygments>=2.2.0
""",
            'create_dirs': True
        },
    },
    header={
        'requires': [
            'asttokens>=2.0.1',
            'colorama>=0.3.9',
            'executing>=0.3.1',
            'pygments>=2.2.0',
        ],
    },
)])
def test_python_dependencies_requires(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-missing-require' not in out
    assert 'W: python-leftover-require' not in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/lib/python3.10/site-packages/icecream-2.1.3-py3.10.egg-info/requires.txt': {
            'content': """
asttokens>=2.0.1
colorama>=0.3.9
executing>=0.3.1
pygments>=2.2.0
""",
            'create_dirs': True
        },
    },
    header={
        'requires': [
            'asttokens>=2.0.1',
            'executing>=0.3.1',
            'pygments>=2.2.0',
        ],
    },
)])
def test_python_dependencies_missing_requires(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-missing-require' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files={
        '/usr/lib/python3.10/site-packages/flit-3.8.0.dist-info/METADATA': {
            'content-path': 'files/python-flit-metadata.txt',
            'create_dirs': True
        },
    },
    header={
        'requires': [
            'python3-flit-core',
            'python3-requests',
            'python3-tomli-w',
        ],
    },
)])
def test_python_dependencies_missing_metadata(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-missing-require' in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        files={
            '/usr/lib/python3.10/site-packages/icecream-2.1.3-py3.10.egg-info/requires.txt': {
                'content': """
asttokens>=2.0.1
colorama>=0.3.9
executing>=0.3.1
pygments>=2.2.0
""",
                'create_dirs': True
            },
        },
        header={
            'requires': [
                'python3-asttokens >= 2.0.1',
                'python3-colorama >= 0.3.9',
                'python3-executing >= 0.3.1',
                'python3-poetry',
                'python3-pygments >= 2.2.0',
            ],
        },
    ),
    get_tested_mock_package(
        files={
            '/usr/lib/python3.10/site-packages/flit-3.8.0.dist-info/METADATA': {
                'content-path': 'files/python-flit-metadata.txt',
                'create_dirs': True
            },
        },
        header={
            'requires': [
                'python3-docutils',
                'python3-flit-core',
                'python3-poetry',
                'python3-requests',
                'python3-tomli-w',
            ],
        },
    ),
])
def test_python_dependencies_leftover(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-leftover-require' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files=[
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/base.cpython-310.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/base.cpython-39.opt-1.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/base.cpython-39.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/__init__.cpython-310.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/__init__.cpython-39.opt-1.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/__init__.cpython-39.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/_saferef.cpython-310.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/_saferef.cpython-39.opt-1.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/_saferef.cpython-39.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/_utilities.cpython-310.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/_utilities.cpython-39.opt-1.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/_utilities.cpython-39.pyc',
    ]
)])
def test_python_pyc_multiple_versions(package, test, output):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: python-pyc-multiple-versions expected: 310' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
    files=[
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/base.cpython-39.opt-1.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/base.cpython-39.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/__init__.cpython-39.opt-1.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/__init__.cpython-39.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/_saferef.cpython-39.opt-1.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/_saferef.cpython-39.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/_utilities.cpython-39.opt-1.pyc',
        '/usr/lib/python3.9/site-packages/blinker/__pycache__/_utilities.cpython-39.pyc',
    ]
)])
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
