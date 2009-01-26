# -*- coding: utf-8 -*-
#############################################################################
# File          : TagsCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 00:03:24 1999
# Version       : $Id$
# Purpose       : Check a package to see if some rpm tags are present
#############################################################################

import os
import re

import rpm

from Filter import printError, printWarning
import AbstractCheck
import Config
import FilesCheck
import Pkg


DEFAULT_VALID_LICENSES = (
    # OSI approved licenses, http://www.opensource.org/licenses/ (unversioned,
    # trailing "license" dropped based on fuzzy logic, and in well-known cases,
    # the abbreviation used instead of the full name, but list kept sorted by
    # the full name).  Updated 2009-01-23.
    'Academic Free License',
    'Adaptive Public License',
    'Apache License',
    'Apache Software License',
    'Apple Public Source License',
    'Artistic',
    'Attribution Assurance License',
    'BSD',
    'Computer Associates Trusted Open Source License',
    'CDDL', # Common Development and Distribution License
    'CPL', # Common Public License
    'CUA Office Public License',
    'EU DataGrid Software License',
    'Eclipse Public License',
    'Educational Community License',
    'Eiffel Forum License',
    'Entessa Public License',
    'Fair License',
    'Frameworx License',
    'GNU Affero GPLv3',
    'GNU Affero GPLv3+',
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
    'Intel Open Source License',
    'ISC License',
    'Jabber Open Source License',
    'Lucent Public License',
    'Microsoft Public License',
    'Microsoft Reciprocal License',
    'MIT',
    'CVW License', # MITRE Collaborative Virtual Workspace License
    'Motosoto License',
    'MPL', # Mozilla Public License
    'Multics License',
    'NASA Open Source Agreement',
    'Naumen Public License',
    'Nethack General Public License',
    'Nokia Open Source License',
    'Non-profit Open Software License',
    'NTP License',
    'OCLC Research Public License',
    'Open Group Test Suite License',
    'Open Software License',
    'PHP License',
    'Python license', # CNRI Python License
    'Python Software Foundation License',
    'QPL', # Qt Public License
    'RealNetworks Public Source License',
    'Reciprocal Public License',
    'Ricoh Source Code Public License',
    'Sleepycat License',
    'Sun Industry Standards Source License',
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
    'Design Public License', # ???
    'GFDL', # GNU Free Documentation License
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

DEFAULT_INVALID_REQUIRES = ('^is$', '^not$', '^owned$', '^by$', '^any$', '^package$', '^libsafe\.so\.')

VALID_GROUPS = Config.getOption('ValidGroups', Pkg.get_default_valid_rpmgroups())
VALID_LICENSES = Config.getOption('ValidLicenses', DEFAULT_VALID_LICENSES)
INVALID_REQUIRES = map(lambda x: re.compile(x), Config.getOption('InvalidRequires', DEFAULT_INVALID_REQUIRES))
packager_regex = re.compile(Config.getOption('Packager'))
changelog_version_regex = re.compile('[^>]([^ >]+)\s*$')
changelog_text_version_regex = re.compile('^\s*-\s*((\d+:)?[\w\.]+-[\w\.]+)')
release_ext = Config.getOption('ReleaseExtension')
extension_regex = release_ext and re.compile(release_ext)
use_version_in_changelog = Config.getOption('UseVersionInChangelog', 1)
devel_number_regex = re.compile('(.*?)([0-9.]+)(_[0-9.]+)?-devel')
lib_devel_number_regex = re.compile('^lib(.*?)([0-9.]+)(_[0-9.]+)?-devel')
url_regex = re.compile('^(ftp|http|https)://')
invalid_url_regex = re.compile(Config.getOption('InvalidURL'), re.IGNORECASE)
lib_package_regex = re.compile('(?:^(?:compat-)?lib.*?(\.so.*)?|libs?[\d-]*)$', re.IGNORECASE)
leading_space_regex = re.compile('^\s+')
license_regex = re.compile('\(([^)]+)\)|\s(?:and|or)\s')
invalid_version_regex = re.compile('([0-9](?:rc|alpha|beta|pre).*)', re.IGNORECASE)
# () are here for grouping purpose in the regexp
forbidden_words_regex = re.compile('(' + Config.getOption('ForbiddenWords') + ')', re.IGNORECASE)
valid_buildhost_regex = re.compile(Config.getOption('ValidBuildHost'))
epoch_regex = re.compile('^[0-9]+:')
use_epoch = Config.getOption('UseEpoch', 0)
use_utf8 = Config.getOption('UseUTF8', Config.USEUTF8_DEFAULT)
max_line_len = 79
tag_regex = re.compile('^((?:Auto(?:Req|Prov|ReqProv)|Build(?:Arch(?:itectures)?|Root)|(?:Build)?Conflicts|(?:Build)?(?:Pre)?Requires|Copyright|(?:CVS|SVN)Id|Dist(?:ribution|Tag|URL)|DocDir|(?:Build)?Enhances|Epoch|Exclu(?:de|sive)(?:Arch|OS)|Group|Icon|License|Name|No(?:Patch|Source)|Obsoletes|Packager|Patch\d*|Prefix(?:es)?|Provides|(?:Build)?Recommends|Release|RHNPlatform|Serial|Source\d*|(?:Build)?Suggests|Summary|(?:Build)?Supplements|URL|Vendor|Version)(?:\([^)]+\))?:)\s*\S', re.IGNORECASE)
punct = '.,:;!?'

def spell_check(pkg, str, tagname):
    for seq in str.split():
        for word in re.split('[^a-z]+', seq.lower()):
            if len(word) > 0:
                try:
                    if word[0] == '\'':
                        word = word[1:]
                    if word[-1] == '\'':
                        word = word[:-1]
                    correct = BAD_WORDS[word]
                    printWarning(pkg, 'spelling-error-in-' + tagname, word, correct)
                except KeyError:
                    pass

class TagsCheck(AbstractCheck.AbstractCheck):

    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, 'TagsCheck')

    def check(self, pkg):

        packager = pkg[rpm.RPMTAG_PACKAGER]
        if not packager:
            printError(pkg, 'no-packager-tag')
        elif Config.getOption('Packager') and not packager_regex.search(packager):
            printWarning(pkg, 'invalid-packager', packager)

        version = pkg[rpm.RPMTAG_VERSION]
        if not version:
            printError(pkg, 'no-version-tag')
        else:
            res = invalid_version_regex.search(version)
            if res:
                printError(pkg, 'invalid-version', version)

        release = pkg[rpm.RPMTAG_RELEASE]
        if not release:
            printError(pkg, 'no-release-tag')
        elif release_ext and not extension_regex.search(release):
            printWarning(pkg, 'not-standard-release-extension', release)

        epoch = pkg[rpm.RPMTAG_EPOCH]
        if epoch is None:
            if use_epoch:
                printError(pkg, 'no-epoch-tag')
        else:
            if epoch > 99:
                printWarning(pkg, 'unreasonable-epoch', epoch)

        if use_epoch:
            for o in pkg.obsoletes():
                if o[1] and not epoch_regex.search(o[1]):
                    printWarning(pkg, 'no-epoch-in-obsoletes', o[0] + ' ' + o[1])
            for c in pkg.conflicts():
                if c[1] and not epoch_regex.search(c[1]):
                    printWarning(pkg, 'no-epoch-in-conflicts', c[0] + ' ' + c[1])
            for p in pkg.provides():
                if p[1] and not epoch_regex.search(p[1]):
                    printWarning(pkg, 'no-epoch-in-provides', p[0] + ' ' + p[1])

        name = pkg.name
        deps = pkg.requires() + pkg.prereq()
        devel_depend = 0
        is_devel = FilesCheck.devel_regex.search(name)
        is_source = pkg.isSource()
        for d in deps:
            if use_epoch and d[1] and d[0][0:7] != 'rpmlib(' and not epoch_regex.search(d[1]):
                printWarning(pkg, 'no-epoch-in-dependency', d[0] + ' ' + d[1])
            for r in INVALID_REQUIRES:
                if r.search(d[0]):
                    printError(pkg, 'invalid-dependency', d[0])

            if d[0].startswith('/usr/local/'):
                printError(pkg, 'invalid-dependency', d[0])

            if not devel_depend and not is_devel and not is_source:
                if FilesCheck.devel_regex.search(d[0]):
                    printError(pkg, 'devel-dependency', d[0])
                    devel_depend = 1
            if is_source and lib_devel_number_regex.search(d[0]):
                printError(pkg, 'invalid-build-requires', d[0])
            if not is_source and not is_devel:
                res = lib_package_regex.search(d[0])
                if res and not res.group(1) and not d[1]:
                    printError(pkg, 'explicit-lib-dependency', d[0])
            if d[2] == rpm.RPMSENSE_EQUAL and d[1].find('-') != -1:
                printWarning(pkg, 'requires-on-release', d[0], d[1])
            if d[1].find('%') != -1:
                printError(pkg, 'percent-in-dependency', d[0], d[1])

        if not name:
            printError(pkg, 'no-name-tag')
        else:
            if is_devel and not is_source:
                base = is_devel.group(1)
                dep = None
                has_so = 0
                for f in pkg.files().keys():
                    if f.endswith('.so'):
                        has_so = 1
                        break
                if has_so:
                    base_or_libs = base + '/' + base + '-libs/lib' + base
                    for d in deps:
                        if d[0] == base or d[0] == base + '-libs' or d[0] == 'lib' + base:
                            dep = d
                            break
                    if not dep:
                        printWarning(pkg, 'no-dependency-on', base_or_libs)
                    elif version:
                        if epoch is not None: # regardless of use_epoch
                            expected = str(epoch) + ":" + version
                        else:
                            expected = version
                        if dep[1][:len(expected)] != expected:
                            if dep[1] != '':
                                printWarning(pkg, 'incoherent-version-dependency-on', base_or_libs, dep[1], expected)
                            else:
                                printWarning(pkg, 'no-version-dependency-on', base_or_libs, expected)
                    res = devel_number_regex.search(name)
                    if not res:
                        printWarning(pkg, 'no-major-in-name', name)
                    else:
                        if res.group(3):
                            prov = res.group(1) + res.group(2) + '-devel'
                        else:
                            prov = res.group(1) + '-devel'

                        if not prov in map(lambda x: x[0], pkg.provides()):
                            printWarning(pkg, 'no-provides', prov)

        summary = pkg[rpm.RPMTAG_SUMMARY]
        if not summary:
            printError(pkg, 'no-summary-tag')
        else:
            utf8summary = summary
            if use_utf8:
                utf8summary = Pkg.to_utf8(summary).decode('utf-8')
            spell_check(pkg, summary, 'summary')
            if summary.find('\n') != -1:
                printError(pkg, 'summary-on-multiple-lines')
            if summary[0] != summary[0].upper():
                printWarning(pkg, 'summary-not-capitalized', summary)
            if summary[-1] == '.':
                printWarning(pkg, 'summary-ended-with-dot', summary)
            if len(utf8summary) > max_line_len:
                printError(pkg, 'summary-too-long', summary)
            if leading_space_regex.search(summary):
                printError(pkg, 'summary-has-leading-spaces', summary)
            res = forbidden_words_regex.search(summary)
            if res and Config.getOption('ForbiddenWords'):
                printWarning(pkg, 'summary-use-invalid-word', res.group(1))
            if name:
                sepchars = '[\s' + punct + ']'
                res = re.search('(?:^|\s)(%s)(?:%s|$)' %
                                (re.escape(name), sepchars),
                                summary, re.IGNORECASE | re.UNICODE)
                if res:
                    printWarning(pkg, 'name-repeated-in-summary', res.group(1))
            if use_utf8 and not Pkg.is_utf8_str(summary):
                printError(pkg, 'tag-not-utf8', 'Summary')

        description = pkg[rpm.RPMTAG_DESCRIPTION]
        if not description:
            printError(pkg, 'no-description-tag')
        else:
            spell_check(pkg, description, 'description')
            for l in description.splitlines():
                utf8l = l
                if use_utf8:
                    utf8l = Pkg.to_utf8(l).decode('utf-8')
                if len(utf8l) > max_line_len:
                    printError(pkg, 'description-line-too-long', l)
                res = forbidden_words_regex.search(l)
                if res and Config.getOption('ForbiddenWords'):
                    printWarning(pkg, 'description-use-invalid-word', res.group(1))
                res = tag_regex.search(l)
                if res:
                    printWarning(pkg, 'tag-in-description', res.group(1))
            if use_utf8 and not Pkg.is_utf8_str(description):
                printError(pkg, 'tag-not-utf8', '%description')

        group = pkg[rpm.RPMTAG_GROUP]
        if not group:
            printError(pkg, 'no-group-tag')
        else:
            if VALID_GROUPS and group not in VALID_GROUPS:
                printWarning(pkg, 'non-standard-group', group)

        buildhost = pkg[rpm.RPMTAG_BUILDHOST]
        if not buildhost:
            printError(pkg, 'no-buildhost-tag')
        else:
            if Config.getOption('ValidBuildHost') and not valid_buildhost_regex.search(buildhost):
                printWarning(pkg, 'invalid-buildhost', buildhost)

        changelog = pkg[rpm.RPMTAG_CHANGELOGNAME]
        if not changelog:
            printError(pkg, 'no-changelogname-tag')
        else:
            clt = pkg[rpm.RPMTAG_CHANGELOGTEXT]
            if use_version_in_changelog:
                ret = changelog_version_regex.search(changelog[0])
                if not ret and clt:
                    # we also allow the version specified as the first
                    # thing on the first line of the text
                    ret = changelog_text_version_regex.search(clt[0])
                if not ret:
                    printWarning(pkg, 'no-version-in-last-changelog')
                elif version and release:
                    srpm = pkg[rpm.RPMTAG_SOURCERPM] or ''
                    # only check when source name correspond to name
                    if srpm[0:-8] == '%s-%s-%s' % (name, version, release):
                        expected = [version + '-' + release]
                        if epoch is not None: # regardless of use_epoch
                            expected[0] = str(epoch) + ':' + expected[0]
                        # Allow EVR in changelog without release extension,
                        # the extension is often a macro or otherwise dynamic.
                        if release_ext:
                            expected.append(extension_regex.sub('', expected[0]))
                        if ret.group(1) not in expected:
                            if len(expected) == 1: expected = expected[0]
                            printWarning(pkg, 'incoherent-version-in-changelog', ret.group(1), expected)

            if clt: changelog = changelog + clt
            if use_utf8 and not Pkg.is_utf8_str(' '.join(changelog)):
                printError(pkg, 'tag-not-utf8', '%changelog')

