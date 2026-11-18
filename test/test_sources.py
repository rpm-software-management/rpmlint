import io
import tarfile
import zipfile

import pytest
import zstandard
from rpmlint.checks.SourceCheck import SourceCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def sourcescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = SourceCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', ['source/wrongsrc'])
def test_extension_and_permissions(tmp_path, package, sourcescheck):
    output, test = sourcescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)

    assert len(output.results) == 1

    assert 'inconsistent-file-extension' in out
    assert 'name extension indicates a different compression format' in out

    assert 'strange-permission' not in out
    assert 'a file should have' not in out


@pytest.mark.parametrize('package', ['source/not-compressed-multi-spec'])
def test_compression_and_multispec(tmp_path, package, sourcescheck):
    output, test = sourcescheck
    test.check(get_tested_package(package, tmp_path))
    out = output.print_results(output.results)

    assert 'source-not-compressed' in out
    assert 'source archive or file in your package is not compressed' in out

    assert 'multiple-specfiles' in out
    assert 'package contains multiple spec files' in out


# ── Tests for _check_file_ext (compressed_fileext_magic matching) ──
#
# Test data: test/files/magic/ contains small compressed files, each holding
# a single byte 'x'.  Created with standard CLI tools:
#
#   echo -n x | gzip -n  > byte.gz     # -n omits filename/timestamp
#   echo -n x | bzip2    > byte.bz2
#   echo -n x | xz       > byte.xz
#   echo -n x | zstd -q  > byte.zst
#   echo -n x > 0                      # zip needs a file on disk
#   touch -t 200001010000.00 0         # fixed timestamp for reproducibility
#   TZ=UTC zip -0 -j byte.zip 0       # -0 store, -j junk paths
#   rm 0
#
# In Python (bz2 is byte-identical to CLI; others differ in internal
# flags but are functionally equivalent):
#   gzip.compress(b'x', mtime=0)
#   bz2.compress(b'x')
#   lzma.compress(b'x', format=lzma.FORMAT_XZ)
#   zstandard.ZstdCompressor().compress(b'x')


@pytest.mark.parametrize('ext, content_file', [
    ('gz', 'files/magic/byte.gz'),
    ('tgz', 'files/magic/byte.gz'),   # tgz is gzip too
    ('bz2', 'files/magic/byte.bz2'),
    ('xz', 'files/magic/byte.xz'),
    ('zst', 'files/magic/byte.zst'),
    ('zstd', 'files/magic/byte.zst'),  # .zstd is the same format
    ('zip', 'files/magic/byte.zip'),
])
def test_file_ext_consistent(sourcescheck, ext, content_file):
    """Extension matches actual compression format → no warning."""
    output, test = sourcescheck
    pkg = get_tested_mock_package(
        files={f'archive.{ext}': {'content-path': content_file}},
    )
    test.check_source(pkg)
    out = output.print_results(output.results)
    assert 'inconsistent-file-extension' not in out


@pytest.mark.parametrize('ext, content_file', [
    ('gz', 'files/magic/byte.bz2'),
    ('bz2', 'files/magic/byte.gz'),
    ('xz', 'files/magic/byte.zst'),
    ('zst', 'files/magic/byte.gz'),
    ('zstd', 'files/magic/byte.xz'),
    ('zip', 'files/magic/byte.gz'),
])
def test_file_ext_inconsistent(sourcescheck, ext, content_file):
    """Extension does NOT match actual compression format → warning."""
    output, test = sourcescheck
    pkg = get_tested_mock_package(
        files={f'archive.{ext}': {'content-path': content_file}},
    )
    test.check_source(pkg)
    out = output.print_results(output.results)
    assert 'inconsistent-file-extension' in out


@pytest.mark.parametrize('fname', [
    'archive.gz',
    'archive.tar',
    'archive.txt',
])
def test_file_ext_no_magic(sourcescheck, fname):
    """File with no magic string (empty content) → no crash, no warning."""
    output, test = sourcescheck
    pkg = get_tested_mock_package(
        files={fname: {'metadata': {'magic': None}}},
    )
    test.check_source(pkg)
    out = output.print_results(output.results)
    assert 'inconsistent-file-extension' not in out


