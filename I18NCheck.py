#############################################################################
# File          : I18NCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Mon Nov 22 20:02:56 1999
# Version       : $Id$
# Purpose       : checks i18n bugs.
#############################################################################

from Filter import *
import AbstractCheck
import re

# Defined in header.h
HEADER_I18NTABLE=100

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
    'lug': 'lg', # 'lug' is valid, but we standardize on 2 letter codes
    'en_UK': 'en_GB'}

# Correct subdirs of /usr/share/local for LC_MESSAGES
# and /usr/share/man for locale man pages.
#
# TODO: what makes a subdir "correct"?  This list is missing quite a few
# entries from eg. ISO 639.
#
# 'en_RN' and 'en@IPA' are not real language bu funny variations on english
CORRECT_SUBDIRS = (
'af', 'am', 'ang', 'ar', 'as', 'az', 'az_IR', 'be', 'bg', 'bn', 'bn_IN', 'br',
'bs', 'ca', 'cs', 'cy', 'da', 'de', 'de_AT', 'dz', 'el',
'en_AU', 'en_CA', 'en_GB', 'en_IE', 'en_US', 'en_RN', 'en@IPA',
'eo', 'es', 'es_AR', 'es_ES', 'es_DO', 'es_GT', 'es_HN', 'es_SV', 'es_PE',
'es_PA', 'es_MX', 'et', 'eu',
'fa', 'fi', 'fo', 'fr', 'fur', 'ga', 'gd', 'gl', 'gn', 'gu', 'gv',
'he', 'hi', 'hr', 'hu', 'hy',
'ia', 'id', 'is', 'it', 'iu', 'ja', 'ka', 'kl', 'km', 'kn', 'ko', 'ku', 'kw',
# 'ltg' is not a standard ISO code; latgalian hasn't yet an ISO code
'ky', 'lg', 'li', 'lo', 'lt', 'ltg', 'lv',
'mg', 'mi', 'mk', 'ml', 'mn', 'mr', 'ms', 'mt', 'my',
'nb', 'nds', 'nds_DE', 'ne', 'nl', 'nn', 'no', 'nr', 'nso',
'oc', 'or', 'pa_IN', 'ph', 'pl', 'pp', 'pt', 'pt_BR', 'qu', 'ro', 'ru', 'rw',
'sc', 'se', 'si', 'sk', 'sl', 'sq', 'sr', 'sr@Latn', 'sr@ije', 'ss', 'st',
'sv', 'ta', 'te', 'tg', 'th', 'tk', 'tl', 'tn', 'tr', 'ts', 'tt',
'ug', 'uk', 'ur', 'uz', 'uz@Latn',
've', 'vi', 'wa', 'wen', 'xh', 'yi', 'yo', 'zh_CN', 'zh_HK', 'zh_TW', 'zu',
# KDE uses 'ven' for 've'
'ven',
#
# note: 'pa' should be replaced by 'pa_IN'; but it is still largely used
'pa',
# note: zh_CN.GB2312 and zh_TW.Big5 (that is, names with charset information)
# are obsolescent, but still widely used; some day however they should
# be removed from this list.
'zh_CN.GB2312', 'zh_TW.Big5',
)

st = '-('
for s in CORRECT_SUBDIRS:
    st += '|' + s[0:2]
st += ')$'

package_regex=re.compile(st)
locale_regex=re.compile('^(/usr/share/locale/([^/]+))/')
correct_subdir_regex=re.compile('^(([a-z][a-z]([a-z])?(_[A-Z][A-Z])?)([.@].*$)?)$')
lc_messages_regex=re.compile('/usr/share/locale/([^/]+)/LC_MESSAGES/.*(mo|po)$')
man_regex=re.compile('/usr(?:/share)?/man/([^/]+)/man./[^/]+$')