#         provides = pkg.provides()
#         for (provide_name, provide_version, provide_flags) in provides:
#             if name == provide_name:
#                 printWarning(pkg, 'package-provides-itself')
#                 break

        def split_license(license):
            return map(lambda x: x.strip(),
                       [l for l in license_regex.split(license) if l])

        rpm_license = pkg[rpm.RPMTAG_LICENSE]
        if not rpm_license:
            printError(pkg, 'no-license')
        else:
            if rpm_license not in VALID_LICENSES:
                for l1 in split_license(rpm_license):
                    if l1 in VALID_LICENSES:
                        continue
                    for l2 in split_license(l1):
                        if l2 not in VALID_LICENSES:
                            printWarning(pkg, 'invalid-license', l2)

        url = pkg[rpm.RPMTAG_URL]
        if url and url != 'none':
            if not url_regex.search(url):
                printWarning(pkg, 'invalid-url', url)
            elif Config.getOption('InvalidURL') and invalid_url_regex.search(url):
                printWarning(pkg, 'invalid-url', url)
        else:
            printWarning(pkg, 'no-url-tag')

        obs_names = map(lambda x: x[0], pkg.obsoletes())
        prov_names = map(lambda x: x[0], pkg.provides())

        if pkg.name in obs_names:
            printError(pkg, 'obsolete-on-name')
        for o in obs_names:
            if not o in prov_names:
                printWarning(pkg, 'obsolete-not-provided', o)
        for o in pkg.obsoletes():
            if o[1].find('%') != -1:
                printError(pkg, 'percent-in-obsoletes', o[0], o[1])

        # TODO: should take versions, <, <=, =, >=, > into account here
        #       https://bugzilla.redhat.com/460872
        useless_provides = []
        for p in prov_names:
            if prov_names.count(p) != 1:
                if p not in useless_provides:
                    useless_provides.append(p)
        for p in useless_provides:
            printError(pkg, 'useless-provides', p)

        for p in pkg.provides():
            if p[1].find('%') != -1:
                printError(pkg, 'percent-in-provides', p[0], p[1])

        for c in pkg.conflicts():
            if c[1].find('%') != -1:
                printError(pkg, 'percent-in-conflicts', c[0], c[1])

        expected = '%s-%s-%s.%s.rpm' % (name, version, release, pkg.arch)
        basename = os.path.basename(pkg.filename)
        if basename != expected:
            printWarning(pkg, 'non-coherent-filename', basename, expected)

