import stat

import rpm

from Testing import get_tested_mock_package

FILES = get_tested_mock_package(
    files={
        '/%{unexpanded}/test': {},
        '/usr/bin/unexpanded-macro-files': {'is_dir': True},
        '/usr/share/licenses/unexpanded-macro-files': {'is_dir': True},
        '/usr/share/licenses/unexpanded-macro-files/LICENSE': {}
    },
    header={
        'requires': ["""
        /bin/bash
        bash
        rpmlib(CompressedFileNames) <= 3.0.4-1
        rpmlib(FileDigests) <= 4.6.0-1
        rpmlib(PayloadFilesHavePrefix) <= 4.0-1
        rpmlib(PayloadIsZstd) <= 5.4.18-1
        """]}
)

FILES2 = get_tested_mock_package(
    name='python3-power',
    files={
        '/usr/lib/python3.3/site-packages/power/__init__.py': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 0 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/darwin.cpython-33.pyc': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/darwin.cpython-33.pyo': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/common.py': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 0 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/darwin.py': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 0 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/linux.py': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 0 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/tests.py': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 0 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/win32.py': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 0 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/darwin/IOPSKeys_h/index.html': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/darwin/IOPSKeys_h/toc.html': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/darwin/IOPowerSources_h/index.html': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/darwin/IOPowerSources_h/toc.html': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/linux/power_supply.h': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/linux/power_supply_class.txt': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/win32/CallNtPowerInformation.htm': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/win32/GetSystemPowerStatus .htm': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/win32/Power Setting GUIDs.htm': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/win32/PowerSettingRegisterNotification.htm': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/win32/PowerSettingUnregisterNotification.htm': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/win32/SYSTEM_BATTERY_STATE.htm': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/python3-power-1.1/win32/SYSTEM_POWER_STATUS.htm': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/__init__.cpython-33.pyc': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/__init__.cpython-33.pyo': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/common.cpython-33.pyc': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/common.cpython-33.pyo': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/linux.cpython-33.pyc': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/linux.cpython-33.pyo': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/tests.cpython-33.pyc': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/tests.cpython-33.pyo': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/win32.cpython-33.pyc': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/lib/python3.3/site-packages/power/__pycache__/win32.cpython-33.pyo': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}}
    },
    header={
        'requires': [
            'python(abi) = 3.3',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PartialHardlinkSets) <= 4.0.4-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        ]
    }
)

