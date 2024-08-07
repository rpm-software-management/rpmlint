import pytest
from rpmlint.checks.IconSizesCheck import IconSizesCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_mock_package


@pytest.fixture(scope='function', autouse=True)
def iconsizescheck():
    CONFIG.info = True
    output = Filter(CONFIG)
    test = IconSizesCheck(CONFIG, output)
    return output, test


@pytest.mark.parametrize('package', [get_tested_mock_package(
files={
    '/usr/bin/tasque': {},
    '/usr/lib/pkgconfig/tasque.pc': {},
    '/usr/lib/tasque': {'is_dir': True},
    '/usr/lib/tasque/Gtk.Tasque.dll': {},
    '/usr/lib/tasque/RtmBackend.dll': {},
    '/usr/lib/tasque/RtmNet.dll': {},
    '/usr/lib/tasque/SqliteBackend.dll': {},
    '/usr/lib/tasque/Tasque.exe': {},
    '/usr/lib/tasque/Tasque.exe.Defines.config': {},
    '/usr.lib/tasque/Tasque.exe.config': {},
    '/usr/lib/tasque/libtasque.dll': {},
    '/usr/share/applications/tasque.desktop': {},
    '/usr/share/dbus-1/services/org.gnome.Tasque.service': {},
    '/usr/share/icons/hicolor/16x16/apps/tasque-panel.png': {
        'magic': '18 x 18'
    },
    '/usr/share/icons/hicolor/16x16/apps/tasque.png': {
        'magic': '18 x 18'
    },
    '/usr/share/icons/hicolor/22x22/apps/tasque-panel.png': {
        'magic': '24 x 24'
    },
    '/usr/share/icons/hicolor/22x22/apps/tasque.png': {
        'magic': '24 x 24'
    },
    '/usr/share/icons/hicolor/24x24/apps/tasque-panel.png': {
        'magic': '26 x 26'
    },
    '/usr/share/icons/hicolor/24x24/apps/tasque.png': {
        'magic': '26 x 26'
    },
    '/usr/share/icons/hicolor/32x32/apps/tasque.png': {
        'magic': '34 x 34'
    },
    '/usr/share/icons/hicolor/48x48/apps/tasque.png': {
        'magic': '50 x 50'
    },
    '/usr/share/icons/hicolor/scalable/apps/tasque.svg': {},
    '/usr/share/pixmaps/tasque-16.png': {
        'magic': '18 x 18'
    },
    '/usr/share/pixmaps/tasque-32.png': {
        'magic': '34 x 34'
    },
    '/usr/share/tasque': {'is_dir': True},
    '/usr/share/tasque/icons': {'is_dir': True},
    '/usr/share/tasque/icons/hicolor': {'is_dir': True},
    '/usr/share/tasque/icons/hicolor/128x128': {'is_dir': True},
    '/usr/share/tasque/icons/hicolor/128x128/places': {'is_dir': True},
    '/usr/share/tasque/icons/hicolor/128x128/places/tasque-rtm-logo.png': {
        'magic': '130 x 130'
    },
    '/usr/share/tasque/icons/hicolor/16x16': {'is_dir': True},
    '/usr/share/tasque/icons/hicolor/16x16/status': {'is_dir': True},
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-0.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-1.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-10.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-11.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-2.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-3.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-4.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-5.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-6.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-7.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-8.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-completing-9.png': {
        'magic': '18 x 18'
    },
    '/usr/share/tasque/icons/hicolor/16x16/status/tasque-note.png': {
        'magic': '22 x 22'
    },
    '/usr/share/tasque/sounds': {'is_dir': True},
    '/usr/share/tasque/sounds/notify.wav': {}
})])
def test_icon_sizes(package, iconsizescheck):
    output, test = iconsizescheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'E: wrong-icon-size /usr/share/tasque/icons/hicolor/16x16/status/tasque-note.png expected: 16x16 actual: 22x22' in out
