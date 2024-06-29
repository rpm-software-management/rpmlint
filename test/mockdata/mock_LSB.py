from Testing import get_tested_mock_package


LSB = get_tested_mock_package(
files={
'/usr/sbin/fping',
'/usr/share/doc/packages/fPing',
'/usr/share/doc/packages/fPing/CHANGELOG.md',
'/usr/share/licenses/fPing',
'/usr/share/licenses/fPing/COPYING',
'/usr/share/man/man8/fping.8.gz',
},
header={
'name': 'fPing@1',
'version': '1.0_beta',
'release': '1.0-beta'
})
