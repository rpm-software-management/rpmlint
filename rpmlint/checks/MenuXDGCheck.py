
#
# check xdg file format violation
#
# http://standards.freedesktop.org/desktop-entry-spec/desktop-entry-spec-latest.html
#

import codecs
import configparser as cfgparser
from pathlib import Path

from rpmlint.checks.AbstractCheck import AbstractFilesCheck
from rpmlint.pkg import getstatusoutput, is_utf8

STANDARD_BIN_DIRS = ('/bin', '/sbin', '/usr/bin', '/usr/sbin')


class MenuXDGCheck(AbstractFilesCheck):
    def __init__(self, config, output):
        # desktop file need to be in $XDG_DATA_DIRS
        # $ echo $XDG_DATA_DIRS/applications
        # /var/lib/menu-xdg:/usr/share
        super().__init__(config, output, r'(?:/usr|/etc/opt|/opt/.*)/share/applications/.*\.desktop$')

    def parse_desktop_file(self, pkg, root, f, filename):
        cfp = cfgparser.RawConfigParser()
        try:
            with codecs.open(f, encoding='utf-8') as inputf:
                cfp.read_file(inputf, filename)
        except cfgparser.DuplicateSectionError as e:
            self.output.add_info('E',
                                 pkg, 'desktopfile-duplicate-section', filename,
                                 '[%s]' % e.section)
        except cfgparser.MissingSectionHeaderError:
            self.output.add_info('E', pkg, 'desktopfile-missing-header', filename)
        except cfgparser.Error as e:
            # Only in Python >= 3.2
            if (hasattr(cfgparser, 'DuplicateOptionError') and
                    isinstance(e, cfgparser.DuplicateOptionError)):
                self.output.add_info('E', pkg, 'desktopfile-duplicate-option', filename,
                                     '[%s]/%s' % (e.section, e.option))
            else:
                self.output.add_info('W', pkg, 'invalid-desktopfile', filename,
                                     e.message.partition(':')[0])
        except UnicodeDecodeError as e:
            self.output.add_info('W', pkg, 'invalid-desktopfile', filename, 'Unicode error: %s' % (e))
        else:
            binary = None
            if cfp.has_option('Desktop Entry', 'Exec'):
                binary = cfp.get('Desktop Entry', 'Exec').partition(' ')[0]
            if binary:
                found = False
                if binary.startswith('/'):
                    found = Path(root + binary).exists()
                else:
                    for i in STANDARD_BIN_DIRS:
                        if Path(root + i + '/' + binary).exists():
                            # no need to check if the binary is +x, rpmlint does it
                            # in another place
                            found = True
                            break
                if not found:
                    self.output.add_info('W', pkg, 'desktopfile-without-binary', filename, binary)

    def check_file(self, pkg, filename):
        root = pkg.dirName()
        f = root + filename
        st = getstatusoutput(('desktop-file-validate', f), True)
        if st[0]:
            error_printed = False
            for line in st[1].splitlines():
                if 'error: ' in line:
                    self.output.add_info('E', pkg, 'invalid-desktopfile', filename,
                                         line.split('error: ')[1])
                    error_printed = True
            if not error_printed:
                self.output.add_info('E', pkg, 'invalid-desktopfile', filename)
        if not is_utf8(f):
            self.output.add_info('E', pkg, 'non-utf8-desktopfile', filename)

        self.parse_desktop_file(pkg, root, f, filename)
