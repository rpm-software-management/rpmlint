#############################################################################
# File		: I18NCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Mon Nov 22 20:02:56 1999
# Version	: $Id$
# Purpose	: checks i18n bugs.
#############################################################################

from Filter import *
import AbstractCheck
import re

# Defined in header.h
HEADER_I18NTABLE=100

# Associative array of invalid value => correct value
INCORRECT_LOCALES = {
    "in": "id",
    "in_ID": "id_ID",
    "iw": "he",
    "iw_IL": "he_IL",
    "gr": "el",
    "gr_GR": "el_GR",
    "cz": "cs",
    "cz_CZ": "cs_CZ",
    "sw": "sv",
    "en_UK": "en_GB"}

# Correct subdirs of /usr/share/local for LC_MESSAGES
CORRECT_SUBDIRS = (
"af", "ar", "az", "a3", "be", "bg", "br", "ca", "cs", "cy", "da", "de",
"de_AT", "el", "en_GB", "en_RN", "eo", "es", "es_AR", "es_ES", "es_DO",
"es_GT", "es_HN", "es_SV", "es_PE", "es_PA", "es_MX", "et", "eu", "fa",
"fa_IR.iransystem", "fi", "fo", "fr", "ga", "gd", "gl", "gv", "he", "hr",
"hu", "hy", "id", "is", "it", "ja", "ka", "ka_GE.georgian-ps", "kl", "ko",
"kw", "lo", "lt", "lv", "ma", "mk", "ms", "nb", "nl", "no", "no@nynorsk",
"ny", "oc", "pd", "ph", "pl", "pp", "pt", "pt_BR", "ro", "ru", "sk", "sl",
"sp", "sq", "sr", "sv", "ta", "tg", "th", "tr", "tt", "ur", "uk", "vi",
"vi_VN.viscii", "wa", "yi", "zh_CN", "zh_CN.GB2312", "zh_TW.Big5"
)

# list of exceptions
EXCEPTION_DIRS=('C', 'POSIX', 'iso88591', 'iso8859')

class I18NCheck(AbstractCheck.AbstractCheck):
    locale_regex=re.compile("^(/usr/share/locale/([^/]+))/")
    correct_subdir_regex=re.compile("^(([a-z][a-z](_[A-Z][A-Z])?)([.@].*$)?)$")
    lc_messages_regex=re.compile("/usr/share/locale/([^/]+)/LC_MESSAGES/.*(mo|po)$")
    mo_regex=re.compile("\.mo$")
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, "I18NCheck")

    def check(self, pkg, verbose):
	files=pkg.files()
	locales=[]			# list of locales for this packages

	i18n_tags = pkg[HEADER_I18NTABLE]
        i18n_files = pkg.langFiles()
        
	for i in i18n_tags:
	    try:
		correct=INCORRECT_LOCALES[i]
		printError(pkg, "incorrect-i18n-tag-" + correct, i)
	    except KeyError:
		pass
	    
	for f in files.keys():
	    res=I18NCheck.locale_regex.search(f)
	    if res:
		locale=res.group(2)
		# checks the same locale only once
		if not locale in locales:
		    locales.append(locale)
		    res2=I18NCheck.correct_subdir_regex.search(locale)
		    if not res2:
			if not locale in EXCEPTION_DIRS:
			    printError(pkg, "incorrect-locale-subdir", f)
		    else:
			locale_name = res2.group(2)
			try:
			    correct=INCORRECT_LOCALES[locale_name]
			    printError(pkg, "incorrect-locale-" + correct, f)
			except KeyError:
			    pass
            res=I18NCheck.lc_messages_regex.search(f)
            if res:
                subdir=res.group(1)
                if not subdir in CORRECT_SUBDIRS:
                    printError(pkg, "invalid-lc-messages-dir", f)

            if I18NCheck.mo_regex.search(f):
                if pkg.fileLang(f) == '':
                    printWarning(pkg, "file-not-in-%lang", f)
                    
# Create an object to enable the auto registration of the test
check=I18NCheck()

# I18NCheck.py ends here
