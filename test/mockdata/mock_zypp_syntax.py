from Testing import get_tested_mock_package

ZYPPSYNTAX = get_tested_mock_package(
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
            'rpmlib(RichDependencies) <= 4.12.0-1',
        ],
        'supplements': ['packageand(c:d)'],
        'recommends': ['packageand(a:b)'],
        'suggests': ['(a and b)'],
        'conflicts': [
            'bee',
            'otherproviders(yast2_theme)',
        ],
    },
)

ZYPPSYNTAX2 = get_tested_mock_package(
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
            'rpmlib(RichDependencies) <= 4.12.0-1',
        ],
        'supplements': ['(c and d)'],
        'recommends': ['b'],
        'suggests': ['(a and b)'],
        'conflicts': [
            'bee',
        ],
    },
)
