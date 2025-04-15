from Testing import get_tested_mock_package


NoFHSPackage = get_tested_mock_package(
    lazyload=True,
    files=['/usr/dummy', '/var/dummy', '/var/local'],
)
