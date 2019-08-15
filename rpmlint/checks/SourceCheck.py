#############################################################################
# File          : SourceCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Wed Oct 27 21:17:03 1999
# Purpose       : verify source package correctness.
#############################################################################

import re

from rpmlint.checks.AbstractCheck import AbstractCheck


class SourceCheck(AbstractCheck):
    source_regex = re.compile(r'\\.(tar|patch|tgz|diff)$')
    compressed_fileext_magic = {
        'xz': 'XZ compressed',
        'gz': 'gzip compressed',
        'tgz': 'gzip compressed',
        'bz2': 'bzip2 compressed',
    }

    def __init__(self, config, output):
        super().__init__(config, output)
        self.compress_ext = config.configuration['CompressExtension']
        self.valid_src_perms = config.configuration['ValidSrcPerms']

        source_details_dict = {
            'source-or-patch-not-compressed':
            """A source archive or file in your package is not compressed using the %s
            compression method (doesn't have the %s extension).""" %
            (self.compress_ext, self.compress_ext),
        }
        self.output.error_details.update(source_details_dict)

    def check_source(self, pkg):
        # process file list
        spec_file = None
        for fname, pkgfile in pkg.files().items():
            file_ext = fname.rpartition('.')[2]
            if (file_ext in self.compressed_fileext_magic and
                    pkgfile.magic and
                    self.compressed_fileext_magic[file_ext] not in pkgfile.magic):
                self.output.add_info('W', pkg, 'inconsistent-file-extension', fname)

            if fname.endswith('.spec'):
                if spec_file:
                    self.output.add_info('E', pkg, 'multiple-specfiles', spec_file, fname)
                else:
                    spec_file = fname
            elif self.source_regex.search(fname) and self.compress_ext and \
                    not fname.endswith(self.compress_ext):
                self.output.add_info('W', pkg, 'source-or-patch-not-compressed',
                                     self.compress_ext, fname)
            perm = pkgfile.mode & 0o7777
            if perm not in self.valid_src_perms:
                self.output.add_info('W', pkg, 'strange-permission', fname, '%o' % perm)
