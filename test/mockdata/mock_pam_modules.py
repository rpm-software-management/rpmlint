from Testing import get_tested_mock_package

PAMMODULES = get_tested_mock_package(
files={
'/usr/lib64/security/pam-module.so': {'content': ''}
}
)
