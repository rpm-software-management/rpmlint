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
