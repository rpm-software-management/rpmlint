import os

from rpmlint.AbstractCheck import AbstractCheck


class RpmFileCheck(AbstractCheck):
    def __init__(self, config, output):
        AbstractCheck.__init__(self, config, output, "RpmFileCheck")
        rpmfile_details_dict = {
            'filename-too-long-for-joliet':
            '''This filename is too long to fit on a joliet filesystem (limit is 64 unicode
        chars).''',
        }
        self.output.error_details.update(rpmfile_details_dict)

    def check(self, pkg):
        # http://en.wikipedia.org/wiki/Joliet_(file_system)
        rpmfile_name = os.path.basename(pkg.filename)
        if len(rpmfile_name) > 64:
            self.output.add_info('W', pkg, 'filename-too-long-for-joliet', rpmfile_name)
