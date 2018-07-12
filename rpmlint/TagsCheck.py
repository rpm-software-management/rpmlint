# -*- coding: utf-8 -*-
#############################################################################
# File          : TagsCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 00:03:24 1999
# Purpose       : Check a package to see if some rpm tags are present
#############################################################################

import calendar
import os
import re
import time
try:
    from urlparse import urlparse
except ImportError:  # Python 3
    from urllib.parse import urlparse

import rpm

import rpmlint.AbstractCheck as AbstractCheck
import rpmlint.Config as Config
import rpmlint.FilesCheck as FilesCheck
import rpmlint.Pkg as Pkg
from rpmlint.Filter import addDetails, printError, printInfo, printWarning


_use_enchant = Config.getOption("UseEnchant", None)
if _use_enchant or _use_enchant is None:
    try:
        import enchant
        import enchant.checker
    except ImportError:
        enchant = None
else:
    enchant = None
del _use_enchant

DEFAULT_VALID_LICENSES = (
    # OSI approved licenses, http://www.opensource.org/licenses/ (unversioned,
    # trailing "license" dropped based on fuzzy logic, and in well-known cases,
    # the abbreviation used instead of the full name, but list kept sorted by
    # the full name).  Updated 2010-02-01.
    'Academic Free License',
    'Adaptive Public License',
    'AGPLv3',  # Affero GNU Public License
    'AGPLv3+',  # Affero GNU Public License
    'Apache License',
    'Apache Software License',
    'Apple Public Source License',
    'Artistic',
    'Attribution Assurance License',
    'BSD',
    'Boost Software License',
    'Computer Associates Trusted Open Source License',
    'CDDL',  # Common Development and Distribution License
    'Common Public Attribution License',
    'CUA Office Public License',
    'EU DataGrid Software License',
    'Eclipse Public License',
    'Educational Community License',
    'Eiffel Forum License',
    'Entessa Public License',
    'European Union Public License',
    'Fair License',
    'Frameworx License',
    'GPLv1',
    'GPLv1+',
    'GPLv2',
    'GPLv2+',
    'GPLv3',
    'GPLv3+',
    'LGPLv2',
    'LGPLv2+',
    'LGPLv3',
    'LGPLv3+',
    'Historical Permission Notice and Disclaimer',
    'IBM Public License',
    'IPA Font License',
    'ISC License',
    'Lucent Public License',
    'Microsoft Public License',
    'Microsoft Reciprocal License',
    'MirOS License',
    'MIT',
    'Motosoto License',
    'MPL',  # Mozilla Public License
    'Multics License',
    'NASA Open Source Agreement',
    'Naumen Public License',
    'Nethack General Public License',
    'Nokia Open Source License',
    'Non-profit Open Software License',
    'NTP License',
    'OCLC Research Public License',
    'OFL',  # Open Font License
    'Open Group Test Suite License',
    'Open Software License',
    'PHP License',
    'Python license',  # CNRI Python License
    'Python Software Foundation License',
    'QPL',  # Qt Public License
    'RealNetworks Public Source License',
    'Reciprocal Public License',
    'Ricoh Source Code Public License',
    'Simple Public License',
    'Sleepycat License',
    'Sun Public License',
    'Sybase Open Watcom Public License',
    'University of Illinois/NCSA Open Source License',
    'Vovida Software License',
    'W3C License',
    'wxWindows Library License',
    'X.Net License',
    'Zope Public License',
    'zlib/libpng License',
    # Creative commons licenses, http://creativecommons.org/licenses/:
    'Creative Commons Attribution',
    'Creative Commons Attribution-NoDerivs',
    'Creative Commons Attribution-NonCommercial-NoDerivs',
    'Creative Commons Attribution-NonCommercial',
    'Creative Commons Attribution-NonCommercial-ShareAlike',
    'Creative Commons Attribution-ShareAlike',
    # Others:
    'Design Public License',  # ???
    'FSFAP',  # FSF All Permissive license
    'GFDL',  # GNU Free Documentation License
    'LaTeX Project Public License',
    'OpenContent License',
    'Open Publication License',
    'Public Domain',
    'Ruby License',
    'SIL Open Font License',
    # Non open source licences:
    'Charityware',
    'Commercial',
    'Distributable',
    'Freeware',
    'Non-distributable',
    'Proprietary',
    'Shareware',
)

