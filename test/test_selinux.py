import pytest
from rpmlint.checks.SELinuxIndependentModuleCheck import SELinuxIndependentModuleCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def selinuxcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SELinuxIndependentModuleCheck(CONFIG, output)
    yield output, test


@pytest.fixture
def output(selinuxcheck):
    output, _test = selinuxcheck
    yield output


@pytest.fixture
def test(selinuxcheck):
    _output, test = selinuxcheck
    yield test


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        name='flatpak-selinux',
        header={'requires': ['selinux-policy-base >= 20260219-2.2']},
        files=[
            '/usr/share/selinux/devel/include/contrib/flatpak.if',
            '/usr/share/selinux/packages/flatpak.pp.bz2',
        ],
    ),
])
def test_selinux_independent_module(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'selinux-incorrect-if-file-location' in out


@pytest.mark.parametrize('package', [
    get_tested_mock_package(
        name='selinux-policy-devel',
        header={'requires': ['selinux-policy-base >= 20260219-2.2']},
        files=[
            '/usr/share/selinux/devel/include/contrib/flatpak.if',
            '/usr/share/selinux/packages/flatpak.pp.bz2',
        ],
    ),
    get_tested_mock_package(
        name='ok-package',
        header={'requires': ['selinux-policy-base >= 20260219-2.2']},
        files=[
            '/usr/share/selinux/devel/include/distributed/flatpak.if',
            '/usr/share/selinux/devel/include/distributed/testing.if',
            '/usr/share/selinux/devel/include/distributed/subfolder/testing.if',
        ],
    ),
])
def test_selinux_no_independent_module(package, output, test):
    test.check(package)
    out = output.print_results(output.results)
    assert 'selinux-incorrect-if-file-location' not in out
