from Testing import get_tested_mock_package


KRB5_CONF = """
d /var/lib/kerberos 		0755	root	root	-
d /var/lib/kerberos/krb5	0755	root	root	-
d /var/lib/kerberos/krb5/user	0755	root	root	-
d /var/lib/kerberos/krb5kdc	0755	root	root	-
C /var/lib/kerberos/krb5kdc/kdc.conf	0600 root root - /usr/share/kerberos/krb5kdc/kdc.conf
C /var/lib/kerberos/krb5kdc/kadm5.acl	0600 root root - /usr/share/kerberos/krb5kdc/kadm5.acl
C /var/lib/kerberos/krb5kdc/kadm5.dict	0600 root root - /usr/share/kerberos/krb5kdc/kadm5.dict
"""


SYSTEMD_TMPFILES_CONF = """
# create a directory with permissions 0770 owned by user foo and group bar
d /run/my_new_directory 0770 foo bar
"""


PREIN = """
[ -z "${TRANSACTIONAL_UPDATE}" -a -x /usr/bin/systemd-tmpfiles ] &&
    /usr/bin/systemd-tmpfiles --create /usr/lib/tmpfiles.d/systemd-tmpfiles.conf || :
"""

POSTIN = """
[ -z "${TRANSACTIONAL_UPDATE}" -a -x /usr/bin/systemd-tmpfiles ] &&
    /usr/bin/systemd-tmpfiles --create /usr/lib/tmpfiles.d/systemd-tmpfiles_correct.conf || :
"""


TempfiledPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib/tmpfiles.d/krb5.conf': {'content': KRB5_CONF},
        '/usr/lib/tmpfiles.d/symlink.conf': {'linkto': '/usr/lib/tmpfiles.d/krb5.conf'}
    },
    header={},
)


SystemdTempfilesPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/usr/lib/tmpfiles.d/systemd-tmpfiles.conf': {'content': SYSTEMD_TMPFILES_CONF},
    },
    header={'PREIN': PREIN},
)


SystemdTempfilesOkPackage = get_tested_mock_package(
    lazyload=True,
    files={
        '/run/my_new_directory': {},
        '/usr/lib/tmpfiles.d/systemd-tmpfiles_correct.conf': {'content': SYSTEMD_TMPFILES_CONF},
    },
    header={'POSTIN': POSTIN},
)
