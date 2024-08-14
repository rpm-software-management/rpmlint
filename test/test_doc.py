import pytest
from rpmlint.checks.DocCheck import DocCheck
from rpmlint.filter import Filter
from rpm import RPMFILE_DOC

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def doccheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = DocCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [get_tested_mock_package(
name='mydoc',
files={
    '/usr/share/doc/packages/mydoc': {'is_dir': True, 'metadata': {'mode': 0o755, 'size': 0}},
    '/usr/share/doc/packages/mydoc/README': {'metadata': {'mode': 0o755, 'size': 1}},
    '/usr/share/doc/packages/mydoc/doc.html': {'metadata': {'mode': 0o755, 'size': 0}},
    '/usr/share/doc/packages/mydoc/strace.txt': {'metadata': {'mode': 0o644, 'size': 270508}}
},
header={
    'requires': [
        'rpmlib(CompressedFileNames) <= 3.0.4-1',
        'rpmlib(FileDigests) <= 4.6.0-1',
        'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
        'rpmlib(PayloadIsXz) <= 5.2-1',
        'xinetd'
    ]
},
)])
def test_doccheck(package, doccheck):
    output, test = doccheck
    test.check(package)
    out = output.print_results(output.results)
    #assert 'E: executable-docs /usr/share/doc/packages/mydoc/doc.html' in out
    #assert 'E: executable-docs /usr/share/doc/packages/mydoc/README' in out
    #assert 'W: package-with-huge-docs 100%' in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
files={
    '/usr/bin/example': {'metadata': {'mode': 0o755}},
    '/usr/lib/python3.7/site-packages/__pycache__': {'is_dir': True, 'metadata': {'mode': 0o755}},
    '/usr/lib/python3.7/site-packages/__pycache__/example.cpython-37.pyc': {'metadata': {'mode': 0o644}},
    '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info': {'is_dir': True, 'metadata': {'mode': 0o755}},
    '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info/PKG-INFO': {'metadata': {'mode': 0o644}},
    '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info/SOURCES.txt': {'metadata': {'mode': 0o644, 'flags': RPMFILE_DOC}},
    '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info/dependency_links.txt': {'metadata': {'mode': 0o644}},
    '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info/entry_points.txt': {'metadata': {'mode': 0o644}},
    '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info/top_level.txt': {'metadata': {'mode': 0o644}},
    '/usr/lib/python3.7/site-packages/example.py': {'metadata': {'mode': 0o644}}
},
header={
    'requires': [
        '/usr/bin/python3',
        'python(abi) = 3.7',
        'rpmlib(CompressedFileNames) <= 3.0.4-1',
        'rpmlib(FileDigests) <= 4.6.0-1',
        'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
        'rpmlib(PayloadIsXz) <= 5.2-1',
        'some-dependency-not-in-core_reqs'
    ]
}
)])
def test_doc_file_dep(package, doccheck):
    output, test = doccheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: doc-file-dependency' in out
    assert 'W: install-file-in-docs' not in out


@pytest.mark.parametrize('package', [get_tested_mock_package(
files={
'/usr/share/doc/packages/install-file-in-docs': {'is_dir': True, 'metadata': {'mode': 0o755, 'size': 0}},
#'/usr/share/doc/packages/install-file-in-docs/INSTALL': {'metadata': {'mode': 0o644, 'flags': RPMFILE_DOC, 'size': 21}}
},
header={
'requires': [
    'rpmlib(CompressedFileNames) <= 3.0.4-1',
    'rpmlib(FileDigests) <= 4.6.0-1',
    'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
    'rpmlib(PayloadIsXz) <= 5.2-1'
]}
)])
def test_install_file_in_docs(package, doccheck):
    output, test = doccheck
    test.check(package)
    out = output.print_results(output.results)
    #assert 'W: install-file-in-docs' in out
    #assert 'E: executable-docs' not in out
    #assert 'W: package-with-huge-docs 100%' not in out
    #assert 'W: doc-file-dependency' not in out
