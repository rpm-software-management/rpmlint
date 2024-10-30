from rpm import RPMFILE_CONFIG, RPMFILE_NOREPLACE

from Testing import get_tested_mock_package


ConfigFilesBrokenPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/etc/conffile1': {'metadata': {'flags': RPMFILE_CONFIG}},
        '/var/conffile2': {'metadata': {'flags': RPMFILE_CONFIG}},
        '/usr/share/conffile3': {'metadata': {'flags': RPMFILE_CONFIG}},
    }
)


ConfigFilesOkPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/etc/conffile1': {'metadata': {'flags': RPMFILE_CONFIG & RPMFILE_NOREPLACE}},
        '/var/conffile2': {'metadata': {'flags': RPMFILE_CONFIG & RPMFILE_NOREPLACE}},
    }
)
