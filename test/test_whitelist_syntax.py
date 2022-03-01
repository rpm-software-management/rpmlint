import toml


def basic_syntax_checks(entry):
    # xor limitation
    assert ('package' in entry) != ('packages' in entry)
    assert isinstance(entry.get('package', ''), str)
    assert isinstance(entry.get('packages', []), list)

    # an entry without bugs is allowed, there are some non-reviewed legacy
    # entries
    if 'bug' in entry or 'bugs' in entry:
        # xor limitation
        assert ('bug' in entry) != ('bugs' in entry)
        assert isinstance(entry.get('bug', ''), str)
        assert isinstance(entry.get('bugs', []), list)

        bugs = entry.setdefault('bugs', [])
        if 'bug' in entry:
            bugs.append(entry['bug'])

        for bug in bugs:
            bug = bug.strip()
            prefix, nr = bug.split('#', 1)
            assert prefix in ('bsc', 'boo')
            assert nr.isdigit()

    # we use 'note'
    assert 'comment' not in entry


def test_file_digest_whitelists():
    WHITELISTS = [
        ('cron', 'cron-whitelist'),
        ('dbus', 'dbus-services'),
        ('pam', 'pam-modules'),
        ('permissions', 'permissions-whitelist'),
        ('polkit', 'polkit-rules-whitelist')
    ]

    for _type, whitelist in WHITELISTS:
        path = f'configs/openSUSE/{whitelist}.toml'
        data = toml.load(path)
        for entry in data['FileDigestGroup']:
            basic_syntax_checks(entry)

            assert entry['type'] == _type


def test_metadata_whitelists():
    WHITELISTS = [
        ('WorldWritableWhitelist', 'world-writable-whitelist'),
        ('DeviceFilesWhitelist', 'device-files-whitelist')
    ]

    for key, whitelist in WHITELISTS:
        path = f'configs/openSUSE/{whitelist}.toml'
        data = toml.load(path)
        for entry in data[key]:
            basic_syntax_checks(entry)
