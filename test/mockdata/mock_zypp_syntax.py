from Testing import get_tested_mock_package


SyntaxPackageandPackage = get_tested_mock_package(
    lazyload=True,
    header={
        'requires': [],
        'supplements': ['packageand(c:d)'],
        'recommends': ['packageand(a:b)'],
        'suggests': ['(a and b)'],
        'conflicts': [
            'bee',
            'otherproviders(yast2_theme)',
        ],
    },
)


SyntaxAndPackage = get_tested_mock_package(
    lazyload=True,
    header={
        'requires': [],
        'supplements': ['(c and d)'],
        'recommends': ['b'],
        'suggests': ['(a and b)'],
        'conflicts': [
            'bee',
        ],
    },
)