FILES3 = get_tested_mock_package(
    name='testdocumentation',
    files={
        'usr/share/doc/packages/testdocumentation': {'is_dir': True, 'metadata': {'mode': 0o755 | stat.S_IFDIR, 'user': 'root', 'group': 'root', 'flags': 0}},
        '/usr/share/doc/packages/testdocumentation/README1.gz': {'content-path': 'files/README1.gz', 'create_dirs': True, 'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 2 | rpm.RPMFILE_DOC}},
        '/usr/share/doc/packages/testdocumentation/README2.bz2': {'content-path': 'files/README2.bz2', 'create_dirs': True, 'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 2 | rpm.RPMFILE_DOC}},
        '/usr/share/doc/packages/testdocumentation/README3.xz': {'content-path': 'files/README3.xz', 'create_dirs': True, 'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 2 | rpm.RPMFILE_DOC}},
    },
    header={
        'requires': {
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        }
    }
)

FILES4 = get_tested_mock_package(
    name='netmask-debugsource',
    files={
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/errors.c': {'content-path': 'files/netmask/errors.c', 'metadata': {'mode': 0o644 | stat.S_IFREG}},
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/errors.h': {'content-path': 'files/netmask/errors.h', 'metadata': {'mode': 0o644 | stat.S_IFREG}},
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/main.c': {'content-path': 'files/netmask/main.c', 'metadata': {'mode': 0o644 | stat.S_IFREG}},
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/netmask.c': {'content-path': 'files/netmask/netmask.c', 'metadata': {'mode': 0o644 | stat.S_IFREG}},
        '/usr/src/debug/netmask-2.4.3-5.fc27.x86_64/netmask.h': {'content-path': 'files/netmask/netmask.h', 'metadata': {'mode': 0o644 | stat.S_IFREG}},
    },
    header={
        'version': '2.4.3',
        'release': '5.fc27',
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ]
    }
)

FILES5 = get_tested_mock_package(
    files={
        '/usr/share/CMakeLists.txt': {},
        '/usr/share/Makefile.am': {'metadata': {'flags': rpm.RPMFILE_DOC}},
        '/usr/share/Makefile.in': {},
        '/usr/share/selinux': {'is_dir': True},
        '/usr/share/selinux/Makefile': {},
        '/usr/src/foo': {'is_dir': True},
        '/usr/src/foo/Makefile': {}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1'
        ]
    }
)

FILES6 = get_tested_mock_package(
    files={
        '/usr/lib64/python3.7/site-packages/greenlet-0.4.15-py3.7.egg-info': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 0 | stat.S_IFREG}},
        '/usr/lib64/python3.7/site-packages/greenlet.cpython-37m-x86_64-linux-gnu.so': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o755, 'flags': 0 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/AUTHORS': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/NEWS': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/README.rst': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_sources/greenlet.txt': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_sources/index.txt': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/basic.css': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/classic.css': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/default.css': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/doctools.js': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/documentation_options.js': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/file.png': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/jquery-3.2.1.js': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/jquery.js': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/language_data.js': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/minus.png': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/plus.png': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/pygments.css': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/searchtools.js': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/sidebar.js': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/underscore-1.3.1.js': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/_static/underscore.js': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/genindex.html': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/greenlet.html': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/index.html': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/objects.inv': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/search.html': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/doc/packages/python3-greenlet/html/searchindex.js': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 2 | stat.S_IFREG}},
        '/usr/share/licenses/python3-greenlet/LICENSE': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 128 | stat.S_IFREG}},
        '/usr/share/licenses/python3-greenlet/LICENSE.PSF': {'metadata': {'user': 'root', 'group': 'root', 'mode': 0o644, 'flags': 128 | stat.S_IFREG}},
    },
    header={
        'requires': [
            'libc.so.6()(64bit)',
            'libc.so.6(GLIBC_2.14)(64bit)',
            'libc.so.6(GLIBC_2.2.5)(64bit)',
            'libc.so.6(GLIBC_2.4)(64bit)',
            'libpython3.7m.so.1.0()(64bit)',
            'python(abi) = 3.7',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ]
    }
)

FILES7 = get_tested_mock_package(
    files={
        '/.gitignore': {},
        '/.htaccess': {},
        '/bin/foo/bar': {},
        '/etc/systemd/system/foo': {},
        '/etc/tmpfiles.d/foo': {},
        '/etc/udev/rules.d/foo': {},
        '/run/foo': {},
        '/site_perl/foo': {},
        '/usr/info/dir': {},
        '/usr/share/doc/perl-foo/MANIFEST': {},
        '/~backup.rej': {}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ]
    }
)

FILES8 = get_tested_mock_package(
    files={
        '/usr/lib64/tcl/pkgIndex.tcl': {}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
        ]
    }
)

