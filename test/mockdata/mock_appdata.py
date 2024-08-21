from Testing import get_tested_mock_package

APPDATA = get_tested_mock_package(
files={
'/usr/share/appdata/broken.appdata.xml': {
    'content-path': 'files/broken.appdata.xml',
    'create_dirs': True},
'/usr/share/appdata/broken-xml.metainfo.xml': {
    'content-path': 'files/broken-xml.metainfo.xml',
    'create_dirs': True}
})

APPDATA2 = get_tested_mock_package(
files={
'/usr/share/appdata/broken-xml.metainfo.xml': {
    'content-path': 'files/broken-xml.metainfo.xml',
    'create_dirs': True}
})
