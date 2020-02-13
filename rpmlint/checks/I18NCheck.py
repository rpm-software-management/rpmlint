#############################################################################
# File          : I18NCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Mon Nov 22 20:02:56 1999
# Purpose       : checks i18n bugs.
#############################################################################

import re

import rpm
from rpmlint.__isocodes__ import COUNTRIES, LANGUAGES
from rpmlint.checks.AbstractCheck import AbstractCheck


# Associative array of invalid value => correct value
INCORRECT_LOCALES = {
    'in': 'id',
    'in_ID': 'id_ID',
    'iw': 'he',
    'iw_IL': 'he_IL',
    'gr': 'el',
    'gr_GR': 'el_GR',
    'cz': 'cs',
    'cz_CZ': 'cs_CZ',
    'lug': 'lg',  # 'lug' is valid, but we standardize on 2 letter codes
    'en_UK': 'en_GB'}

package_regex = re.compile('-(' + '|'.join(LANGUAGES) + ')$')
locale_regex = re.compile('^(/usr/share/locale/([^/]+))/')
correct_subdir_regex = re.compile('^(([a-z][a-z]([a-z])?(_[A-Z][A-Z])?)([.@].*$)?)$')
lc_messages_regex = re.compile('/usr/share/locale/([^/]+)/LC_MESSAGES/.*(mo|po)$')
man_regex = re.compile('/usr(?:/share)?/man/([^/]+)/man[0-9n][^/]*/[^/]+$')

# list of exceptions
#
# note: ISO-8859-9E is non standard, ISO-8859-{6,8} are of limited use
# as locales (since all modern handling of bidi is based on utf-8 anyway),
# so they should be removed once UTF-8 is deployed)
EXCEPTION_DIRS = (
    'C', 'POSIX', 'CP1251', 'CP1255', 'CP1256',
    'ISO-8859-1', 'ISO-8859-2', 'ISO-8859-3', 'ISO-8859-4', 'ISO-8859-5',
    'ISO-8859-6', 'ISO-8859-7', 'ISO-8859-8', 'ISO-8859-9', 'ISO-8859-9E',
    'ISO-8859-10', 'ISO-8859-13', 'ISO-8859-14', 'ISO-8859-15',
    'KOI8-R', 'KOI8-U', 'UTF-8', 'default')


def is_valid_lang(lang):
    # TODO: @Foo and charset handling
    lang = re.sub('[@.].*$', '', lang)

    if lang in LANGUAGES:
        return True

    ix = lang.find('_')
    if ix == -1:
        return False

    # TODO: don't accept all lang_COUNTRY combinations
    country = lang[ix + 1:]
    if country not in COUNTRIES:
        return False

    lang = lang[0:ix]
    if lang not in LANGUAGES:
        return False

    return True


class I18NCheck(AbstractCheck):
    def check_binary(self, pkg):
        files = list(pkg.files.keys())
        files.sort()
        locales = []                      # list of locales for this packages
        webapp = False

        i18n_tags = pkg[rpm.RPMTAG_HEADERI18NTABLE] or ()

        for i in i18n_tags:
            try:
                correct = INCORRECT_LOCALES[i]
                self.output.add_info('E', pkg, 'incorrect-i18n-tag-' + correct, i)
            except KeyError:
                pass

        # as some webapps have their files under /var/www/html, and
        # others in /usr/share or /usr/lib, the only reliable way
        # sofar to detect them is to look for an apache configuration file
        for f in files:
            if f.startswith('/etc/apache2/') or \
                    f.startswith('/etc/httpd/conf.d/'):
                webapp = True

        for f in files:
            res = locale_regex.search(f)
            if res:
                locale = res.group(2)
                # checks the same locale only once
                if locale not in locales:
                    locales.append(locale)
                    res2 = correct_subdir_regex.search(locale)
                    if not res2:
                        if locale not in EXCEPTION_DIRS:
                            self.output.add_info('E', pkg, 'incorrect-locale-subdir', f)
                    else:
                        locale_name = res2.group(2)
                        try:
                            correct = INCORRECT_LOCALES[locale_name]
                            self.output.add_info('E', pkg, 'incorrect-locale-' + correct, f)
                        except KeyError:
                            pass
            res = lc_messages_regex.search(f)
            subdir = None
            if res:
                subdir = res.group(1)
                if not is_valid_lang(subdir):
                    self.output.add_info('E', pkg, 'invalid-lc-messages-dir', f)
            else:
                res = man_regex.search(f)
                if res:
                    subdir = res.group(1)
                    if is_valid_lang(subdir):
                        subdir = None
                    else:
                        self.output.add_info('E', pkg, 'invalid-locale-man-dir', f)

            if f.endswith('.mo') or subdir:
                if pkg.files[f].lang == '' and not webapp:
                    self.output.add_info('W', pkg, 'file-not-in-%lang', f)

        main_dir, main_lang = ('', '')
        for f in files:
            lang = pkg.files[f].lang
            if main_lang and lang == '' and is_prefix(main_dir + '/', f):
                self.output.add_info('E', pkg, 'subfile-not-in-%lang', f)
            if main_lang != lang:
                main_dir, main_lang = f, lang

        name = pkg.name
        res = package_regex.search(name)
        if res:
            locales = 'locales-' + res.group(1)
            if locales != name:
                if locales not in (x[0] for x in pkg.requires):
                    self.output.add_info('E', pkg, 'no-dependency-on', locales)


def is_prefix(p, s):
    return len(p) <= len(s) and p == s[:len(p)]
