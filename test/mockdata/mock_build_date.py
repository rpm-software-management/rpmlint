from Testing import get_tested_mock_package

BUILDDATE = get_tested_mock_package(
    files={
        '/bin/with-date': {'content': """Jan  1 2019"""},
        '/bin/with-datetime': {'content': """Jan  1 2019 12:15:11"""}
    }
)

BUILDDATE2 = get_tested_mock_package(
    files={
        '/bin/script1',
        '/bin/script2'
    }
)
