import re

from rpmlint.checks.AbstractCheck import AbstractCheck


class SourceCheck(AbstractCheck):
    """
    Validate files in a source package.
    """
    source_regex = re.compile(r'\.(tar|tgz)$')
    compressed_fileext_magic = {
        'xz': 'XZ compressed',
        'gz': 'gzip compressed',
        'tgz': 'gzip compressed',
        'bz2': 'bzip2 compressed',
        'zst': 'ZSTD compressed',
    }

    def __init__(self, config, output):
        super().__init__(config, output)
        self.compress_ext = config.configuration['CompressExtension']
        self.valid_src_perms = [int(value, 8) for value in config.configuration['ValidSrcPerms']]
        self.spec_file = None

        source_details_dict = {
            'source-not-compressed':
            """A source archive or file in your package is not compressed using the %s
            compression method (doesn't have the %s extension).""" %
            (self.compress_ext, self.compress_ext),
        }
        self.output.error_details.update(source_details_dict)

    def check_source(self, pkg):
        # process file list
        for fname, pkgfile in pkg.files.items():

            self._check_file_ext(fname, pkgfile, pkg)
            self._check_permissions(fname, pkgfile, pkg)
            self._check_compressed_source(fname, pkg)
            self._check_multiple_specfiles(fname, pkg)

    def _check_file_ext(self, fname, pkgfile, pkg):
        """
        Check if the filename extension is the same as what file(1) says.
        """
        file_ext = fname.rpartition('.')[2]

        if (file_ext in self.compressed_fileext_magic and
            pkgfile.magic and
                self.compressed_fileext_magic[file_ext] not in pkgfile.magic):
            self.output.add_info('W', pkg, 'inconsistent-file-extension', fname)

    def _check_permissions(self, fname, pkgfile, pkg):
        """
        Check if the file permissions are valid according to 'ValidSrcPerms' configuration option.
        """
        perm = pkgfile.mode & 0o7777
        if perm not in self.valid_src_perms:
            self.output.add_info('W', pkg, 'strange-permission', fname, '%o' % perm)

    def _check_compressed_source(self, fname, pkg):
        """
        Check if the Source is compressed if CompressExtension configuration options is used (gz, tgz, bz2, xz or zst).
        """
        if (self.source_regex.search(fname) and self.compress_ext and
                not fname.endswith(self.compress_ext)):
            self.output.add_info('W', pkg, 'source-not-compressed',
                                 self.compress_ext, fname)

    def _check_multiple_specfiles(self, fname, pkg):
        """
        Check if the source package contains multiple spec files.
        """
        if fname.endswith('.spec'):
            if self.spec_file:
                self.output.add_info('E', pkg, 'multiple-specfiles', self.spec_file, fname)
            else:
                self.spec_file = fname
