from rpm import RPMFILE_CONFIG, RPMFILE_NOREPLACE

from Testing import get_tested_mock_package


LogrotatePackage = get_tested_mock_package(
    lazyload=True,
    files={
        'tmp/foo/my.log': {},
        'tmp/foo2/my.log': {},
        'etc/logrotate.d/logrotate.conf': { 'content-path': 'files/logrotate/logrotate.conf' },
        'etc/logrotate.d/logrotate2.conf': { 'content-path': 'files/logrotate/logrotate2.conf' },
    }
)