FILES9 = get_tested_mock_package(
    files={
        '/etc/bar.rs': {'content': '#![allow(box_pointers)]', 'metadata': {'mode': 0o755}},
        '/etc/foo.rs': {
            'content': '#![allow(box_pointers)]',
            'metadata': {'mode': 0o755 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': rpm.RPMFILE_DOC}
        },
    },
    header={
        'requires': [
            'insserv',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1',
            'xinetd',
        ]
    }
)

FILES10 = get_tested_mock_package(
    files={
        '/etc/ngircd.conf': {},
        '/etc/pam.d/ngircd': {},
        '/usr/lib/systemd/system/ngircd.service': {},
        '/usr/sbin/ngircd': {},
        '/usr/share/doc/ngircd': {'is_dir': True},
        '/usr/share/doc/ngircd/AUTHORS': {},
        '/usr/share/doc/ngircd/Bopm.txt': {},
        '/usr/share/doc/ngircd/COPYING': {},
        '/usr/share/doc/ngircd/Capabilities.txt': {},
        '/usr/share/doc/ngircd/ChangeLog': {},
        '/usr/share/doc/ngircd/Commands.txt': {},
        '/usr/share/doc/ngircd/Contributing.txt': {},
        '/usr/share/doc/ngircd/FAQ.txt': {},
        '/usr/share/doc/ngircd/GIT.txt': {},
        '/usr/share/doc/ngircd/HowToRelease.txt': {},
        '/usr/share/doc/ngircd/Modes.txt': {},
        '/usr/share/doc/ngircd/NEWS': {},
        '/usr/share/doc/ngircd/PAM.txt': {},
        '/usr/share/doc/ngircd/Platforms.txt': {},
        '/usr/share/doc/ngircd/Protocol.txt': {},
        '/usr/share/doc/ngircd/README': {},
        '/usr/share/doc/ngircd/README-AUX.txt': {},
        '/usr/share/doc/ngircd/README-BeOS.txt': {},
        '/usr/share/doc/ngircd/README-Interix.txt': {},
        '/usr/share/doc/ngircd/RFC.txt': {},
        '/usr/share/doc/ngircd/SSL.txt': {},
        '/usr/share/doc/ngircd/Services.txt': {},
        '/usr/share/doc/ngircd/sample-ngircd.conf': {},
        '/usr/share/doc/ngircd/sample-ngircd.conf.tmpl': {},
        '/usr/share/man/man5/ngircd.conf.5.gz': {},
        '/usr/share/man/man8/ngircd.8.gz': {},
        '/var/run/ngircd': {}
    },
    header={
        'requires': ["""
            /bin/sh
            /bin/sh
            /bin/sh
            /bin/sh
            config(ngircd) = 22-2.fc22
            libc.so.6()(64bit)
            libc.so.6(GLIBC_2.14)(64bit)
            libc.so.6(GLIBC_2.15)(64bit)
            libc.so.6(GLIBC_2.2.5)(64bit)
            libc.so.6(GLIBC_2.3)(64bit)
            libc.so.6(GLIBC_2.3.2)(64bit)
            libc.so.6(GLIBC_2.3.4)(64bit)
            libc.so.6(GLIBC_2.4)(64bit)
            libgnutls.so.28()(64bit)
            libgnutls.so.28(GNUTLS_1_4)(64bit)
            libident.so.0()(64bit)
            libpam.so.0()(64bit)
            libpam.so.0(LIBPAM_1.0)(64bit)
            libwrap.so.0()(64bit)
            libz.so.1()(64bit)
            rpmlib(CompressedFileNames) <= 3.0.4-1
            rpmlib(FileDigests) <= 4.6.0-1
            rpmlib(PayloadFilesHavePrefix) <= 4.0-1
            rpmlib(PayloadIsXz) <= 5.2-1
            rtld(GNU_HASH)
            shadow-utils
            systemd
            systemd
            systemd"""]
    }
)

FILES11 = get_tested_mock_package(
    name='my-package-devel',
    files={
        '/usr/x.typelib': {'content-path': 'files/x.typelib', 'metadata': {'mode': 0o644 | stat.S_IFREG, 'size': 100, 'user': 'root', 'group': 'root', 'flags': 0 | rpm.RPMFILE_DOC}}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        ]
    }
)

FILES12 = get_tested_mock_package(
    name='shlib1',
    files={
        '/usr/lib/libfoo-2.so': {'content-path': 'files/shlib2/libfoo-2.so', 'metadata': {'mode': 0o755 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 0 | rpm.RPMFILE_DOC}},
        '/usr/lib/libfoo-2.so.foo': {'content-path': 'files/shlib2/libfoo-2.so.foo', 'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 0 | rpm.RPMFILE_DOC}},
        '/usr/lib/libfoo.so': {'content-path': 'files/shlib2/libfoo.so', 'metadata': {'mode': 0o777 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 0 | rpm.RPMFILE_DOC}, 'linkto': 'libfoo.so.1'},
        '/usr/lib/libfoo.so.1': {'content-path': 'files/shlib2/libfoo.so.1', 'metadata': {'mode': 0o755 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 0 | rpm.RPMFILE_DOC}}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        ]
    }
)

