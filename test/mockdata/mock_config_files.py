from rpm import RPMFILE_CONFIG, RPMFILE_NOREPLACE

from Testing import get_tested_mock_package


CONFIGFILES = get_tested_mock_package(
    files={
        '/etc/conffile1': {'metadata': {'flags': RPMFILE_CONFIG}},
        '/var/conffile2': {'metadata': {'flags': RPMFILE_CONFIG}},
        '/usr/share/conffile3': {'metadata': {'flags': RPMFILE_CONFIG}},
    }
)

CONFIGFILES2 = get_tested_mock_package(
    files=[
        'tmp/foo/my.log',
        'tmp/foo2/my.log',
        'etc/logrotate.d/logrotate2.conf',
        'etc/logrotate.d/logrotate.conf',
    ]
)


CONFIGFILES3 = get_tested_mock_package(
    files={
        '/etc/conffile1': {'metadata': {'flags': RPMFILE_CONFIG & RPMFILE_NOREPLACE}},
        '/var/conffile2': {'metadata': {'flags': RPMFILE_CONFIG & RPMFILE_NOREPLACE}},
    }
)
