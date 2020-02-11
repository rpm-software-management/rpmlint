import re

from rpmlint.helpers import print_warning

try:
    from enchant import Broker
    from enchant.checker import SpellChecker
    from enchant.tokenize import EmailFilter, URLFilter, WikiWordFilter
    ENCHANT = True
except ImportError:
    # if the enchant is not present we simply continue but without
    # spellchecking work being done
    ENCHANT = None


class Spellcheck(object):
    """
    The object containing current state of spellchecking used within rpmlint
    """

    sentence_break_regex = re.compile(r'(^|[.:;!?])\s*$')
    _enchant_checkers = {}

    def __init__(self):
        pass

    def _init_checker(self, lang='en_US'):
        """
        Initialize a checker of selected language if it is not yet present
        lang: language to initialize the dictionary
        """

        # C language means English
        if lang == 'C':
            lang = 'en_US'

        # test if we actually have working enchant
        if not ENCHANT:
            print_warning('(none): W: unable to init enchant, spellchecking disabled.')
            return

        # there might not be myspell/aspell/etc dicts present
        broker = Broker()
        if not broker.dict_exists(lang):
            print_warning(f'(none): W: unable to load spellchecking dictionary for {lang}.')
            return

        if lang not in self._enchant_checkers:
            checker = SpellChecker(lang, filters=[EmailFilter, URLFilter, WikiWordFilter])
            self._enchant_checkers[lang] = checker

    def spell_check(self, text, fmt, lang='en_US', pkgname='', ignored_words=None):
        """
        Spell check string and return list of warnings if we found out any typos.
        text: the checked text
        fmt: format of the result ie 'Description({})'
        lang: language code ie en_US, default en_US
        pkgname: name of the checked package - for specific ignore finegraining
        ignored_words: words to be ignored by the spellchecker
        """
        warned = set()
        suggestions = {}

        # Initialize spelling dictionary if not already done
        if lang not in self._enchant_checkers:
            self._init_checker(lang)
        # If the init failed, just return
        if lang not in self._enchant_checkers:
            return suggestions
        checker = self._enchant_checkers[lang]

        if checker:
            checker.set_text(re.sub(r'\s+', ' ', text))
            # Uppercase packagename to be case insensitive
            uppername = pkgname.upper()
            # Allow partial matches for just part of the name
            upperparts = uppername.split('-')
            # In english we can have ie. django's (so ignore such words)
            if lang.startswith('en'):
                ups = [x + "'S" for x in upperparts]
                upperparts.extend(ups)
            # uppercase all ignorewords
            if ignored_words:
                ignored_words = [x.upper() for x in ignored_words]

            # for each error found skip some parts
            for err in checker:
                # Skip already warned
                if err.word in warned:
                    continue
                warned.add(err.word)

                # Skip all capitalized words that do not start a sentence
                if err.word[0].isupper() and not \
                        self.sentence_break_regex.search(checker.leading_context(3)):
                    continue

                # Skip all uppercase words
                upperword = err.word.upper()
                if err.word == upperword:
                    continue

                # skip all ignored words
                if ignored_words and upperword in ignored_words:
                    continue

                # Skip errors containing package name or equal to a
                # 'component' of it, case insensitively
                if upperword in uppername or upperword in upperparts:
                    continue

                # Work around enchant's digit tokenizing behavior where
                # we split on numbers, just ommit everything thats in there
                if checker.leading_context(1).isdigit() or \
                        checker.trailing_context(1).isdigit():
                    continue

                # Warn and suggest
                sug = ', '.join(checker.suggest()[:3])
                if sug:
                    sug = f'-> {sug}'
                suggestions[err.word] = fmt.format(lang) + f' {err.word} {sug}'
            return suggestions
