from Testing import get_tested_mock_package


BadCrcZipPackage = get_tested_mock_package(
    lazyload=True,
    name='bad-crc',
    files={
        '/usr/share/bad-crc.zip': {
            'content-path': 'files/bad-crc.zip',
        },
        '/usr/share/uncompressed.zip': {
            'content-path': 'files/uncompressed.zip',
        },
    },
)


ClasspathJarPackage = get_tested_mock_package(
    lazyload=True,
    name='classpath-jar',
    files={
        '/usr/share/java/classpath.jar': {
            'content-path': 'files/classpath.jar',
        },
    },
)


EncryptedZipPackage = get_tested_mock_package(
    lazyload=True,
    name='encrypted-zip',
    files={
        '/usr/share/encrypted.zip': {
            'content-path': 'files/encrypted.zip',
        },
    },
)


UnsupportedCompressionZipPackage = get_tested_mock_package(
    lazyload=True,
    name='unsupported-compression-zip',
    files={
        '/usr/share/demo.zip': {
            'content-path': 'files/unsupported-compression.zip',
        },
    },
)
