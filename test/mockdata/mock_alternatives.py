from Testing import get_tested_mock_package


AlternativeConfFolder = get_tested_mock_package(
    lazyload=True,
    header={'requires': [], 'POSTIN': '', 'POSTUN': ''},
    name='alternatives',
    files={
        '/usr/share/libalternatives/rst2html/311.conf': {
            'create_dirs': True,
            'content': 'bin=/usr/bin/rst2html-3.11',
        },
        '/usr/share/libalternatives/rst2html/1313.conf': {
            'create_dirs': True,
            'content': 'binary=/usr/bin/=rst2html-3.13',
        },
        '/usr/share/libalternatives/ldaptor-ldap2dhcpconf/311.conf': {
            'create_dirs': True,
            'content': 'binary=/usr/bin/ldaptor-ldap2dhcpconf-3.11',
        },
        '/usr/share/libalternatives/ldaptor-ldap2dhcpconf/1311.conf': {
            'create_dirs': True,
            'content': 'binary=/usr/bin/ldaptor-ldap2dhcpconf-3.13',
        },
    }
)
