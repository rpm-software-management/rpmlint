import importlib

from rpmlint import helpers


def test_warnprint(capsys):
    """
    Check we print stuff to stderr
    """
    message = 'I am writing to stderr'
    helpers.print_warning(message)
    out, err = capsys.readouterr()
    assert message not in out
    assert message in err


def test_bytetostr():
    """
    Test bytetostr function
    """
    list_items = (
        b'\xc5\xbe\xc3\xad\xc5\xbeala',
        'texty',
    )
    item = b'p\xc5\x99\xc3\xad\xc5\xa1ern\xc4\x9b \xc5\xbelu\xc5\xa5ou\xc4\x8dk\xc3\xbd k\xc5\xaf\xc5\x88'

    result = helpers.byte_to_string(item)
    assert isinstance(result, str)
    assert result == 'příšerně žluťoučký kůň'

    result = helpers.byte_to_string(list_items)
    assert isinstance(result, list)
    assert result[0] == 'žížala'


def test_centering(capsys):
    """
    Check wether centered print works
    """

    message = 'Hello there'
    helpers.print_centered(message, '*')
    out, err = capsys.readouterr()
    assert '** Hello there **' in out
    assert not err


def test_english_environment_keeps_ld_library_path(monkeypatch):
    """
    ENGLISH_ENVIRONMENT forwards LD_LIBRARY_PATH: the tools bundled by
    the launcher (e.g. rpmlint-mini's dash) find their own libraries
    through it.
    """
    monkeypatch.setenv('LD_LIBRARY_PATH', '/opt/testing/lib')
    importlib.reload(helpers)
    try:
        assert helpers.ENGLISH_ENVIRONMENT['LD_LIBRARY_PATH'] == \
            '/opt/testing/lib'
    finally:
        importlib.reload(helpers)


def test_extraction_environment_drops_ld_library_path(monkeypatch):
    """
    EXTRACTION_ENVIRONMENT is ENGLISH_ENVIRONMENT without
    LD_LIBRARY_PATH: the extraction tools come from the build root
    being checked and must resolve its libraries, not the launcher's
    bundled ones.
    """
    monkeypatch.setenv('LD_LIBRARY_PATH', '/opt/testing/lib')
    importlib.reload(helpers)
    try:
        assert 'LD_LIBRARY_PATH' not in helpers.EXTRACTION_ENVIRONMENT
        assert helpers.EXTRACTION_ENVIRONMENT['LC_ALL'] == \
            helpers.ENGLISH_ENVIRONMENT['LC_ALL']
    finally:
        importlib.reload(helpers)
