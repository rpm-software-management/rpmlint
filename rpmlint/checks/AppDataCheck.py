from xml.etree import ElementTree

from rpmlint.checks.AbstractCheck import AbstractFilesCheck
from rpmlint.pkg import getstatusoutput


class AppDataCheck(AbstractFilesCheck):
    """
    check appdata files for format violations
    http://people.freedesktop.org/~hughsient/appdata/
    """
    def __init__(self, config, output):
        # desktop file need to be in $XDG_DATA_DIRS
        # $ echo $XDG_DATA_DIRS/applications
        # /var/lib/menu-xdg:/usr/share
        super().__init__(config, output, r'/usr/share/appdata/.*\.appdata.xml$')
        self.appdata_checker = self.config.configuration['AppDataChecker']
        appdata_details_dict = {
            'invalid-appdata-file':
            'appdata file is not valid, check with {}'.format(' '.join(self.appdata_checker)),
        }
        self.output.error_details.update(appdata_details_dict)

    def check_file(self, pkg, filename):
        root = pkg.dirName()
        f = root + filename

        checker = self.appdata_checker
        if checker[0] == 'appstream-util' and not self.network_enabled:
            checker += ('--nonet',)
        validation_failed = False
        try:
            st = getstatusoutput(checker + (f,))
            # Return code nonzero?
            validation_failed = (st[0] != 0)
        except OSError:
            # checker is not installed, do a validation manually
            try:
                ElementTree.parse(pkg.dirName() + filename)
            except ElementTree.ParseError:
                validation_failed = True
        if validation_failed:
            self.output.add_info('E', pkg, 'invalid-appdata-file', filename)
