from Testing import get_tested_mock_package


BuildrootPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/bin/trace': {'content': '/home/marxin/rpmbuild/BUILDROOT/buildroot-0-0.x86_64'},
    },
)
