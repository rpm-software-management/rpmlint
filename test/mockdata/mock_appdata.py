from Testing import get_tested_mock_package

APPDATA = get_tested_mock_package(
files={
'/usr/share/appdata/broken.appdata.xml': {'content_path': '/usr/share/appdata/broken.appdata.xml'},
'/usr/share/appdata/terminator.appdata.xml': {'content_path': '/usr/share/appdata/terminator.appdata.xml'}
}
)

APPDATA2 = get_tested_mock_package(
files={
'/usr/share/appdata/terminator.appdata.xml': {'content_path': '/usr/share/appdata/terminator.appdata.xml'}
}
)
