import subprocess

from rpmlint.helpers import ENGLISH_ENVIROMENT


class ArParser:
    """
    Class contains all information obtained by ar command.
    """

    def __init__(self, pkgfile_path):
        self.pkgfile_path = pkgfile_path
        self.objects = []
        self.parsing_failed_reason = None
        self.parse()

    def parse(self):
        r = subprocess.run(['ar', 't', self.pkgfile_path], encoding='utf8',
                           stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENGLISH_ENVIROMENT)
        if r.returncode != 0:
            self.parsing_failed_reason = r.stderr
            return

        self.objects = r.stdout.splitlines()
