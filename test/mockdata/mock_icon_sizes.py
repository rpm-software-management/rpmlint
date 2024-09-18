from Testing import get_tested_mock_package

ICONSIZES = get_tested_mock_package(
    files={
        '/usr/share/tasque/icons/hicolor/16x16/status/tasque-note.png': {
            'metadata': {
                'magic': '22 x 22'
            }
        }
    }
)
