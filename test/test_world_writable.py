import pytest
from rpmlint.checks.WorldWritableCheck import WorldWritableCheck
from rpmlint.filter import Filter
from rpmlint.pkg import FakePkg

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def check():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = WorldWritableCheck(CONFIG, output)
    return output, test


def test_device_files_simple(check):
    output, test = check
    with FakePkg('dummy') as pkg:
        pkg.add_file_with_content('/tmp', 'temp folder', rdev=0, mode=0o41777)
        pkg.add_file_with_content('/tempus', 'tempus', rdev=0, mode=0o41777)
        test.check(pkg)
    out = output.print_results(output.results)
    assert len(output.results) == 2
    assert 'dummy: E: world-writable-mismatched-attrs /tempus expected "mode": drw-rw---t, has: drwxr-xr-t'
    assert 'dummy: E: world-writable-unauthorized-file /tmp' in out