BAD_WORDS = {
    'alot': 'a lot',
    'accesnt': 'accent',
    'accelleration': 'acceleration',
    'accessable': 'accessible',
    'accomodate': 'accommodate',
    'acess': 'access',
    'acording': 'according',
    'additionaly': 'additionally',
    'adress': 'address',
    'adresses': 'addresses',
    'adviced': 'advised',
    'albumns': 'albums',
    'alegorical': 'allegorical',
    'algorith': 'algorithm',
    'allpication': 'application',
    'altough': 'although',
    'alows': 'allows',
    'amoung': 'among',
    'amout': 'amount',
    'analysator': 'analyzer',
    'ang': 'and',
    'appropiate': 'appropriate',
    'arraival': 'arrival',
    'artifical': 'artificial',
    'artillary': 'artillery',
    'attemps': 'attempts',
    'automatize': 'automate',
    'automatized': 'automated',
    'automatizes': 'automates',
    'auxilliary': 'auxiliary',
    'availavility': 'availability',
    'availble': 'available',
    'avaliable': 'available',
    'availiable': 'available',
    'backgroud': 'background',
    'baloons': 'balloons',
    'becomming': 'becoming',
    'becuase': 'because',
    'cariage': 'carriage',
    'challanges': 'challenges',
    'changable': 'changeable',
    'charachters': 'characters',
    'charcter': 'character',
    'choosen': 'chosen',
    'colorfull': 'colorful',
    'comand': 'command',
    'commerical': 'commercial',
    'comminucation': 'communication',
    'commoditiy': 'commodity',
    'compability': 'compatibility',
    'compatability': 'compatibility',
    'compatable': 'compatible',
    'compatibiliy': 'compatibility',
    'compatibilty': 'compatibility',
    'compleatly': 'completely',
    'complient': 'compliant',
    'compres': 'compress',
    'containes': 'contains',
    'containts': 'contains',
    'contence': 'contents',
    'continous': 'continuous',
    'contraints': 'constraints',
    'convertor': 'converter',
    'convinient': 'convenient',
    'cryptocraphic': 'cryptographic',
    'deamon': 'daemon',
    'debians': 'Debian\'s',
    'decompres': 'decompress',
    'definate': 'definite',
    'definately': 'definitely',
    'dependancies': 'dependencies',
    'dependancy': 'dependency',
    'dependant': 'dependent',
    'developement': 'development',
    'developped': 'developed',
    'deveolpment': 'development',
    'devided': 'divided',
    'dictionnary': 'dictionary',
    'diplay': 'display',
    'disapeared': 'disappeared',
    'dissapears': 'disappears',
    'documentaion': 'documentation',
    'docuentation': 'documentation',
    'documantation': 'documentation',
    'dont': 'don\'t',
    'easilly': 'easily',
    'ecspecially': 'especially',
    'edditable': 'editable',
    'editting': 'editing',
    'eletronic': 'electronic',
    'enchanced': 'enhanced',
    'encorporating': 'incorporating',
    'enlightnment': 'enlightenment',
    'enterily': 'entirely',
    'enviroiment': 'environment',
    'environement': 'environment',
    'excellant': 'excellent',
    'exlcude': 'exclude',
    'exprimental': 'experimental',
    'extention': 'extension',
    'failuer': 'failure',
    'familar': 'familiar',
    'fatser': 'faster',
    'fetaures': 'features',
    'forse': 'force',
    'fortan': 'fortran',
    'framwork': 'framework',
    'fuction': 'function',
    'fuctions': 'functions',
    'functionnality': 'functionality',
    'functonality': 'functionality',
    'functionaly': 'functionally',
    'futhermore': 'furthermore',
    'generiously': 'generously',
    'grahical': 'graphical',
    'grahpical': 'graphical',
    'grapic': 'graphic',
    'guage': 'gauge',
    'halfs': 'halves',
    'heirarchically': 'hierarchically',
    'helpfull': 'helpful',
    'hierachy': 'hierarchy',
    'hierarchie': 'hierarchy',
    'howver': 'however',
    'implemantation': 'implementation',
    'incomming': 'incoming',
    'incompatabilities': 'incompatibilities',
    'indended': 'intended',
    'indendation': 'indentation',
    'independant': 'independent',
    'informatiom': 'information',
    'initalize': 'initialize',
    'inofficial': 'unofficial',
    'integreated': 'integrated',
    'integrety': 'integrity',
    'integrey': 'integrity',
    'intendet': 'intended',
    'interchangable': 'interchangeable',
    'intermittant': 'intermittent',
    'jave': 'java',
    'langage': 'language',
    'langauage': 'language',
    'langugage': 'language',
    'lauch': 'launch',
    'lesstiff': 'lesstif',
    'libaries': 'libraries',
    'licenceing': 'licencing',
    'loggin': 'login',
    'logile': 'logfile',
    'loggging': 'logging',
    'mandrivalinux': 'Mandriva Linux',
    'maintainance': 'maintenance',
    'maintainence': 'maintenance',
    'makeing': 'making',
    'managable': 'manageable',
    'manoeuvering': 'maneuvering',
    'ment': 'meant',
    'modulues': 'modules',
    'monochromo': 'monochrome',
    'multidimensionnal': 'multidimensional',
    'navagating': 'navigating',
    'nead': 'need',
    'neccesary': 'necessary',
    'neccessary': 'necessary',
    'necesary': 'necessary',
    'nescessary': 'necessary',
    'noticable': 'noticeable',
    'optionnal': 'optional',
    'orientied': 'oriented',
    'pacakge': 'package',
    'pachage': 'package',
    'packacge': 'package',
    'packege': 'package',
    'packge': 'package',
    'pakage': 'package',
    'particularily': 'particularly',
    'persistant': 'persistent',
    'plattform': 'platform',
    'ploting': 'plotting',
    'posible': 'possible',
    'powerfull': 'powerful',
    'prefered': 'preferred',
    'prefferably': 'preferably',
    'prepaired': 'prepared',
    'princliple': 'principle',
    'priorty': 'priority',
    'proccesors': 'processors',
    'proces': 'process',
    'processsing': 'processing',
    'processessing': 'processing',
    'progams': 'programs',
    'programers': 'programmers',
    'programm': 'program',
    'programms': 'programs',
    'promps': 'prompts',
    'pronnounced': 'pronounced',
    'prononciation': 'pronunciation',
    'pronouce': 'pronounce',
    'protcol': 'protocol',
    'protocoll': 'protocol',
    'recieve': 'receive',
    'recieved': 'received',
    'redircet': 'redirect',
    'regulamentations': 'regulations',
    'remoote': 'remote',
    'repectively': 'respectively',
    'replacments': 'replacements',
    'requiere': 'require',
    'runnning': 'running',
    'safly': 'safely',
    'savable': 'saveable',
    'searchs': 'searches',
    'separatly': 'separately',
    'seperate': 'separate',
    'seperately': 'separately',
    'seperatly': 'separately',
    'serveral': 'several',
    'setts': 'sets',
    'similiar': 'similar',
    'simliar': 'similar',
    'speach': 'speech',
    'standart': 'standard',
    'staically': 'statically',
    'staticly': 'statically',
    'succesful': 'successful',
    'succesfully': 'successfully',
    'suplied': 'supplied',
    'suport': 'support',
    'suppport': 'support',
    'supportin': 'supporting',
    'synchonized': 'synchronized',
    'syncronize': 'synchronize',
    'syncronizing': 'synchronizing',
    'syncronus': 'synchronous',
    'syste': 'system',
    'sythesis': 'synthesis',
    'taht': 'that',
    'throught': 'through',
    'useable': 'usable',
    'usefull': 'useful',
    'usera': 'users',
    'usetnet': 'Usenet',
    'utilites': 'utilities',
    'utillities': 'utilities',
    'utilties': 'utilities',
    'utiltity': 'utility',
    'utitlty': 'utility',
    'variantions': 'variations',
    'varient': 'variant',
    'verson': 'version',
    'vicefersa': 'vice-versa',
    'yur': 'your',
    'wheter': 'whether',
    'wierd': 'weird',
    'xwindows': 'X'
}

