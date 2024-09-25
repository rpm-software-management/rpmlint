from Testing import get_tested_mock_package


BROKEN = """
[DEFAULT]
something = true
[else
"""

BADBIN = """
[Desktop Entry]
Name=rpmlint-test
Exec=rpmlint-test file.file
Icon=chameleon_v_balíku
Type=Application
GenericName=rpmlint testcase
Categories=Game;Amusement;
"""


BADDUP = """
[Desktop Entry]
[Desktop Entry]
Name=rpmlint-test
Name=name duplicate
Exec=rpmlint-test file.file
Icon=chameleon_v_balíku
Type=Application
GenericName=rpmlint testcase
Categories=Game;Amusement;
"""


BADSEC = """
Name=rpmlint-test
[Bad Section]
Name[x-test]=xxrpmlint-testxx
Exec=rpmlint-test file.file
Icon=rpmlint-test
Type=Application
GenericName=rpmlint testcase
"""


MenuXDGInvalidPackage = get_tested_mock_package(
    lazyload=True,
    files={'/usr/share/applications/somefile.desktop': {'content': BROKEN}},
)


MenuXDGBadBinPackage = get_tested_mock_package(
    lazyload=True,
    files={'/usr/share/applications/rpmlint-test.desktop': {'content': BADBIN}},
)


MenuXDGBadDupPackage = get_tested_mock_package(
    lazyload=True,
    files={'/usr/share/applications/rpmlint-test.desktop': {'content': BADDUP}},
)


MenuXDGBadSecPackage = get_tested_mock_package(
    lazyload=True,
    files={'/usr/share/applications/rpmlint-test.desktop': {'content': BADSEC}},
)


MenuXDGBadUTF8Package = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/share/applications/rpmlint-test.desktop': {
            'content-path': 'files/rpmlint-test.desktop',
            'create_dirs': True,
        },
    },
)

MenuXDGPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/bin/rpmlint-test': {},
        '/usr/share/applications/rpmlint-test.desktop': {
            'content-path': 'files/rpmlint-test-good.desktop',
            'create_dirs': True,
        },
    },
)