FILES13 = get_tested_mock_package(
    name='shlib2-devel',
    files={
        '/usr/lib/libfoo-2.so': {'content-path': 'files/shlib2/libfoo-2.so', 'metadata': {'mode': 0o755 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 0 | rpm.RPMFILE_DOC}},
        '/usr/lib/libfoo-2.so.foo': {'content-path': 'files/shlib2/libfoo-2.so.foo', 'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 0 | rpm.RPMFILE_DOC}},
        '/usr/lib/libfoo.so': {'content-path': 'files/shlib2/libfoo.so', 'metadata': {'mode': 0o777 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 0 | rpm.RPMFILE_DOC}, 'linkto': 'libfoo.so.1'},
        '/usr/lib/libfoo.so.1': {'content-path': 'files/shlib2/libfoo.so.1', 'metadata': {'mode': 0o755 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 0 | rpm.RPMFILE_DOC}}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsXz) <= 5.2-1'
        ]}
)

FILES14 = get_tested_mock_package(
    files={
        '/etc/security/console.apps': {'is_dir': True, 'metadata': {'mode': 0o755, 'flags': 0 | rpm.RPMFILE_GHOST | stat.S_IFDIR, 'user': 'root', 'group': 'root', 'size': 4096}},
        '/etc/security/console.apps/myapp': {'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'size': 100, 'flags': 1}},
        '/usr/lib/.nosearch': {'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'flags': 0}},
        '/usr/lib/emptyfile': {'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'size': 0, 'flags': 0}},  # Tamaño 0 para activar la verificación
        '/usr/lib/nonemptyfile': {'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'size': 100, 'flags': 0}},  # Tamaño no 0
        '/usr/lib/python': {'is_dir': True, 'metadata': {'flags': rpm.RPMFILE_GHOST | stat.S_IFDIR | 0, 'size': 4096, 'mode': 0o755 | stat.S_IFDIR, 'user': 'root', 'group': 'root'}},
        '/usr/lib/python/__init__.py': {'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'size': 0, 'flags': 0}},  # Tamaño 0 pero será ignorado por normal_zero_length_regex
        '/usr/lib/python/py.typed': {'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'size': 0, 'flags': 0}},  # Tamaño 0 pero será ignorado por normal_zero_length_regex
        '/usr/lib/python/pypackagefromwheel-0.0.0.dist-info/REQUESTED': {'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'size': 0, 'flags': 0}},  # Tamaño 0 pero será ignorado
        '/usr/lib/ruby/gem.build_complete': {'metadata': {'mode': 0o644 | stat.S_IFREG, 'user': 'root', 'group': 'root', 'size': 0, 'flags': 0}},  # Tamaño 0 pero será ignorado
    },
    header={
        'requires': [
            'config(file-zero-length) = 1.1-0',
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1'
        ]
    }
)

FILES15 = get_tested_mock_package(
    files={
        '/usr/share/man/man0p': {'is_dir': True},
        '/usr/share/man/man0p/foo.3.gz': {},
        '/usr/share/man/man1': {'is_dir': True},
        '/usr/share/man/man1/test.1.zst': {},
        '/usr/share/man/man3': {'is_dir': True},
        '/usr/share/man/man3/foo': {'is_dir': True},
        '/usr/share/man/man3/foo/bar': {'is_dir': True},
        '/usr/share/man/man3/foo/bar/baz.3.gz': {},
        '/usr/share/man/man3/some.3pm.gz': {}
    },
    header={
        'requires': [
            'rpmlib(CompressedFileNames) <= 3.0.4-1',
            'rpmlib(FileDigests) <= 4.6.0-1',
            'rpmlib(PayloadFilesHavePrefix) <= 4.0-1',
            'rpmlib(PayloadIsZstd) <= 5.4.18-1'
        ]
    }
)

FILES16 = get_tested_mock_package(
    files={
        '/usr/share/package/bin.py': {
            'content': '#!/usr/bin/python3\nprint("python required")',
            'metadata': {'mode': 0o755 | stat.S_IFREG},
        },
        '/usr/bin/testlink': {
            'linkto': '../share/package/bin.py',
        },
    },
    header={},
)

FILES17 = get_tested_mock_package(
    files={
        '/usr/share/package/bin.py': {
            'content': '#!/usr/bin/python3\nprint("python required")',
            'metadata': {'mode': 0o755 | stat.S_IFREG},
        },
        '/usr/bin/testlink': {
            'linkto': '../share/package/bin.py',
        },
    },
    header={
        'requires': ['/usr/bin/python3'],
    },
)

FILES18 = get_tested_mock_package(
    header={'requires': []},
    files={
        '/etc/raddb/mods-config/sql/moonshot-targeted-ids/mysql': {
            'is_dir': True,
            'metadata': {'mode': 0o640 | stat.S_IFDIR},
        },
        '/etc/raddb/mods-config/sql/moonshot-targeted-ids/postgresql': {
            'is_dir': True,
            'metadata': {'mode': 0o640 | stat.S_IFDIR},
        },
        '/etc/raddb/mods-config/sql/moonshot-targeted-ids/sqlite': {
            'is_dir': True,
            'metadata': {'mode': 0o640 | stat.S_IFDIR},
        },
    },
)

FILES19 = get_tested_mock_package(
    header={'requires': []},
    files={
        '/etc/raddb': {
            'is_dir': True,
            'metadata': {
                'mode': 0o640 | stat.S_IFDIR
            },
        },
        '/etc/raddb/certs': {
            'is_dir': True,
            'metadata': {
                'mode': 0o640 | stat.S_IFDIR
            },
        },
        '/etc/raddb/mods-available': {
            'is_dir': True,
            'metadata': {
                'mode': 0o640 | stat.S_IFDIR
            },
        },
        '/etc/raddb/mods-config': {
            'is_dir': True,
            'metadata': {
                'mode': 0o640 | stat.S_IFDIR
            },
        },
        '/etc/raddb/policy.d': {
            'is_dir': True,
            'metadata': {
                'mode': 0o640 | stat.S_IFDIR
            },
        },
        '/etc/raddb/sites-available': {
            'is_dir': True,
            'metadata': {
                'mode': 0o640 | stat.S_IFDIR
            },
        },
        '/etc/raddb/sites-enabled': {
            'is_dir': True,
            'metadata': {
                'mode': 0o640 | stat.S_IFDIR
            },
        },
        '/usr/lib64/freeradius': {
            'is_dir': True,
            'metadata': {
                'mode': 0o640 | stat.S_IFDIR
            },
        },
        '/usr/share/freeradius': {
            'is_dir': True,
            'metadata': {
                'mode': 0o640 | stat.S_IFDIR
            },
        },
    }
)

FILES20 = get_tested_mock_package(
    header={'requires': []},
    files={
        '/var/lib/pipewire': {'is_dir': True, 'metadata': {'mode': 0o000 | stat.S_IFDIR}},
        '/var/lib/dir_read': {'is_dir': True, 'metadata': {'mode': 0o755 | stat.S_IFDIR}},
        '/var/lib/pipewire/ghost_file': {'metadata': {'mode': 0o000, 'flags': rpm.RPMFILE_GHOST}},
        '/var/lib/pipewire/ghost_file_read': {'metadata': {'mode': 0o644, 'flags': rpm.RPMFILE_GHOST}},
        '/var/lib/pipewire/normal_file': {'metadata': {'mode': 0o000}},
        '/var/lib/pipewire/normal_file_read': {'metadata': {'mode': 0o644}},
    },
)

FILES21 = get_tested_mock_package(
    header={'requires': []},
    files={
        '/run/netconfig/resolv.conf': {'metadata': {'mode': 0o000, 'flags': rpm.RPMFILE_GHOST}},
        '/run/netconfig/yp.conf': {'metadata': {'mode': 0o644, 'flags': rpm.RPMFILE_GHOST}},
        '/run/netconfig': {'is_dir': True, 'metadata': {'mode': 0o000, 'flags': rpm.RPMFILE_GHOST | stat.S_IFDIR}},
        '/usr/lib/tmpfiles.d/netconfig.conf': {
            'content': """
d /run/netconfig 0755 root group -
f /run/netconfig/resolv.conf 0644 root root -
f /run/netconfig/yp.conf 0644 root root -
"""
        },
    },
)
