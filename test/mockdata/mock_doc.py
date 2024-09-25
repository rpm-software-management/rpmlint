import stat
import rpm
from Testing import get_tested_mock_package


MyDocPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/share/doc/packages/mydoc/README': {
            'metadata': {
                'mode': 0o755 | stat.S_IFREG,
                'flags': rpm.RPMFILE_DOC,
            },
        },
        '/usr/share/doc/packages/mydoc/doc.html': {
            'metadata': {
                'mode': 0o755 | stat.S_IFREG,
                'flags': rpm.RPMFILE_DOC,
            },
        },
        '/usr/share/doc/packages/mydoc/strace.txt': {
            'metadata': {
                'mode': 0o644 | stat.S_IFREG,
                'flags': rpm.RPMFILE_DOC,
                'size': 268 * 1024,
            },
        },
    },
    header={
        'requires': [
            'python-leftover',
            'python-no-leftover',
        ],
    },
)


DocFileDependencyPackage = get_tested_mock_package(
    lazyload=True,
    name='doc-file-dependency',
    files={
        '/usr/bin/example': {
            'metadata': {'mode': stat.S_IFREG | 0o755, 'flags': rpm.RPMFILE_DOC},
        },
        '/usr/lib/python3.7/site-packages/__pycache__/example.cpython-37.pyc': {
            'metadata': {
                'mode': stat.S_IFREG | 0o644,
                'flags': rpm.RPMFILE_DOC,
                'requires': ['python(abi) = 3.7'],
            },
        },
        '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info/PKG-INFO': {
            'metadata': {'mode': stat.S_IFREG | 0o644, 'flags': rpm.RPMFILE_DOC},
        },
        '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info/SOURCES.txt': {
            'metadata': {'mode': stat.S_IFREG | 0o644, 'flags': rpm.RPMFILE_DOC},
        },
        '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info/dependency_links.txt': {
            'metadata': {'mode': stat.S_IFREG | 0o644, 'flags': rpm.RPMFILE_DOC},
        },
        '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info/entry_points.txt': {
            'metadata': {'mode': stat.S_IFREG | 0o644, 'flags': rpm.RPMFILE_DOC},
        },
        '/usr/lib/python3.7/site-packages/example-1.0.0-py3.7.egg-info/top_level.txt': {
            'metadata': {'mode': stat.S_IFREG | 0o644, 'flags': rpm.RPMFILE_DOC},
        },
        '/usr/lib/python3.7/site-packages/example.py': {
            'metadata': {
                'mode': stat.S_IFREG | 0o644,
                'flags': rpm.RPMFILE_DOC,
                'requires': ['python(abi) = 3.7'],
            },
        },
    },
    header={'provides': [], 'requires': []},
)

InstallFileInDocPackage = get_tested_mock_package(
    lazyload=True,
    name='install-file-in-docs',
    files={
        '/usr/share/doc/packages/install-file-in-docs/INSTALL': {
            'metadata': {'mode': stat.S_IFREG | 0o644, 'flags': rpm.RPMFILE_DOC},
        },
    },
    header={'provides': [], 'requires': []},
)
