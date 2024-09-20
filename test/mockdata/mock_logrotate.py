import stat

from rpm import RPMFILE_CONFIG, RPMFILE_NOREPLACE

from Testing import get_tested_mock_package


LogrotatePackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/tmp/foo': {
            'create_dirs': True,
            'is_dir': True,
            'metadata': {
                'mode': stat.S_IFDIR | 0o755,
                'user': 'marxin',
                'group': 'users',
            },
        },
        '/tmp/foo2': {
            'create_dirs': True,
            'is_dir': True,
            'metadata': {
                'mode': stat.S_IFREG | stat.S_ISUID | 0o777,
                'user': 'root',
                'group': 'users2',
            },
        },
        '/tmp/foo/my.log': {
            'metadata': {
                'mode': 0o644 | stat.S_IFREG,
                'user': 'root',
                'group': 'users2',
            },
        },
        '/tmp/foo2/my.log': {
            'metadata': {
                'mode': stat.S_IFREG | stat.S_ISUID | 0o777,
                'user': 'root',
                'group': 'users2',
            },
        },
        '/etc/logrotate.d/logrotate.conf': {
            'create_dirs': True,
            'content-path': 'files/logrotate/logrotate.conf',
        },
        '/etc/logrotate.d/logrotate2.conf': {
            'create_dirs': True,
            'content-path': 'files/logrotate/logrotate2.conf',
        },
    }
)
