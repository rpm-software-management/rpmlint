from pathlib import Path
import re
import tarfile
from zipfile import BadZipFile, is_zipfile, ZipFile

try:
    import magic
except ImportError:
    magic = None
import zstandard

from rpmlint.checks.AbstractCheck import AbstractCheck


class SourceCheck(AbstractCheck):
    """
    Validate files in a source package.
    """
    source_regex = re.compile(r'\.(tar|tgz)$')

    # Regex patterns. Applied to a string from file(1) tool.
    compressed_fileext_magic = {
        'xz': r'XZ compressed',
        'gz': r'gzip compressed',
        'tgz': r'gzip compressed',
        'bz2': r'bzip2 compressed',
        'zst': r'(ZSTD|Zstandard) compressed',
        'zstd': r'(ZSTD|Zstandard) compressed',
        'zip': r'Zip archive data',
    }

    binary_fileext_regex = re.compile(
        r'\.(?:a|bc|class|dex|dll|dylib|ear|exe|gch|jar|ko|lib|node|o|obj|pyc|pyo|so(?:\..*)?|wasm|war)$',
        re.IGNORECASE,
    )
    binary_magic_regex = re.compile(
        r'(?:application/(?:java-archive|java-vm|wasm|vnd\.android\.dex|'
        r'x-(?:archive|bytecode\.python|dosexec|executable|java-archive|llvm|mach-binary|object|pie-executable|sharedlib))'
        r'|ELF|Mach-O|PE32|WebAssembly|Java class data|Dalvik dex file|LLVM IR bitcode|'
        r'GCC precompiled header|(?:^|\s)(?:current )?ar archive|python.*byte-compiled)',
        re.IGNORECASE,
    )
    embedded_wasm_magic = b'AGFzb'
    magic_sample_size = 256 * 1024

    def __init__(self, config, output):
        super().__init__(config, output)
        self.compress_ext = config.configuration['CompressExtension']
        self.valid_src_perms = [int(value, 8) for value in config.configuration['ValidSrcPerms']]
        self.check_source_binaries = config.configuration['CheckSourceBinaries']
        self.spec_file = None

        source_details_dict = {
            'source-not-compressed':
            """A source archive or file in your package is not compressed using the %s
            compression method (doesn't have the %s extension).""" %
            (self.compress_ext, self.compress_ext),
        }
        self.output.error_details.update(source_details_dict)

    def reset(self):
        self.spec_file = None

    def check_source(self, pkg):
        # process file list
        for fname, pkgfile in pkg.files.items():
            self._check_file_ext(fname, pkgfile, pkg)
            self._check_permissions(fname, pkgfile, pkg)
            self._check_compressed_source(fname, pkg)
            self._check_multiple_specfiles(fname, pkg)
            if self.check_source_binaries:
                self._check_source_binaries(fname, pkgfile, pkg)

    def _check_file_ext(self, fname, pkgfile, pkg):
        """
        Check if the filename extension is the same as what file(1) says.
        """
        if not pkgfile.magic:
            return
        file_ext = fname.rpartition('.')[2]
        pattern = self.compressed_fileext_magic.get(file_ext)
        if pattern is None:
            return  # file(1) pattern is unknown for given file extension
        if re.match(pattern, pkgfile.magic, re.IGNORECASE):
            return
        self.output.add_info('W', pkg, 'inconsistent-file-extension',
                             f'file {fname!r} magic {pkgfile.magic!r} does not match {pattern!r}')

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

    @classmethod
    def _magic_from_buffer(cls, data):
        """Return a libmagic description for bytes with either supported binding."""
        if not magic or not data:
            return ''
        try:
            if hasattr(magic, 'from_buffer'):
                return magic.from_buffer(data)
            if hasattr(magic, 'detect_from_content'):
                return magic.detect_from_content(data).name
        except (ValueError, TypeError):
            pass
        return ''

    @classmethod
    def _is_binary(cls, name, description, sample=b''):
        return bool(
            cls.binary_fileext_regex.search(name)
            or cls.binary_magic_regex.search(description or '')
            or cls.embedded_wasm_magic in sample
        )

    @classmethod
    def _read_sample(cls, stream):
        return stream.read(cls.magic_sample_size)

    def _report_binary(self, pkg, source, member, description):
        location = f'{source}:{member}' if member else source
        self.output.add_info('W', pkg, 'source-contains-prebuilt-binary', location, description)

    def _check_stream(self, pkg, source, member, stream):
        sample = self._read_sample(stream)
        description = self._magic_from_buffer(sample)
        if self._is_binary(member, description, sample) or self._contains_embedded_wasm(stream, sample):
            self._report_binary(pkg, source, member, description)

    @classmethod
    def _contains_embedded_wasm(cls, stream, initial=b''):
        marker = cls.embedded_wasm_magic
        if marker in initial:
            return True
        previous = initial[-(len(marker) - 1):]
        while chunk := stream.read(cls.magic_sample_size):
            if marker in previous + chunk:
                return True
            previous = chunk[-(len(marker) - 1):]
        return False

    def _check_tar(self, pkg, fname, archive):
        for member in archive:
            if not member.isfile():
                continue
            stream = archive.extractfile(member)
            if stream is None:
                continue
            with stream:
                self._check_stream(pkg, fname, member.name, stream)

    def _check_zip(self, pkg, fname, path):
        try:
            with ZipFile(path) as archive:
                for member in archive.infolist():
                    if member.is_dir():
                        continue
                    try:
                        with archive.open(member) as stream:
                            self._check_stream(pkg, fname, member.filename, stream)
                    except (BadZipFile, RuntimeError):
                        continue
        except (BadZipFile, OSError):
            pass

    def _check_zstd_tar(self, pkg, fname, path):
        try:
            with open(path, 'rb') as source:
                with zstandard.ZstdDecompressor().stream_reader(source) as stream:
                    with tarfile.open(fileobj=stream, mode='r|') as archive:
                        self._check_tar(pkg, fname, archive)
        except (OSError, tarfile.TarError, zstandard.ZstdError):
            pass

    def _check_source_binaries(self, fname, pkgfile, pkg):
        path = Path(pkgfile.path)
        if not path.is_file():
            return

        # Report a source that is itself a binary, such as a JAR or object file.
        if self._is_binary(fname, pkgfile.magic):
            self._report_binary(pkg, fname, None, pkgfile.magic)
            return

        if is_zipfile(path):
            self._check_zip(pkg, fname, path)
            return

        try:
            with tarfile.open(path, mode='r:*') as archive:
                self._check_tar(pkg, fname, archive)
            return
        except (OSError, tarfile.TarError):
            pass

        if fname.lower().endswith(('.tar.zst', '.tar.zstd', '.tzst')):
            self._check_zstd_tar(pkg, fname, path)
            return

        # Standalone text sources can contain an embedded base64 WebAssembly
        # module too. Spec files and patches may merely discuss that marker.
        if not fname.lower().endswith(('.spec', '.patch', '.diff')):
            try:
                with open(path, 'rb') as stream:
                    if self._contains_embedded_wasm(stream):
                        self._report_binary(pkg, fname, None, pkgfile.magic)
            except OSError:
                pass