CAPITALIZED_IGNORE_LIST = (
    'jQuery', 'openSUSE', 'wxWidgets', 'a', 'an', 'uWSGI')

DEFAULT_INVALID_REQUIRES = ('^is$', '^not$', '^owned$', '^by$', '^any$',
                            '^package$', r'^libsafe\.so\.')

VALID_GROUPS = Config.getOption('ValidGroups', None)
if VALID_GROUPS is None:  # get defaults from rpm package only if it's not set
    VALID_GROUPS = Pkg.get_default_valid_rpmgroups()
VALID_LICENSES = Config.getOption('ValidLicenses', DEFAULT_VALID_LICENSES)
INVALID_REQUIRES = map(re.compile, Config.getOption('InvalidRequires', DEFAULT_INVALID_REQUIRES))
packager_regex = re.compile(Config.getOption('Packager'))
changelog_version_regex = re.compile(r'[^>]([^ >]+)\s*$')
changelog_text_version_regex = re.compile(r'^\s*-\s*((\d+:)?[\w\.]+-[\w\.]+)')
release_ext = Config.getOption('ReleaseExtension')
extension_regex = release_ext and re.compile(release_ext)
use_version_in_changelog = Config.getOption('UseVersionInChangelog', True)
devel_number_regex = re.compile(r'(.*?)([0-9.]+)(_[0-9.]+)?-devel')
lib_devel_number_regex = re.compile(r'^lib(.*?)([0-9.]+)(_[0-9.]+)?-devel')
invalid_url_regex = re.compile(Config.getOption('InvalidURL'), re.IGNORECASE)
lib_package_regex = re.compile(r'(?:^(?:compat-)?lib.*?(\.so.*)?|libs?[\d-]*)$', re.IGNORECASE)
leading_space_regex = re.compile(r'^\s+')
license_regex = re.compile(r'\(([^)]+)\)|\s(?:and|or|AND|OR)\s')
invalid_version_regex = re.compile(r'([0-9](?:rc|alpha|beta|pre).*)', re.IGNORECASE)
# () are here for grouping purpose in the regexp
forbidden_words_regex = re.compile(r'(%s)' % Config.getOption('ForbiddenWords'), re.IGNORECASE)
valid_buildhost_regex = re.compile(Config.getOption('ValidBuildHost'))
use_epoch = Config.getOption('UseEpoch', False)
use_utf8 = Config.getOption('UseUTF8', Config.USEUTF8_DEFAULT)
max_line_len = Config.getOption('MaxLineLength', 79)
tag_regex = re.compile(r'^((?:Auto(?:Req|Prov|ReqProv)|Build(?:Arch(?:itectures)?|Root)|(?:Build)?Conflicts|(?:Build)?(?:Pre)?Requires|Copyright|(?:CVS|SVN)Id|Dist(?:ribution|Tag|URL)|DocDir|(?:Build)?Enhances|Epoch|Exclu(?:de|sive)(?:Arch|OS)|Group|Icon|License|Name|No(?:Patch|Source)|Obsoletes|Packager|Patch\d*|Prefix(?:es)?|Provides|(?:Build)?Recommends|Release|RHNPlatform|Serial|Source\d*|(?:Build)?Suggests|Summary|(?:Build)?Supplements|(?:Bug)?URL|Vendor|Version)(?:\([^)]+\))?:)\s*\S', re.IGNORECASE)
punct = '.,:;!?'
sentence_break_regex = re.compile(r'(^|[.:;!?])\s*$')
so_dep_regex = re.compile(r'\.so(\.[0-9a-zA-z]+)*(\([^)]*\))*$')
# we assume that no rpm packages existed before rpm itself existed...
oldest_changelog_timestamp = calendar.timegm(time.strptime("1995-01-01", "%Y-%m-%d"))

