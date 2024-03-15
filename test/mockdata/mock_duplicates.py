from Testing import get_tested_mock_package


HardlinksAndDuplicatesPresent = get_tested_mock_package(
    lazyload=True,
    files={
        '/etc/bar': {'content': 'large enough file', 'metadata': {'mode': 33188}},
        '/etc/bar2': {'content': 'large enough file', 'metadata': {'mode': 33188}},
        '/etc/bar3': {'content': 'large enough file', 'metadata': {'mode': 33188}},
        '/etc/foo': {'content': 'Foo file', 'metadata': {'mode': 33188, 'inode': 10}},
        '/etc/foo2': {'content': 'Foo 2 file', 'metadata': {'mode': 33188, 'flags': 1, 'inode': 5}},
        '/etc/small': {'content': ' \n', 'metadata': {'mode': 33188}},
        '/etc/small2': {'content': ' \n', 'metadata': {'mode': 33188}},
        '/etc/strace1.txt': {'content': 'this is a very large file', 'metadata': {'mode': 33188, 'size': 270509}},
        '/etc/strace2.txt': {'content': 'this is a very large file', 'metadata': {'mode': 33188, 'size': 270509}},
        '/var/foo': {'content': 'Foo file', 'metadata': {'mode': 33188, 'inode': 10}},
        '/var/foo2': {'content': 'Foo 2 file', 'metadata': {'mode': 33188, 'flags': 1, 'inode': 5}}
    }
)

NoHardLinksAndDuplicatesPresent = HardlinksAndDuplicatesPresent.clone(
    files={
        '/usr/share/bad-crc.zip': {'content': 'this is a zip file', 'metadata': {'mode': 33188, 'flags': 1}},
        '/usr/share/uncompressed.zip': {'content': 'this is an another zip file', 'metadata': {'mode': 33188, 'flags': 1}},
    },
)
