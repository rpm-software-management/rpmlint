import re

from rpmlint.checks.AbstractCheck import AbstractCheck
from rpmlint.helpers import print_warning


class SignatureCheck(AbstractCheck):
    """
    Checks for PGP signature in the package.

    It checks if the signature is present, known (imported in RPM DB) and
    valid. It uses 'rpm -Kv' command than returns detailed information about
    the package digests and signature.
    """
    any_sig_regex = re.compile(r'[Ss]ignature, key ID')
    nokey_sig_regex = re.compile(r'[Ss]ignature, key ID ([\w\d]*): NOKEY')
    invalid_sig_regex = re.compile(r'invalid OpenPGP signature')

    def check(self, pkg):
        retcode, output = pkg.checkSignature()

        # Skip all signature checks if checkSignature output is empty
        if output is None:
            print_warning(f'No output from checkSignature() for '
                          f'{pkg.filename}. Skipping signature checks.')
            return

        self._check_no_signature(pkg, retcode, output)
        self._check_unknown_key(pkg, retcode, output)
        self._check_invalid_signature(pkg, retcode, output)

    def _check_no_signature(self, pkg, retcode, output):
        """
        Check if the package contains a signature.

        Print an error if there is no signature present. That means that
        there is no mention about any signature in the 'rpm -Kv' output.
        """
        if retcode == 0 and not SignatureCheck.any_sig_regex.search(output):
            self.output.add_info('E', pkg, 'no-signature')

    def _check_unknown_key(self, pkg, retcode, output):
        """
        Check if the public key is imported in the RPM database.

        Print an error if it's not imported and signature is therefore unknown.
        """
        if retcode == 1:
            nokey = SignatureCheck.nokey_sig_regex.search(output)
            if nokey and not SignatureCheck.invalid_sig_regex.search(output):
                self.output.add_info('E', pkg, 'unknown-key', nokey.group(1))

    def _check_invalid_signature(self, pkg, retcode, output):
        """
        Check if the signature is valid.

        Print an error if the signature is corrupted.
        """
        if retcode == 1 and SignatureCheck.invalid_sig_regex.search(output):
            self.output.add_info('E', pkg, 'invalid-signature')
