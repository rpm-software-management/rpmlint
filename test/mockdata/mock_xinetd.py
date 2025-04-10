from Testing import get_tested_mock_package


RequireXinetd = get_tested_mock_package(
    lazyload=True,
    header={
        'requires': [
            'xinetd',
        ],
    },
)