private_so_paths = set()
for path in ('%perl_archlib', '%perl_vendorarch', '%perl_sitearch',
             '%python_sitearch', '%python2_sitearch', '%python3_sitearch',
             '%ruby_sitearch', '%php_extdir'):
    epath = rpm.expandMacro(path)
    if epath and epath != path:
        private_so_paths.add(epath)
        private_so_paths.add(re.sub(r'/lib64(?=/|$)', '/lib', epath))
        private_so_paths.add(re.sub(r'/lib(?=/|$)', '/lib64', epath))

_enchant_checkers = {}


def spell_check(pkg, str, fmt, lang, ignored):

    dict_found = True
    warned = set()
    if enchant:
        if lang == 'C':
            lang = 'en_US'

        checker = _enchant_checkers.get(lang)
        if not checker and lang not in _enchant_checkers:
            try:
                checker = enchant.checker.SpellChecker(
                    lang, filters=[enchant.tokenize.EmailFilter,
                                   enchant.tokenize.URLFilter,
                                   enchant.tokenize.WikiWordFilter])
            except enchant.DictNotFoundError:
                printInfo(pkg, 'enchant-dictionary-not-found', lang)
                pass
            _enchant_checkers[lang] = checker

        if checker:
            # squeeze whitespace to ease leading context check
            checker.set_text(re.sub(r'\s+', ' ', str))
            if use_utf8:
                uppername = Pkg.to_unicode(pkg.header[rpm.RPMTAG_NAME]).upper()
            else:
                uppername = pkg.name.upper()
            upperparts = uppername.split('-')
            if lang.startswith('en'):
                ups = [x + "'S" for x in upperparts]
                upperparts.extend(ups)
            for err in checker:

                # Skip already warned and ignored words
                if err.word in warned or err.word in ignored:
                    continue

                # Skip all capitalized words that do not start a sentence
                if err.word[0].isupper() and not \
                        sentence_break_regex.search(checker.leading_context(3)):
                    continue

                upperword = err.word.upper()

                # Skip all uppercase words
                if err.word == upperword:
                    continue

                # Skip errors containing package name or equal to a
                # "component" of it, case insensitively
                if uppername in upperword or upperword in upperparts:
                    continue

                # Work around enchant's digit tokenizing behavior:
                # http://github.com/rfk/pyenchant/issues/issue/3
                if checker.leading_context(1).isdigit() or \
                        checker.trailing_context(1).isdigit():
                    continue

                # Warn and suggest
                sug = ', '.join(checker.suggest()[:3])
                if sug:
                    sug = '-> %s' % sug
                printWarning(pkg, 'spelling-error', fmt % lang, err.word, sug)
                warned.add(err.word)

        else:
            dict_found = False

    if not enchant or not dict_found:
        for seq in str.split():
            for word in re.split(r'[^a-z]+', seq.lower()):
                if len(word) == 0:
                    continue
                correct = BAD_WORDS.get(word)
                if not correct:
                    continue
                if word[0] == '\'':
                    word = word[1:]
                if word[-1] == '\'':
                    word = word[:-1]
                if word in warned or word in ignored:
                    continue
                printWarning(pkg, 'spelling-error', fmt % lang, word, '->',
                             correct)
                warned.add(word)


class TagsCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'TagsCheck')

    def _unexpanded_macros(self, pkg, tagname, value, is_url=False):
        if not value:
            return
        if not isinstance(value, (list, tuple)):
            value = [value]
        for val in value:
            for match in AbstractCheck.macro_regex.findall(val):
                # Do not warn about %XX URL escapes
                if is_url and re.match('^%[0-9A-F][0-9A-F]$', match, re.I):
                    continue
                printWarning(pkg, 'unexpanded-macro', tagname, match)

    def check(self, pkg):

        packager = pkg[rpm.RPMTAG_PACKAGER]
        if packager:
            self._unexpanded_macros(pkg, 'Packager', packager)
            if Config.getOption('Packager') and \
               not packager_regex.search(packager):
                printWarning(pkg, 'invalid-packager', packager)
        else:
            printError(pkg, 'no-packager-tag')

        version = pkg[rpm.RPMTAG_VERSION]
        if version:
            self._unexpanded_macros(pkg, 'Version', version)
            res = invalid_version_regex.search(version)
            if res:
                printError(pkg, 'invalid-version', version)
        else:
            printError(pkg, 'no-version-tag')

        release = pkg[rpm.RPMTAG_RELEASE]
        if release:
            self._unexpanded_macros(pkg, 'Release', release)
            if release_ext and not extension_regex.search(release):
                printWarning(pkg, 'not-standard-release-extension', release)
        else:
            printError(pkg, 'no-release-tag')

        epoch = pkg[rpm.RPMTAG_EPOCH]
        if epoch is None:
            if use_epoch:
                printError(pkg, 'no-epoch-tag')
        else:
            if epoch > 99:
                printWarning(pkg, 'unreasonable-epoch', epoch)
            epoch = str(epoch)

        if use_epoch:
            for tag in ("obsoletes", "conflicts", "provides", "recommends",
                        "suggests", "enhances", "supplements"):
                for x in (x for x in getattr(pkg, tag)()
                          if x[1] and x[2][0] is None):
                    printWarning(pkg, 'no-epoch-in-%s' % tag,
                                 Pkg.formatRequire(*x))

        name = pkg.name
        deps = pkg.requires() + pkg.prereq()
        devel_depend = False
        is_devel = FilesCheck.devel_regex.search(name)
        is_source = pkg.isSource()
        for d in deps:
            value = Pkg.formatRequire(*d)
            if use_epoch and d[1] and d[2][0] is None and \
                    not d[0].startswith('rpmlib('):
                printWarning(pkg, 'no-epoch-in-dependency', value)
            for r in INVALID_REQUIRES:
                if r.search(d[0]):
                    printError(pkg, 'invalid-dependency', d[0])

            if d[0].startswith('/usr/local/'):
                printError(pkg, 'invalid-dependency', d[0])

            if is_source:
                if lib_devel_number_regex.search(d[0]):
                    printError(pkg, 'invalid-build-requires', d[0])
            elif not is_devel:
                if not devel_depend and FilesCheck.devel_regex.search(d[0]):
                    printError(pkg, 'devel-dependency', d[0])
                    devel_depend = True
                if not d[1]:
                    res = lib_package_regex.search(d[0])
                    if res and not res.group(1):
                        printError(pkg, 'explicit-lib-dependency', d[0])

            if d[1] == rpm.RPMSENSE_EQUAL and d[2][2] is not None:
                printWarning(pkg, 'requires-on-release', value)
            self._unexpanded_macros(pkg, 'dependency %s' % (value,), value)

        self._unexpanded_macros(pkg, 'Name', name)
        if not name:
            printError(pkg, 'no-name-tag')
        else:
            if is_devel and not is_source:
                base = is_devel.group(1)
                dep = None
                has_so = False
                for fname in pkg.files():
                    if fname.endswith('.so'):
                        has_so = True
                        break
                if has_so:
                    base_or_libs = base + '/' + base + '-libs/lib' + base
                    # try to match *%_isa as well (e.g. "(x86-64)", "(x86-32)")
                    base_or_libs_re = re.compile(
                        r'^(lib)?%s(-libs)?(\(\w+-\d+\))?$' % re.escape(base))
                    for d in deps:
                        if base_or_libs_re.match(d[0]):
                            dep = d
                            break
                    if not dep:
                        printWarning(pkg, 'no-dependency-on', base_or_libs)
                    elif version:
                        exp = (epoch, version, None)
                        sexp = Pkg.versionToString(exp)
                        if not dep[1]:
                            printWarning(pkg, 'no-version-dependency-on',
                                         base_or_libs, sexp)
                        elif dep[2][:2] != exp[:2]:
                            printWarning(pkg,
                                         'incoherent-version-dependency-on',
                                         base_or_libs,
                                         Pkg.versionToString((dep[2][0],
                                                              dep[2][1], None)),
                                         sexp)
                    res = devel_number_regex.search(name)
                    if not res:
                        printWarning(pkg, 'no-major-in-name', name)
                    else:
                        if res.group(3):
                            prov = res.group(1) + res.group(2) + '-devel'
                        else:
                            prov = res.group(1) + '-devel'

                        if prov not in (x[0] for x in pkg.provides()):
                            printWarning(pkg, 'no-provides', prov)

        # List of words to ignore in spell check
        ignored_words = set()
        for pf in pkg.files():
            ignored_words.update(pf.split('/'))
        ignored_words.update((x[0] for x in pkg.provides()))
        ignored_words.update((x[0] for x in pkg.requires()))
        ignored_words.update((x[0] for x in pkg.conflicts()))
        ignored_words.update((x[0] for x in pkg.obsoletes()))

        langs = pkg[rpm.RPMTAG_HEADERI18NTABLE]

        summary = pkg[rpm.RPMTAG_SUMMARY]
        if summary:
            if not langs:
                self._unexpanded_macros(pkg, 'Summary', Pkg.b2s(summary))
            else:
                for lang in langs:
                    self.check_summary(pkg, lang, ignored_words)
        else:
            printError(pkg, 'no-summary-tag')

        description = pkg[rpm.RPMTAG_DESCRIPTION]
        if description:
            if not langs:
                self._unexpanded_macros(pkg, '%description',
                                        Pkg.b2s(description))
            else:
                for lang in langs:
                    self.check_description(pkg, lang, ignored_words)

            if len(Pkg.b2s(description)) < len(pkg[rpm.RPMTAG_SUMMARY]):
                printWarning(pkg, 'description-shorter-than-summary')
        else:
            printError(pkg, 'no-description-tag')

        group = pkg[rpm.RPMTAG_GROUP]
        self._unexpanded_macros(pkg, 'Group', group)
        if not group:
            printError(pkg, 'no-group-tag')
        elif VALID_GROUPS and group not in VALID_GROUPS:
            printWarning(pkg, 'non-standard-group', group)

        buildhost = pkg[rpm.RPMTAG_BUILDHOST]
        self._unexpanded_macros(pkg, 'BuildHost', buildhost)
        if not buildhost:
            printError(pkg, 'no-buildhost-tag')
        elif Config.getOption('ValidBuildHost') and \
                not valid_buildhost_regex.search(buildhost):
            printWarning(pkg, 'invalid-buildhost', buildhost)

        changelog = pkg[rpm.RPMTAG_CHANGELOGNAME]
        if not changelog:
            printError(pkg, 'no-changelogname-tag')
        else:
            clt = pkg[rpm.RPMTAG_CHANGELOGTEXT]
            if use_version_in_changelog:
                ret = changelog_version_regex.search(Pkg.b2s(changelog[0]))
                if not ret and clt:
                    # we also allow the version specified as the first
                    # thing on the first line of the text
                    ret = changelog_text_version_regex.search(Pkg.b2s(clt[0]))
                if not ret:
                    printWarning(pkg, 'no-version-in-last-changelog')
                elif version and release:
                    srpm = pkg[rpm.RPMTAG_SOURCERPM] or ''
                    # only check when source name correspond to name
                    if srpm[0:-8] == '%s-%s-%s' % (name, version, release):
                        expected = [version + '-' + release]
                        if epoch is not None:  # regardless of use_epoch
                            expected[0] = str(epoch) + ':' + expected[0]
                        # Allow EVR in changelog without release extension,
                        # the extension is often a macro or otherwise dynamic.
                        if release_ext:
                            expected.append(
                                extension_regex.sub('', expected[0]))
                        if ret.group(1) not in expected:
                            if len(expected) == 1:
                                expected = expected[0]
                            printWarning(pkg, 'incoherent-version-in-changelog',
                                         ret.group(1), expected)

            if use_utf8:
                if clt:
                    changelog = changelog + clt
                for s in changelog:
                    if not Pkg.is_utf8_bytestr(s):
                        printError(pkg, 'tag-not-utf8', '%changelog')
                        break

            clt = pkg[rpm.RPMTAG_CHANGELOGTIME][0]
            if clt:
                clt -= clt % (24 * 3600)  # roll back to 00:00:00, see #246
                if clt < oldest_changelog_timestamp:
                    printWarning(pkg, 'changelog-time-overflow',
                                 time.strftime("%Y-%m-%d", time.gmtime(clt)))
                elif clt > time.time():
                    printError(pkg, 'changelog-time-in-future',
                               time.strftime("%Y-%m-%d", time.gmtime(clt)))

