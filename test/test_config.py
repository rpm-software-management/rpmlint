import os

from rpmlint.Config import Config

from Testing import TEST_CONFIG, testpath


TEST_CONFIG_2 = os.path.join(testpath(), 'configs/test2.config')
TEST_CONFIG_FILTERS = os.path.join(testpath(), 'configs/testfilters.config')
TEST_LIST1 = os.path.join(testpath(), 'configs/testlists1.config')
TEST_LIST2 = os.path.join(testpath(), 'configs/testlists2.config')
TEST_RPMLINTRC = os.path.join(testpath(), 'configs/testing-rpmlintrc')


def test_printing(capsys):
    cfg = Config()
    cfg.print_config()
    out, err = capsys.readouterr()
    assert not err
    assert out


def test_custom_config(capsys):
    cfg = Config()
    # bullshit config
    cfg.find_configs('BULLSHIT')
    out, err = capsys.readouterr()
    assert 'BULLSHIT' not in cfg.conf_files
    assert 'BULLSHIT' in err
    # existing config
    cfg.find_configs(TEST_CONFIG)
    out, err = capsys.readouterr()
    assert cfg.conf_files
    assert not err


def test_parsing():
    # ugly content variables from old config
    bad_crypto_warning = \
        """This application package calls a function to explicitly set crypto ciphers
        for SSL/TLS. That may cause the application not to use the system-wide set
        cryptographic policy and should be modified in accordance to:
        https://fedoraproject.org/wiki/Packaging:CryptoPolicies"""
    call_blacklist = {
        'crypto-policy-non-compliance-openssl': {
            'f_name': 'SSL_CTX_set_cipher_list',
            'good_param': '',
            'description': bad_crypto_warning,
        },
        'crypto-policy-non-compliance-gnutls-1': {
            'f_name': 'gnutls_priority_set_direct',
            'good_param': '',
            'description': bad_crypto_warning,
        },
        'crypto-policy-non-compliance-gnutls-2': {
            'f_name': 'gnutls_priority_init',
            'good_param': 'SYSLOG',
            'description': bad_crypto_warning
        },
    }

    cfg = Config(TEST_CONFIG)
    assert cfg.configuration
    assert cfg.configuration['Distribution'] == 'Fedora Project'
    assert cfg.configuration['WarnOnFunction'] == call_blacklist
    # default value check
    assert cfg.configuration['UseDefaultRunlevels'] is True


def test_double_config():
    """
    Load two configs and make sure we overshadow, not replace
    """
    cfg = Config(TEST_CONFIG)
    assert len(cfg.conf_files) == 1
    assert cfg.configuration['ExtraMenuNeeds'][0] == 'gnome'
    # shovel in another config
    cfg.load_config(TEST_CONFIG_2)
    assert len(cfg.conf_files) == 2
    assert cfg.configuration['Distribution'] == 'Fedora Project'
    assert cfg.configuration['Vendor'] == 'SUSE'
    assert cfg.configuration['ExtraMenuNeeds'][0] == 'windows'
    assert cfg.configuration['WarnOnFunction']['crypto-policy-non-compliance-gnutls-1']
    assert cfg.configuration['WarnOnFunction']['crypto-policy-non-compliance-openssl']['f_name'] == 'REPLACED'
    assert cfg.configuration['WarnOnFunction']['crypto-policy-3']['f_name'] == 'new_blobie'


def test_filters():
    """
    Load some filters and make sure we generate nice regexp
    """
    cfg = Config(TEST_CONFIG_FILTERS)
    assert len(cfg.configuration['Filters']) == 9
    assert cfg.configuration['Filters'][0] == '.*invalid-buildhost.*'


def test_list_merging():
    """
    Load two configs and check we properly either override or append
    """
    cfg = Config(TEST_LIST1)
    assert len(cfg.configuration['Filters']) == 1
    assert cfg.configuration['ValidGroups'][0] == 'bullshitgroup'
    cfg.load_config(TEST_LIST2)
    assert len(cfg.configuration['Filters']) == 2
    assert len(cfg.configuration['ValidGroups']) == 1
    assert cfg.configuration['ValidGroups'][0] == 'System/Libraries'


def test_checks_functions():
    """
    Test resetting of the tests and loading new ones
    """
    cfg = Config(TEST_CONFIG)
    assert len(cfg.configuration['Checks']) == 20
    cfg.reset_checks()
    assert len(cfg.configuration['Checks']) == 0
    cfg.add_check('TagsCheck')
    assert len(cfg.configuration['Checks']) == 1
    cfg.add_check('CompleteFakeTestsThatDoesNotExist')
    assert len(cfg.configuration['Checks']) == 1


def test_badness_functions():
    """
    Test badness settings
    """
    cfg = Config(TEST_CONFIG_2)
    assert len(cfg.configuration['Scoring']) == 0
    cfg.set_badness('suse-dbus-unauthorized-service', 15)
    assert len(cfg.configuration['Scoring']) == 1
    assert cfg.configuration['Scoring']['suse-dbus-unauthorized-service'] == 15


def test_rpmlint_loading():
    """
    Make sure we can load up rpmlintrc file without executing any code
    """
    cfg = Config(TEST_CONFIG)
    cfg.load_rpmlintrc(TEST_RPMLINTRC)
    assert len(cfg.configuration['Filters']) == 109
    assert len(cfg.configuration['Scoring']) == 2
