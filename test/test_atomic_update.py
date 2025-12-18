import pytest
import rpm
from rpmlint.checks.AtomicUpdateCheck import AtomicUpdateCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def atomiccheck():
    CONFIG.info = True
    CONFIG.configuration['AtomicCheckGhosts'] = True
    output = Filter(CONFIG)
    test = AtomicUpdateCheck(CONFIG, output)
    yield output, test


@pytest.fixture
def output(atomiccheck):
    output, _test = atomiccheck
    yield output


@pytest.fixture
def test(atomiccheck):
    _output, test = atomiccheck
    yield test


@pytest.mark.parametrize('package', [
    get_tested_mock_package(files=('/var/lib/pipewire',)),
    get_tested_mock_package(files=('/opt/bin/test',)),
    get_tested_mock_package(files=('/usr/local/bin/test',)),
    get_tested_mock_package(files=('/boot/efi/test',)),
])
def test_not_atomic(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: dir-or-file-outside-snapshot' in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(files=('/etc/custom.config',)),
    get_tested_mock_package(files=('/usr/lib64/libc.so',)),
    get_tested_mock_package(files=('/usr/etc/nfs.conf',)),
    get_tested_mock_package(files=('/bin/test',)),
    get_tested_mock_package(files=('/sbin/test',)),
    get_tested_mock_package(files=('/lib/libc.so',)),
    get_tested_mock_package(files=('/lib64/libc.so',)),
    get_tested_mock_package(files=('/boot/grub2/grub.cfg',)),
])
def test_atomic(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: dir-or-file-outside-snapshot' not in out
    assert 'W: ghost-outside-snapshot' not in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(files={
        '/var/lib/pipewire/ghost_file': {'metadata': {'flags': rpm.RPMFILE_GHOST}},
    }),
])
def test_not_atomic_ghost(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: ghost-outside-snapshot' in out
