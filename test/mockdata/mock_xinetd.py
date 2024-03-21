from Testing import get_tested_mock_package


RequireXinetd = get_tested_mock_package(
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
            'xinetd'
        ]
    },
)