# Create an object to enable the auto registration of the test
check = TagsCheck()

# Add information about checks
if Config.info:
    addDetails(
'summary-too-long',
'The "Summary:" must not exceed %d characters.' % max_line_len,

'invalid-version',
'''The version string must not contain the pre, alpha, beta or rc suffixes
because when the final version will be out, you will have to use an Epoch tag
to make the package upgradable. Instead put it in the release tag, prefixed
with something you have control over.''',

'spelling-error-in-description',
'''You made a misspelling in the Description. Please double-check.''',

'spelling-error-in-summary',
'''You made a misspelling in the Summary. Please double-check.''',

'no-packager-tag',
'''There is no Packager tag in your package. You have to specify a packager using
the Packager tag. Ex: Packager: John Doo <john.doo@example.com>.''',

'invalid-packager',
'''The packager email must finish with a email compatible with the Packager option
of rpmlint. Please change it and rebuild your package.''',

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

'no-provides',
'''Your library package doesn't provide the -devel name without the major version
included.''',

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
'''There is no %description tag in your spec file. To insert it, just insert a
'%description' tag in your spec file, add a textual description of the package
after it, and rebuild the package.''',

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
'''The last changelog entry doesn't contain a version. Please insert the
version that is coherent with the version of the package and rebuild it.''',

'incoherent-version-in-changelog',
'''The last entry in %changelog contains a version identifier that is not
coherent with the epoch:version-release tuple of the package.''',

'no-license',
'''There is no License tag in your spec file. You have to specify one license
for your program (eg. GPL). To insert this tag, just insert a 'License' in
your specfile.''',

'invalid-license',
'''The value of the License tag was not recognized.  Known values are:
"%s".''' % '", "'.join(VALID_LICENSES),

'invalid-url',
'''Your URL is not valid. It must begin with http, https or ftp and must no
longer contain the word mandrake.''',

'obsolete-not-provided',
'''If a package is obsoleted by a compatible replacement, the obsoleted package
should also be provided in order to not cause unnecessary dependency breakage.
If the obsoleting package is not a compatible replacement for the old one,
leave out the Provides.''',

'invalid-dependency',
'''An invalid dependency has been detected. It usually means that the build of
the package was buggy.''',

'no-epoch-tag',
'''There is no Epoch tag in your package. You have to specify an epoch using the
Epoch tag.''',

'unreasonable-epoch',
'''The value of your Epoch tag is unreasonably large (> 99).''',

'no-epoch-in-obsoletes',
'''Your package contains a versioned Obsoletes entry without an Epoch.''',

'no-epoch-in-conflicts',
'''Your package contains a versioned Conflicts entry without an Epoch.''',

'no-epoch-in-provides',
'''Your package contains a versioned Provides entry without an Epoch.''',

'no-epoch-in-dependency',
'''Your package contains a versioned dependency without an Epoch.''',

'devel-dependency',
'''Your package has a dependency on a devel package but it's not a devel
package itself.''',

'invalid-build-requires',
'''Your source package contains a dependency not compliant with the lib64 naming.
This BuildRequires dependency will not be resolved on lib64 platforms
(eg. amd64).''',

'explicit-lib-dependency',
'''You must let rpm find the library dependencies by itself. Do not put unneeded
explicit Requires: tags.''',

'useless-provides',
'''This package provides 2 times the same capacity. It should only provide it
once.''',

'obsolete-on-name',
'''A package should not obsolete itself, as it can cause weird errors in tools.''',

'tag-not-utf8',
'''The character encoding of the value of this tag is not UTF-8.''',

'requires-on-release',
'''This rpm requires a specific release of another package.''',

'percent-in-dependency',
'''This rpm has a dependency whose version part contains the '%' character.
It could be an unexpanded macro, please double check.''',

'percent-in-obsoletes',
'''This rpm has an Obsoletes whose version part contains the '%' character.
It could be an unexpanded macro, please double check.''',

'percent-in-provides',
'''This rpm has a Provides whose version part contains the '%' character.
It could be an unexpanded macro, please double check.''',

'percent-in-conflicts',
'''This rpm has a Conflicts whose version part contains the '%' character.
It could be an unexpanded macro, please double check.''',

'no-url-tag',
'''The URL tag is missing.''',

'name-repeated-in-summary',
'''The name of the package is repeated in its summary.  This is often redundant
information and looks silly in various programs' output.  Make the summary
brief and to the point without including redundant information in it.''',
)

# TagsCheck.py ends here

# Local variables:
# indent-tabs-mode: nil
# py-indent-offset: 4
# End:
# ex: ts=4 sw=4 et
