import subprocess
from xml.etree import ElementTree

from rpmlint.checks.AbstractCheck import AbstractFilesCheck
from rpmlint.helpers import ENGLISH_ENVIROMENT


class AppDataCheck(AbstractFilesCheck):
    """
    check appdata files for format violations
    https://www.freedesktop.org/software/appstream/docs/
    """
    # default command, split here so we can mock it later
    cmd = 'appstream-util validate-relax --nonet '

    def __init__(self, config, output):
        super().__init__(config, output, r'/usr/share/appdata/.*\.(appdata|metainfo).xml$')

    def check_file(self, pkg, filename):
        root = pkg.dirName()
        f = root + filename
        cmd = self.cmd + f

        validation_failed = False
        try:
            r = subprocess.run(cmd.split(), env=ENGLISH_ENVIROMENT)
            if r.returncode != 0:
                validation_failed = True
        except FileNotFoundError:
            # appstream-util is not installed
            # validate the xml format only
            try:
                ElementTree.parse(f)
            except ElementTree.ParseError:
                validation_failed = True
        if validation_failed:
            self.output.add_info('E', pkg, 'invalid-appdata-file', filename)
