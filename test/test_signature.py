import pytest
from rpmlint.checks.SignatureCheck import SignatureCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def signaturecheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SignatureCheck(CONFIG, output)
    return output, test


# The signature was stripped via "rpmsign --delsign <package>"
@pytest.mark.parametrize('package', ['binary/no-signature'])
def test_no_signature(tmpdir, package, signaturecheck):
    output, test = signaturecheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: no-signature' in out
    assert 'E: unknown-key' not in out
    assert 'E: invalid-signature' not in out


# The test rpm was signed with gpg key created for this purpose that is not
# imported in rpm db and therefore unknown-key error should be thrown
@pytest.mark.parametrize('package', ['binary/unknown-key'])
def test_unknown_key(tmpdir, package, signaturecheck):
    output, test = signaturecheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: unknown-key 31fdc502' in out
    assert 'E: no-signature' not in out
    assert 'E: invalid-signature' not in out


# The test rpm hello-2.0-1.x86_64-signed.rpm was taken from
# https://github.com/rpm-software-management/rpm/blob/master/tests/data/RPMS/
# and then the signature was corrupted by running "dd if=/dev/zero
# of=hello-2.0-1.x86_64-signed.rpm conv=notrunc bs=1 seek=264 count=6
# 2> /dev/null"
@pytest.mark.parametrize('package', ['binary/hello'])
def test_invalid_signature(tmpdir, package, signaturecheck):
    output, test = signaturecheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'E: invalid-signature' in out
    assert 'E: no-signature' not in out
    assert 'E: unknown-key' not in out
