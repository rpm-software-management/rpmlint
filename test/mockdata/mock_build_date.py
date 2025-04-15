from Testing import get_tested_mock_package


BuildDatePackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/bin/with-date': {'content': 'Jan  1 2019'},
        '/bin/with-datetime': {'content': 'Jan  1 2019 12:15:11'},
    },
)