def test_file_ext_unknown_extension(sourcescheck):
    """Extension not in compressed_fileext_magic → no warning."""
    output, test = sourcescheck
    pkg = get_tested_mock_package(
        files={'archive.lz4': {'content-path': 'files/magic/byte.gz'}},
    )
    test.check_source(pkg)
    out = output.print_results(output.results)
    assert 'inconsistent-file-extension' not in out


def make_tar(files, mode='w:gz'):
    archive = io.BytesIO()
    with tarfile.open(fileobj=archive, mode=mode) as tar:
        for name, content in files.items():
            info = tarfile.TarInfo(name)
            info.size = len(content)
            tar.addfile(info, io.BytesIO(content))
    return archive.getvalue()


def make_zip(files):
    archive = io.BytesIO()
    with zipfile.ZipFile(archive, mode='w') as zipped:
        for name, content in files.items():
            zipped.writestr(name, content)
    return archive.getvalue()


@pytest.mark.parametrize('archive_name, binary_name', [
    pytest.param('sources.tar.gz', 'vendor/prebuilt.o', id='tar-gzip'),
    pytest.param('sources.tar.zst', 'vendor/prebuilt.class', id='tar-zstd'),
    pytest.param('sources.zip', 'vendor/prebuilt.wasm', id='zip'),
])
def test_source_binary_archive(sourcescheck, archive_name, binary_name):
    output, test = sourcescheck
    test.check_source_binaries = True
    files = {
        'src/main.c': b'int main(void) { return 0; }',
        binary_name: b'not really a binary',
    }
    if archive_name.endswith('.tar.gz'):
        content = make_tar(files)
    elif archive_name.endswith('.tar.zst'):
        content = zstandard.ZstdCompressor().compress(make_tar(files, mode='w'))
    else:
        content = make_zip(files)
    pkg = get_tested_mock_package(files={archive_name: {'content': content}})

    test.check_source(pkg)
    out = output.print_results(output.results)

    assert f'W: source-contains-prebuilt-binary {archive_name}:vendor/prebuilt.' in out
    assert 'src/main.c' not in out


def test_source_binary_check_is_disabled_by_default(sourcescheck):
    output, test = sourcescheck
    pkg = get_tested_mock_package(files={
        'sources.tar.gz': {'content': make_tar({'prebuilt.so': b'not really a library'})},
    })

    test.check_source(pkg)

    assert 'source-contains-prebuilt-binary' not in output.print_results(output.results)


def test_direct_binary_source(sourcescheck):
    output, test = sourcescheck
    test.check_source_binaries = True
    pkg = get_tested_mock_package(files={'prebuilt.jar': {'content': b'not really a jar'}})

    test.check_source(pkg)
    out = output.print_results(output.results)

    assert 'W: source-contains-prebuilt-binary prebuilt.jar' in out


def test_binary_magic_does_not_confuse_tar_with_ar():
    assert SourceCheck._is_binary('sources.tar', 'POSIX tar archive') is False
    assert SourceCheck._is_binary('library', 'current ar archive') is True


def test_embedded_wasm_in_source_archive(sourcescheck):
    output, test = sourcescheck
    test.check_source_binaries = True
    content = make_tar({'loader.js': b'const wasm = "AGFzbQEAAAA";'})
    pkg = get_tested_mock_package(files={'sources.tar.gz': {'content': content}})

    test.check_source(pkg)
    out = output.print_results(output.results)

    assert 'W: source-contains-prebuilt-binary sources.tar.gz:loader.js' in out


def test_embedded_wasm_in_standalone_source(sourcescheck):
    output, test = sourcescheck
    test.check_source_binaries = True
    pkg = get_tested_mock_package(files={
        'loader.js': {'content': b'const wasm = "AGFzbQEAAAA";'},
    })

    test.check_source(pkg)
    out = output.print_results(output.results)

    assert 'W: source-contains-prebuilt-binary loader.js' in out
