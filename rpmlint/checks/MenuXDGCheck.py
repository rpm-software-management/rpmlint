
#
# check xdg file format violation
#
# http://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html
#

import codecs
import configparser as cfgparser
from pathlib import Path
import subprocess

from rpmlint.checks.AbstractCheck import AbstractFilesCheck
from rpmlint.helpers import ENGLISH_ENVIROMENT

STANDARD_BIN_DIRS = ('/bin', '/sbin', '/usr/bin', '/usr/sbin')


class MenuXDGCheck(AbstractFilesCheck):
    """
    Check whether MenuXDG files installed by a package are valid.
    """
    def __init__(self, config, output):
        # desktop file need to be in $XDG_DATA_DIRS
        # $ echo $XDG_DATA_DIRS/applications
        # /var/lib/menu-xdg:/usr/share
        super().__init__(config, output, r'/usr/share/applications/.*\.desktop$')

    def parse_desktop_file(self, pkg, root, f, filename):
        """
        Check the structure of a desktop file.
        """
        cfp = cfgparser.RawConfigParser()
        try:
            with codecs.open(f, encoding='utf-8') as inputf:
                cfp.read_file(inputf, filename)
        except cfgparser.Error as e:
            self._handle_parser_error(pkg, filename, e)
        except UnicodeDecodeError as e:
            self.output.add_info('E', pkg, 'non-utf8-desktopfile', filename, f'Unicode error: {e}')
        else:
            self._has_binary(pkg, root, cfp, filename)

    def check_file(self, pkg, filename):
        root = pkg.dirName()
        f = root + filename
        try:
            command = subprocess.run(('desktop-file-validate', f), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, env=ENGLISH_ENVIROMENT)
            text = command.stdout.decode()
            if command.returncode:
                error_printed = False
                for line in text.splitlines():
                    if 'error: ' in line:
                        self.output.add_info('E', pkg, 'invalid-desktopfile', filename,
                                             line.split('error: ')[1])
                        error_printed = True
                if not error_printed:
                    self.output.add_info('E', pkg, 'invalid-desktopfile', filename)

            self.parse_desktop_file(pkg, root, f, filename)
        except UnicodeDecodeError as e:
            self.output.add_info('E', pkg, 'non-utf8-desktopfile', filename, f'Unicode error: {e}')

    def _handle_parser_error(self, pkg, filename, e):
        """
        Determine what to do with a caught configparser error.
        """
        # I would love to use switch, however, each warning is printed differently
        if (isinstance(e, cfgparser.MissingSectionHeaderError)):
            self.output.add_info('E', pkg, 'desktopfile-missing-header', filename)
        elif (isinstance(e, cfgparser.DuplicateSectionError)):
            self.output.add_info('E', pkg, 'desktopfile-duplicate-section', filename,
                                 '[{e.section}]')
        elif (isinstance(e, cfgparser.DuplicateOptionError)):
            self.output.add_info('E', pkg, 'desktopfile-duplicate-option', filename,
                                 '[{e.section}]/{e.option}')
        else:
            self.output.add_info('E', pkg, 'invalid-desktopfile', filename,
                                 e.message.partition(':')[0])

    def _has_binary(self, pkg, root, cfp, filename):
        """
        Check whether there is a binary assigned to the desktop file.

        Needs configparser instance, it is assumed to be called in parse_desktop_file.
        """
        binary = None
        if cfp.has_option('Desktop Entry', 'Exec'):
            binary = cfp.get('Desktop Entry', 'Exec').partition(' ')[0]
        # If there is no binary mentioned it is OK
        if not binary:
            return
        if binary.startswith('/'):
            if (Path(root + binary).exists()):
                return
        else:
            for i in STANDARD_BIN_DIRS:
                if Path(root + i + '/' + binary).exists():
                    # no need to check if the binary is +x, rpmlint does it
                    # in another place
                    return
        self.output.add_info('W', pkg, 'desktopfile-without-binary', filename, binary)
