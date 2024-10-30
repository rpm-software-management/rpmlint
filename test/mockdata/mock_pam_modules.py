from Testing import get_tested_mock_package


PAMModulePackage = get_tested_mock_package(
    lazyload=True,
    files=['/usr/lib64/security/pam-module.so'],
)
