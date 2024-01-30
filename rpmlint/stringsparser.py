import subprocess

from rpmlint.helpers import ENGLISH_ENVIRONMENT


class StringsParser:
    """
    Class contains all information obtained by strings command.
    """

    def __init__(self, pkgfile_path):
        self.pkgfile_path = pkgfile_path
        self.strings = []
        self.parsing_failed_reason = None
        self.parse()

    def parse(self):
        r = subprocess.run(['strings', self.pkgfile_path], encoding='utf8',
                           capture_output=True, env=ENGLISH_ENVIRONMENT)
        if r.returncode != 0:
            self.parsing_failed_reason = r.stderr
            return

        self.strings = r.stdout.splitlines()
