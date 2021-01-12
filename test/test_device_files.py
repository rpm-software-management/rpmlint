import pytest
from rpmlint.checks.DeviceFilesCheck import DeviceFilesCheck
from rpmlint.filter import Filter
from rpmlint.pkg import FakePkg

from Testing import CONFIG


@pytest.fixture(scope='function', autouse=True)
def check():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = DeviceFilesCheck(CONFIG, output)
    return output, test


def test_device_files_simple(check):
    output, test = check
    with FakePkg('dummy') as pkg:
        pkg.add_file_with_content('/dev/sdb1', 'some device', rdev=5, mode=25008)
        pkg.add_file_with_content('/dev/mydevice', 'some device', rdev=5, mode=25008)
        test.check(pkg)
    out = output.print_results(output.results)
    assert len(output.results) == 2
    assert 'dummy: E: device-mismatched-attrs /dev/sdb1 expected "mode": crw-rw----, has: brw-rw----' in out
    assert 'dummy: E: device-unauthorized-file /dev/mydevice' in out


def test_device_files_success(check):
    output, test = check
    with FakePkg('dummy') as pkg:
        pkg.add_file_with_content('/var/log/foo.txt', 'some data', rdev=0)
        test.check(pkg)
    assert not output.results