#         for provide_name in (x[0] for x in pkg.provides()):
#             if name == provide_name:
#                 printWarning(pkg, 'package-provides-itself')
#                 break

        def split_license(license):
            return (x.strip() for x in
                    (l for l in license_regex.split(license) if l))

        rpm_license = pkg[rpm.RPMTAG_LICENSE]
        if not rpm_license:
            printError(pkg, 'no-license')
        else:
            valid_license = True
            if rpm_license not in VALID_LICENSES:
                for l1 in split_license(rpm_license):
                    if l1 in VALID_LICENSES:
                        continue
                    for l2 in split_license(l1):
                        if l2 not in VALID_LICENSES:
                            printWarning(pkg, 'invalid-license', l2)
                            valid_license = False
            if not valid_license:
                self._unexpanded_macros(pkg, 'License', rpm_license)

        for tag in ('URL', 'DistURL', 'BugURL'):
            if hasattr(rpm, 'RPMTAG_%s' % tag.upper()):
                url = Pkg.b2s(pkg[getattr(rpm, 'RPMTAG_%s' % tag.upper())])
                self._unexpanded_macros(pkg, tag, url, is_url=True)
                if url:
                    (scheme, netloc) = urlparse(url)[0:2]
                    if not scheme or not netloc or "." not in netloc or \
                            scheme not in ('http', 'https', 'ftp') or \
                            (Config.getOption('InvalidURL') and
                             invalid_url_regex.search(url)):
                        printWarning(pkg, 'invalid-url', tag, url)
                    else:
                        self.check_url(pkg, tag, url)
                elif tag == 'URL':
                    printWarning(pkg, 'no-url-tag')

        obs_names = [x[0] for x in pkg.obsoletes()]
        prov_names = [x[0] for x in pkg.provides()]

        for o in (x for x in obs_names if x not in prov_names):
            printWarning(pkg, 'obsolete-not-provided', o)
        for o in pkg.obsoletes():
            value = Pkg.formatRequire(*o)
            self._unexpanded_macros(pkg, 'Obsoletes %s' % (value,), value)

        # TODO: should take versions, <, <=, =, >=, > into account here
        #       https://bugzilla.redhat.com/460872
        useless_provides = set()
        for p in prov_names:
            if (prov_names.count(p) != 1 and
                    not p.startswith('debuginfo(') and
                    p not in useless_provides):
                useless_provides.add(p)
        for p in sorted(useless_provides):
            printError(pkg, 'useless-provides', p)

        for tagname, items in (
                ('Provides', pkg.provides()),
                ('Conflicts', pkg.conflicts()),
                ('Obsoletes', pkg.obsoletes()),
                ('Supplements', pkg.supplements()),
                ('Suggests', pkg.suggests()),
                ('Enhances', pkg.enhances()),
                ('Recommends', pkg.recommends())):
            for p in items:
                value = Pkg.formatRequire(*p)
                self._unexpanded_macros(pkg, '%s %s' % (tagname, value), value)

        obss = pkg.obsoletes()
        if obss:
            provs = pkg.provides()
            for prov in provs:
                for obs in obss:
                    if Pkg.rangeCompare(obs, prov):
                        printWarning(pkg, 'self-obsoletion',
                                     '%s obsoletes %s' %
                                     (Pkg.formatRequire(*obs),
                                      Pkg.formatRequire(*prov)))

        expfmt = rpm.expandMacro("%{_build_name_fmt}")
        if pkg.isSource():
            # _build_name_fmt often (always?) ends up not outputting src/nosrc
            # as arch for source packages, do it ourselves
            expfmt = re.sub(r'(?i)%\{?ARCH\b\}?', pkg.arch, expfmt)
        expected = pkg.header.sprintf(expfmt).split("/")[-1]
        basename = os.path.basename(pkg.filename)
        if basename != expected:
            printWarning(pkg, 'non-coherent-filename', basename, expected)

        for tag in ('Distribution', 'DistTag', 'ExcludeArch', 'ExcludeOS',
                    'Vendor'):
            if hasattr(rpm, 'RPMTAG_%s' % tag.upper()):
                res = Pkg.b2s(pkg[getattr(rpm, 'RPMTAG_%s' % tag.upper())])
                self._unexpanded_macros(pkg, tag, res)

        for path in private_so_paths:
            for fname, pkgfile in pkg.files().items():
                if fname.startswith(path):
                    for prov in pkgfile.provides:
                        if so_dep_regex.search(prov[0]):
                            printWarning(pkg, "private-shared-object-provides",
                                         fname, Pkg.formatRequire(*prov))

    def check_description(self, pkg, lang, ignored_words):
        description = pkg.langtag(rpm.RPMTAG_DESCRIPTION, lang)
        if use_utf8:
            if not Pkg.is_utf8_bytestr(description):
                printError(pkg, 'tag-not-utf8', '%description', lang)
            description = Pkg.to_unicode(description)
        else:
            description = Pkg.b2s(description)
        self._unexpanded_macros(pkg, '%%description -l %s' % lang, description)
        spell_check(pkg, description, '%%description -l %s', lang,
                    ignored_words)
        for l in description.splitlines():
            if len(l) > max_line_len:
                printError(pkg, 'description-line-too-long', lang, l)
            res = forbidden_words_regex.search(l)
            if res and Config.getOption('ForbiddenWords'):
                printWarning(pkg, 'description-use-invalid-word', lang,
                             res.group(1))
            res = tag_regex.search(l)
            if res:
                printWarning(pkg, 'tag-in-description', lang, res.group(1))

    def check_summary(self, pkg, lang, ignored_words):
        summary = pkg.langtag(rpm.RPMTAG_SUMMARY, lang)
        if use_utf8:
            if not Pkg.is_utf8_bytestr(summary):
                printError(pkg, 'tag-not-utf8', 'Summary', lang)
            summary = Pkg.to_unicode(summary)
        else:
            summary = Pkg.b2s(summary)
        self._unexpanded_macros(pkg, 'Summary(%s)' % lang, summary)
        spell_check(pkg, summary, 'Summary(%s)', lang, ignored_words)
        if '\n' in summary:
            printError(pkg, 'summary-on-multiple-lines', lang)
        if (summary[0] != summary[0].upper() and
                summary.partition(' ')[0] not in CAPITALIZED_IGNORE_LIST):
            printWarning(pkg, 'summary-not-capitalized', lang, summary)
        if summary[-1] == '.':
            printWarning(pkg, 'summary-ended-with-dot', lang, summary)
        if len(summary) > max_line_len:
            printError(pkg, 'summary-too-long', lang, summary)
        if leading_space_regex.search(summary):
            printError(pkg, 'summary-has-leading-spaces', lang, summary)
        res = forbidden_words_regex.search(summary)
        if res and Config.getOption('ForbiddenWords'):
            printWarning(pkg, 'summary-use-invalid-word', lang, res.group(1))
        if pkg.name:
            sepchars = r'[\s%s]' % punct
            res = re.search(r'(?:^|\s)(%s)(?:%s|$)' %
                            (re.escape(pkg.name), sepchars),
                            summary, re.IGNORECASE | re.UNICODE)
            if res:
                printWarning(pkg, 'name-repeated-in-summary', lang,
                             res.group(1))


