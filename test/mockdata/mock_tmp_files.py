from Testing import get_tested_mock_package

TMPFILES = get_tested_mock_package(
    files={
        '/usr/lib/tmpfiles.d/krb5.conf': {'content': """
d /var/lib/kerberos 		0755	root	root	-
d /var/lib/kerberos/krb5	0755	root	root	-
d /var/lib/kerberos/krb5/user	0755	root	root	-
d /var/lib/kerberos/krb5kdc	0755	root	root	-
C /var/lib/kerberos/krb5kdc/kdc.conf	0600 root root - /usr/share/kerberos/krb5kdc/kdc.conf
C /var/lib/kerberos/krb5kdc/kadm5.acl	0600 root root - /usr/share/kerberos/krb5kdc/kadm5.acl
C /var/lib/kerberos/krb5kdc/kadm5.dict	0600 root root - /usr/share/kerberos/krb5kdc/kadm5.dict
"""},
        '/usr/lib/tmpfiles.d/symlink.conf': {'linkto': '/usr/lib/tmpfiles.d/krb5.conf'}
    },
    header={},
)


TMPFILES2 = get_tested_mock_package(
    files={
        '/usr/lib/tmpfiles.d/systemd-tmpfiles.conf': {'content': """
# create a directory with permissions 0770 owned by user foo and group bar
d /run/my_new_directory 0770 foo bar
"""}, },
    header={
        'PREIN': """[ -z "${TRANSACTIONAL_UPDATE}" -a -x /usr/bin/systemd-tmpfiles ] && /usr/bin/systemd-tmpfiles --create /usr/lib/tmpfiles.d/systemd-tmpfiles.conf || :
"""},
)


TMPFILES3 = get_tested_mock_package(
    files={
        '/run/my_new_directory'
        '/usr/lib/tmpfiles.d/systemd-tmpfiles_correct.conf': {'content': """
# create a directory with permissions 0770 owned by user foo and group bar
d /run/my_new_directory 0770 foo bar
"""}, },
    header={}, )
