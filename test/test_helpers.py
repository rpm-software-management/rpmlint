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