# Create an object to enable the auto registration of the test
check = TagsCheck()

# Add information about checks
addDetails(
'summary-too-long',
'The "Summary:" must not exceed %d characters.' % max_line_len,

'invalid-version',
'''The version string must not contain the pre, alpha, beta or rc suffixes
because when the final version will be out, you will have to use an Epoch tag
to make the package upgradable. Instead put it in the release tag, prefixed
with something you have control over.''',

'spelling-error',
'''The value of this tag appears to be misspelled. Please double-check.''',

'no-packager-tag',
'''There is no Packager tag in your package. You have to specify a packager
using the Packager tag. Ex: Packager: John Doe <john.doe@example.com>.''',

'invalid-packager',
'''The packager email must end with an email compatible with the Packager
option of rpmlint. Please change it and rebuild your package.''',

'no-version-tag',
'''There is no Version tag in your package. You have to specify a version using
the Version tag.''',

'no-release-tag',
'''There is no Release tag in your package. You have to specify a release using
the Release tag.''',

'not-standard-release-extension',
'Your release tag must match the regular expression ' + release_ext + '.',

'no-name-tag',
'''There is no Name tag in your package. You have to specify a name using the
Name tag.''',

'non-coherent-filename',
'''The file which contains the package should be named
<NAME>-<VERSION>-<RELEASE>.<ARCH>.rpm.''',

'no-dependency-on',
'''
''',

'incoherent-version-dependency-on',
'''
''',

'no-version-dependency-on',
'''
''',

'no-major-in-name',
'''The major number of the library isn't included in the package's name.
''',

'description-shorter-than-summary',
'''The package description should be longer than the summary. Be a bit more
verbose, please.''',

'no-provides',
'''Your library package doesn't provide the -devel name without the major
version included.''',

'no-summary-tag',
'''There is no Summary tag in your package. You have to describe your package
using this tag. To insert it, just insert a tag 'Summary'.''',

'summary-on-multiple-lines',
'''Your summary must fit on one line. Please make it shorter and rebuild the
package.''',

'summary-not-capitalized',
'''Summary doesn't begin with a capital letter.''',

'summary-ended-with-dot',
'''Summary ends with a dot.''',

'summary-has-leading-spaces',
'''Summary begins with whitespace which will waste space when displayed.''',

'no-description-tag',
'''The description of the package is empty or missing. To add it, insert a
%description section in your spec file, add a textual description of the
package after it, and rebuild the package.''',

'description-line-too-long',
'''Your description lines must not exceed %d characters. If a line is exceeding
this number, cut it to fit in two lines.''' % max_line_len,

'tag-in-description',
'''Something that looks like a tag was found in the package's description.
This may indicate a problem where the tag was not actually parsed as a tag
but just textual description content, thus being a no-op.  Verify if this is
the case, and move the tag to a place in the specfile where %description
won't fool the specfile parser, and rebuild the package.''',

'no-group-tag',
'''There is no Group tag in your package. You have to specify a valid group
in your spec file using the Group tag.''',

'non-standard-group',
'''The value of the Group tag in the package is not valid.  Valid groups are:
"%s".''' % '", "'.join(VALID_GROUPS),

'no-changelogname-tag',
'''There is no %changelog tag in your spec file. To insert it, just insert a
'%changelog' in your spec file and rebuild it.''',

'no-version-in-last-changelog',
'''The latest changelog entry doesn't contain a version. Please insert the
version that is coherent with the version of the package and rebuild it.''',

'incoherent-version-in-changelog',
'''The latest entry in %changelog contains a version identifier that is not
coherent with the epoch:version-release tuple of the package.''',

'changelog-time-overflow',
'''The timestamp of the latest entry in %changelog is suspiciously far away in
the past; it is possible that it is actually so much in the future that it
has overflowed rpm's timestamp representation.''',

'changelog-time-in-future',
'''The timestamp of the latest entry in %changelog is in the future.''',

'no-license',
'''There is no License tag in your spec file. You have to specify one license
for your program (eg. GPL). To insert this tag, just insert a 'License' in
your specfile.''',

'invalid-license',
'''The value of the License tag was not recognized.  Known values are:
"%s".''' % '", "'.join(VALID_LICENSES),

'obsolete-not-provided',
'''If a package is obsoleted by a compatible replacement, the obsoleted package
should also be provided in order to not cause unnecessary dependency breakage.
If the obsoleting package is not a compatible replacement for the old one,
leave out the Provides.''',

'invalid-dependency',
'''An invalid dependency has been detected. It usually means that the build of
the package was buggy.''',

'no-epoch-tag',
'''There is no Epoch tag in your package. You have to specify an epoch using
the Epoch tag.''',

'unreasonable-epoch',
'''The value of your Epoch tag is unreasonably large (> 99).''',

'no-epoch-in-dependency',
'''Your package contains a versioned dependency without an Epoch.''',

'devel-dependency',
'''Your package has a dependency on a devel package but it's not a devel
package itself.''',

'invalid-build-requires',
'''Your source package contains a dependency not compliant with the lib64
naming. This BuildRequires dependency will not be resolved on lib64 platforms
(eg. amd64).''',

'explicit-lib-dependency',
'''You must let rpm find the library dependencies by itself. Do not put
unneeded explicit Requires: tags.''',

'useless-provides',
'''This package provides 2 times the same capacity. It should only provide it
once.''',

'tag-not-utf8',
'''The character encoding of the value of this tag is not UTF-8.''',

'requires-on-release',
'''This rpm requires a specific release of another package.''',

'no-url-tag',
'''The URL tag is missing. Please add a http or ftp link to the project location.''',

'name-repeated-in-summary',
'''The name of the package is repeated in its summary.  This is often redundant
information and looks silly in various programs' output.  Make the summary
brief and to the point without including redundant information in it.''',

'enchant-dictionary-not-found',
'''A dictionary for the Enchant spell checking library is not available for
the language given in the info message.  Spell checking will proceed with
rpmlint's built-in implementation for localized tags in this language.
For better spell checking results in this language, install the appropriate
dictionary that Enchant will use for this language, often for example
hunspell-* or aspell-*.''',

'self-obsoletion',
'''The package obsoletes itself.  This is known to cause errors in various
tools and should thus be avoided, usually by using appropriately versioned
Obsoletes and/or Provides and avoiding unversioned ones.''',

'unexpanded-macro',
'''This tag contains something that looks like an unexpanded macro; this is
often the sign of a misspelling. Please check your specfile.''',

'private-shared-object-provides',
'''A shared object soname provides is provided by a file in a path from which
other packages should not directly load shared objects from.  Such shared
objects should thus not be depended on and they should not result in provides
in the containing package.  Get rid of the provides if appropriate, for example
by filtering it out during build.  Note that in some cases this may require
disabling rpmbuild's internal dependency generator.''',
)

for i in ("obsoletes", "conflicts", "provides", "recommends", "suggests",
          "enhances", "supplements"):
    addDetails("no-epoch-in-%s" % i,
               "Your package contains a versioned %s entry without an Epoch."
               % i.capitalize())

# TagsCheck.py ends here
