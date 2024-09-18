from Testing import get_tested_mock_package

MENUXDG = get_tested_mock_package(
files={
'/usr/share/applications/somefile.desktop': {'content': """
[DEFAULT]
something = true
[else
"""}
})

MENUXDG1 = get_tested_mock_package(
files={
'/usr/share/applications/rpmlint-test.desktop': {'content': """
[Desktop Entry]
Name=rpmlint-test
Exec=rpmlint-test file.file
Icon=chameleon_v_balíku
Type=Application
GenericName=rpmlint testcase
Categories=Game;Amusement;
"""}
})

MENUXDG2 = get_tested_mock_package(
files={
'/usr/share/applications/rpmlint-test.desktop': {'content': """
[Desktop Entry]
[Desktop Entry]
Name=rpmlint-test
Name=name duplicate
Exec=rpmlint-test file.file
Icon=chameleon_v_balíku
Type=Application
GenericName=rpmlint testcase
Categories=Game;Amusement;
"""}
})

MENUXDG3 = get_tested_mock_package(
files={
'/usr/share/applications/rpmlint-test.desktop': {'content': """
Name=rpmlint-test
[Bad Section]
Name[x-test]=xxrpmlint-testxx
Exec=rpmlint-test file.file
Icon=rpmlint-test
Type=Application
GenericName=rpmlint testcase"""}
})

MENUXDG4 = get_tested_mock_package(
files={
'/usr/share/applications/rpmlint-test.desktop': {
    'content-path': 'files/rpmlint-test.desktop',
    'create_dirs': True,
}
})

MENUXDG5 = get_tested_mock_package(
files={
'/usr/bin/rpmlint-test',
'/usr/share/applications',
'/usr/share/applications/rpmlint-test.desktop',
'/usr/share/icons/hicolor',
'/usr/share/icons/hicolor/scalable',
'/usr/share/icons/hicolor/scalable/apps',
'/usr/share/icons/hicolor/scalable/apps/chameleon_v_balíku.png'
})
