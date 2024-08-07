from Testing import get_tested_mock_package

ERLANG = get_tested_mock_package(
    files={
        '/usr/lib/erlang/m-no-CInf.beam': {
            'content-path': 'files/m-no-CInf.beam',
            'create_dirs': True,
        },
        '/usr/lib/erlang/m.beam': {
            'content-path': 'files/m.beam',
            'create_dirs': True,
        },
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1'],
    },
)
