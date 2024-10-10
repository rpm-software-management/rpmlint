from Testing import get_tested_mock_package


I18NPackage = get_tested_mock_package(
    lazyload=True,
    files=[
        '/usr/share/locale/zh/LC_MESSAGES/goodvibes.mo',
        '/usr/share/locale/zh_Hant/LC_MESSAGES/goodvibes.mo',
        '/usr/share/locale/es_ES/LC_MESSAGES/goodvibes.mo',
        '/usr/share/locale/zh_TW/LC_MESSAGES/goodvibes.mo',
        '/usr/share/locale/pt_BR/LC_MESSAGES/goodvibes.mo',
    ],
)


InvalidI18NPackage = get_tested_mock_package(
    lazyload=True,
    files=[
        '/usr/share/locale/xx_ES/LC_MESSAGES/goodvibes.mo',
        '/usr/share/locale/es_XX/LC_MESSAGES/goodvibes.mo',
        '/usr/share/locale/xx/LC_MESSAGES/goodvibes.mo',
    ],
)
