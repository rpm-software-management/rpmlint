import pytest
from rpmlint.checks.FileDigestCheck import FileDigestCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def digestcheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = FileDigestCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['binary/file-signature-good'])
def test_signatures(tmpdir, package, digestcheck):
    output, test = digestcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert not out


@pytest.mark.parametrize('package', ['binary/file-signature-symlinks'])
def test_signatures_symlinks(tmpdir, package, digestcheck):
    output, test = digestcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert len(output.results) == 2
    assert 'file-signature-symlinks.x86_64: E: cron-file-symlink /etc/cron.daily/symlink' in out
    assert 'file-signature-symlinks.x86_64: E: cron-file-digest-ghost /etc/cron.daily/test-me-ghost' in out


@pytest.mark.parametrize('package', ['binary/file-signature-bad'])
def test_signatures_bad(tmpdir, package, digestcheck):
    output, test = digestcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert len(output.results) == 1
    assert 'file-signature-bad.x86_64: E: cron-file-digest-mismatch /etc/cron.daily/suse.de-sarg expected sha256:edeaaff3f1774ad2888673770c6d64097e391bc362d7d6fb34982ddf0efd18cb, has:8dbb513cddb18fe825dad6836161e03c109de7736913444dd5ad3de9d5579afe' in out


def test_description_message(tmpdir, digestcheck):
    output, test = digestcheck
    assert output.get_description('cron-file-digest-unauthorized') == 'Please refer to\nhttps://en.opensuse.org/openSUSE:Package_security_guidelines#audit_bugs for\nmore information.\n\n'
