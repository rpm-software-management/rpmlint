import subprocess


class StringsParser:
    """
    Class contains all information obtained by strings command.
    """

    def __init__(self, pkgfile_path):
        self.pkgfile_path = pkgfile_path
        self.strings = []
        self.parsing_failed = False
        self.parse()

    def parse(self):
        r = subprocess.run(['strings', self.pkgfile_path], encoding='utf8',
                           stdout=subprocess.PIPE, stderr=subprocess.DEVNULL)
        if r.returncode != 0:
            self.parsing_failed = True
            return

        self.strings = r.stdout.splitlines()
