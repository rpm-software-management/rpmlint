import pytest
import rpmlint.spellcheck


@pytest.mark.skipif(not rpmlint.spellcheck.ENCHANT, reason='Missing enchant bindings')
def test_spelldict(capsys):
    """
    Check we can init dictionary spellchecker
    """
    spell = rpmlint.spellcheck.Spellcheck()
    spell._init_checker()
    out, err = capsys.readouterr()
    assert not out
    assert not err
    assert 'unable to load spellchecking dictionary' not in err

    spell._init_checker('not-existing-language')
    out, err = capsys.readouterr()
    assert not out
    assert 'unable to load spellchecking dictionary' in err

    assert 'en_US' in spell._enchant_checkers
    assert spell._enchant_checkers['en_US'] is not None
    assert 'not-existing-language' not in spell._enchant_checkers


@pytest.mark.skipif(not rpmlint.spellcheck.ENCHANT, reason='Missing enchant bindings')
def test_spellchecking():
    """
    Check if we can test the spelling
    """
    spell = rpmlint.spellcheck.Spellcheck()

    # correct text
    text = 'I swear this text is proper English'
    result = spell.spell_check(text, 'Description({}):')
    assert not result

    # english 2 typos
    text = "I don't think tihs tetx is correct English"
    result = spell.spell_check(text, 'Description({}):')
    assert len(result) == 2
    assert result['tihs'] == 'Description(en_US): tihs -> this, hits, ties'

    # different language, one typo
    text = 'Příčerně žluťoučký kůň'
    result = spell.spell_check(text, 'Summary({}):', 'cs_CZ')
    assert len(result) == 1
    assert result['Příčerně'] == 'Summary(cs_CZ): Příčerně -> Příčetně, Příčeně, Příšerně'

    # non-existing language, should return nothing:
    text = 'Weird english text'
    result = spell.spell_check(text, 'Summary({}):', 'de_CZ')
    assert not result


@pytest.mark.skipif(not rpmlint.spellcheck.ENCHANT, reason='Missing enchant bindings')
def test_pkgname_spellchecking():
    spell = rpmlint.spellcheck.Spellcheck()

    pkgname = 'python-squeqe'
    text = "This package is squeqe's framework helper"
    result = spell.spell_check(text, 'Description({}):', 'en_US', pkgname)
    assert not result


@pytest.mark.skipif(not rpmlint.spellcheck.ENCHANT, reason='Missing enchant bindings')
def test_ignorelist_spellchecking():
    spell = rpmlint.spellcheck.Spellcheck()

    ignore = ['wrod', 'žížala']
    text = 'This package should not have any typos in wrod or žíŽala'
    result = spell.spell_check(text, 'Description({}):', ignored_words=ignore)
    assert not result
