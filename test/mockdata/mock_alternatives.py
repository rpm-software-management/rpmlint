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
import rpm

from Testing import get_tested_mock_package


UpdateAlternativesOkPackage = get_tested_mock_package(
    lazyload=True,
    name='alternatives-ok',
    header={
        'requires': [
            ('/bin/sh', rpm.RPMSENSE_SCRIPT_PRE | rpm.RPMSENSE_SCRIPT_POST),
            ('/usr/bin/update-alternatives', rpm.RPMSENSE_SCRIPT_POST),
        ],
        'postin': 'update-alternatives --install /usr/bin/alternative-ok alternative-ok /usr/bin/alternator 99',
        'postun': 'if [ ! -f /usr/bin/alternative-ok ] ; then\n\tupdate-alternatives --remove alternative-ok /usr/bin/alternator\n\tupdate-alternatives --remove alternative-ok /usr/bin/alternator2\nfi',
    },
    files={
        '/etc/alternatives/alternative-ok': {
            'metadata': {'flags': rpm.RPMFILE_GHOST},
        },
        '/usr/bin/alternative-ok': {
            'linkto': '/etc/alternatives/alternative-ok',
        },
        '/usr/bin/alternator': {},
    },
)


UpdateAlternativesBorkedPackage = get_tested_mock_package(
    lazyload=True,
    name='alternatives-borked',
    header={
        'requires': ['/bin/sh'],
        'postin': "# we can't do it in OBS as it actually even stops this from being built\n# it will still be caught by the checks in rpmlint tho\n#update-alternatives --install /usr/bin/alternative-borked alternative-borked /usr/bin/alternator 99",
        'postun': '# do nothing',
    },
    files={
        '/etc/alternatives/alternative-borked': {},
        '/usr/bin/alternative-borked': {},
        '/usr/bin/alternator': {},
    },
)


NonAlternativesPackage = get_tested_mock_package(
    lazyload=True,
    name='non-alternatives',
    header={
        'requires': ['/bin/sh'],
    },
)


UpdateAlternativesCorrectnessPackage = get_tested_mock_package(
    lazyload=True,
    name='update-alternatives-correctness',
    header={
        'requires': [
            ('/bin/sh', rpm.RPMSENSE_SCRIPT_PRE | rpm.RPMSENSE_SCRIPT_POST),
            ('update-alternatives', rpm.RPMSENSE_SCRIPT_POST),
        ],
        'postin': ' \nupdate-alternatives --quiet --install /usr/bin/evtx_dump.py evtx_dump.py /usr/bin/evtx_dump.py-3.9 39 \n',
        'postun': '\n\nif [ ! -e "/usr/bin/evtx_dump.py-3.9" ]; then \n    update-alternatives --quiet --remove "evtx_dump.py" "/usr/bin/evtx_dump.py-3.9" \nfi \n',
    },
    files={
        '/etc/alternatives/evtx_dump.py': {
            'metadata': {'flags': rpm.RPMFILE_GHOST},
        },
        '/usr/bin/evtx_dump.py': {
            'linkto': '/etc/alternatives/evtx_dump.py',
        },
        '/usr/bin/evtx_dump.py-3.9': {},
    },
)


LibalternativesOkPackage = get_tested_mock_package(
    lazyload=True,
    name='libalternatives-ok',
    header={
        'requires': ['alts'],
    },
    files={
        '/usr/bin/alternator': {
            'linkto': 'alts',
        },
        '/usr/bin/alternator_exe': {},
        '/usr/share/libalternatives/alternator/1.conf': {
            'create_dirs': True,
            'content': 'binary=/usr/bin/alternator_exe\nman=alternator.1\n',
        },
        '/usr/share/man/man1/alternator.1.gz': {
            'create_dirs': True,
        },
    },
)


LibalternativesBorkedPackage = get_tested_mock_package(
    lazyload=True,
    name='libalternatives-borked',
    header={
        'requires': ['/bin/sh'],
    },
    files={
        '/usr/bin/alternator_with_empty_config': {
            'linkto': 'alts',
        },
        '/usr/bin/alternator_without_config': {
            'linkto': 'alts',
        },
        '/usr/share/libalternatives/alternator_with_empty_config': {
            'is_dir': True,
        },
        '/usr/share/libalternatives/borked_alternator/1.conf': {
            'create_dirs': True,
            'content': 'binary=/usr/bin/not_there\nman=not_there.1, not_there.2\n',
        },
        '/usr/share/libalternatives/ghost/99.conf': {
            'create_dirs': True,
            'metadata': {'flags': rpm.RPMFILE_GHOST},
        },
    },
)