# list of exceptions
#
# note: ISO-8859-9E is non standard, ISO-8859-{6,8} are of limited use
# as locales (since all modern handling of bidi is based on utf-8 anyway),
# so they should be removed once UTF-8 is deployed)
EXCEPTION_DIRS=('C', 'POSIX', 'CP1251', 'CP1255', 'CP1256',
'ISO-8859-1', 'ISO-8859-2', 'ISO-8859-3', 'ISO-8859-4', 'ISO-8859-5',
'ISO-8859-6', 'ISO-8859-7', 'ISO-8859-8', 'ISO-8859-9', 'ISO-8859-9E',
'ISO-8859-10', 'ISO-8859-13', 'ISO-8859-14', 'ISO-8859-15',
'KOI8-R', 'KOI8-U', 'UTF-8')

class I18NCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'I18NCheck')

    def check(self, pkg):

        if pkg.isSource():
            return

        files=pkg.files().keys()
        files.sort()
        locales=[]                      # list of locales for this packages
        webapp=False

        i18n_tags = pkg[HEADER_I18NTABLE] or ()
        #i18n_files = pkg.langFiles()

        for i in i18n_tags:
            try:
                correct=INCORRECT_LOCALES[i]
                printError(pkg, 'incorrect-i18n-tag-' + correct, i)
            except KeyError:
                pass

        # as some webapps have their files under /var/www/html, and
        # others in /usr/share or /usr/lib, the only reliable way
        # sofar to detect them is to look for an apache configuration file
        for f in files:
            if f.startswith('/etc/apache2/') or f.startswith('/etc/httpd/conf.d/'):
                webapp=True

        for f in files:
            res=locale_regex.search(f)
            if res:
                locale=res.group(2)
                # checks the same locale only once
                if not locale in locales:
                    locales.append(locale)
                    res2=correct_subdir_regex.search(locale)
                    if not res2:
                        if not locale in EXCEPTION_DIRS:
                            printError(pkg, 'incorrect-locale-subdir', f)
                    else:
                        locale_name = res2.group(2)
                        try:
                            correct=INCORRECT_LOCALES[locale_name]
                            printError(pkg, 'incorrect-locale-' + correct, f)
                        except KeyError:
                            pass
            res=lc_messages_regex.search(f)
            subdir=None
            if res:
                subdir=res.group(1)
                if not subdir in CORRECT_SUBDIRS:
                    printError(pkg, 'invalid-lc-messages-dir', f)
            else:
                res=man_regex.search(f)
                if res:
                    subdir=res.group(1)
                    if subdir != 'man' and not subdir in CORRECT_SUBDIRS:
                        printError(pkg, 'invalid-locale-man-dir', f)
                    else:
                        subdir=None

            if f.endswith('.mo') or subdir:
                if pkg.fileLang(f) == '' and not webapp:
                    printWarning(pkg, 'file-not-in-%lang', f)

        main_dir, main_lang = ("", "")
        for f in files:
            lang = pkg.fileLang(f)
            if main_lang and lang == "" and is_prefix(main_dir + '/', f):
                printError(pkg, 'subfile-not-in-%lang', f)
            if main_lang != lang:
                main_dir, main_lang = f, lang

        name=pkg.name
        res=package_regex.search(name)
        if res:
            locales='locales-' + res.group(1)
            if locales != name:
                if not locales in map(lambda x: x[0], pkg.requires()):
                    printError(pkg, 'no-dependency-on', locales)

def is_prefix(p, s):
    return len(p) <= len(s) and p == s[:len(p)]

# Create an object to enable the auto registration of the test
check=I18NCheck()

if Config.info:
    addDetails(
# Need to add a function to list all the locales
'incorrect-i18n-tag-',
"""
""",

'incorrect-locale-subdir',
"""
""",

'incorrect-locale-',
"""
""",

'invalid-lc-messages-dir',
"""
""",

'invalid-locale-man-dir',
"""
""",

'file-not-in-lang',
"""
""",

'no-dependency-on',
"""
""",

'subfile-not-in-%lang',
""" If /foo/bar is not tagged %lang(XX) whereas /foo is, the package won't be installable if XX is not in %_install_langs""",

)

# I18NCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
