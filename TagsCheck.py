#############################################################################
# File		: TagsCheck.py
# Package	: rpmlint
# Author	: Frederic Lepied
# Created on	: Tue Sep 28 00:03:24 1999
# Version	: $Id$
# Purpose	: Check a package to see if some rpm tags are present
#############################################################################

from Filter import *
import AbstractCheck
import rpm
import string
import re
import Config

DEFAULT_VALID_GROUPS=(
    'Accessibility',
    'System/Servers',
    'System/Kernel and hardware',
    'System/Libraries',
    'System/XFree86',
    'System/Fonts/Console',
    'System/Fonts/True type',
    'System/Fonts/Type1',
    'System/Fonts/X11 bitmap',
    'System/Base',
    'System/Configuration/Hardware',
    'System/Configuration/Packaging',
    'System/Configuration/Networking',
    'System/Configuration/Printing',
    'System/Configuration/Boot and Init',
    'System/Configuration/Other',
    'System/Internationalization',
    'Development/Kernel',
    'Development/Databases',
    'Development/Perl',
    'Development/Python',
    'Development/C',
    'Development/C++',
    'Development/Java',
    'Development/GNOME and GTK+',
    'Development/KDE and Qt',
    'Development/Other',
    'Sciences/Astronomy',
    'Sciences/Biology',
    'Sciences/Chemistry',
    'Sciences/Computer science',
    'Sciences/Geosciences',
    'Sciences/Mathematics',
    'Sciences/Physics',
    'Sciences/Other',
    'Communications',
    'Databases',
    'Editors',
    'Emulators',
    'Games/Adventure',
    'Games/Arcade',
    'Games/Boards',
    'Games/Cards',
    'Games/Puzzles',
    'Games/Sports',
    'Games/Strategy',
    'Games/Other',
    'Toys',
    'Archiving/Compression',
    'Archiving/Cd burning',
    'Archiving/Backup',
    'Archiving/Other',
    'Monitoring',
    'Sound',
    'Graphics',
    'Video',
    'Networking/File transfer',
    'Networking/IRC',
    'Networking/Instant messaging',
    'Networking/Chat',
    'Networking/News',
    'Networking/Mail',
    'Networking/WWW',
    'Networking/Remote access',
    'Networking/Other',
    'Office',
    'Publishing',
    'Terminals',
    'Shells',
    'File tools',
    'Text tools',
    'Graphical desktop/GNOME',
    'Graphical desktop/Icewm',
    'Graphical desktop/FVWM based',
    'Graphical desktop/KDE',
    'Graphical desktop/Sawfish',
    'Graphical desktop/WindowMaker',
    'Graphical desktop/Enlightenment',
    'Graphical desktop/Other',
    'Books/Howtos',
    'Books/Faqs',
    'Books/Computer books',
    'Books/Litterature',
    'Books/Other'
    )

# liste grabbed from www.opensource.org/licenses

DEFAULT_VALID_LICENSES = (
    'GPL',
    'LGPL',
    'GFDL',
    'OPL',
    'Artistic',
    'BSD',
    'MIT',
    'QPL',
    'MPL',
    'IBM Public License',
    'Apache License',
    'PHP License',
    'Public Domain',
    'Modified CNRI Open Source License',
    'zlib License',
    'CVW License',
    'Ricoh Source Code Public License',
    'Python license',
    'Vovida Software License',
    'Sun Internet Standards Source License',
    'Intel Open Source License',
    'Jabber Open Source License',
    'Nokia Open Source License',
    'Sleepycat License',
    'Nethack General Public License',
    'Common Public License',
    'Apple Public Source License',
    'X.Net License',
    'Sun Public License',
    'Eiffel Forum License',
    'W3C License',
    'Zope Public License',
    # non open source licences:
    'Proprietary',
    'Freeware',
    'Shareware',
    'Charityware'
    )

DEFAULT_PACKAGER = '@mandrakesoft.com|bugs@linux-mandrake.com|https://qa.mandrakesoft.com|http://www.mandrakeexpert.com'

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
DEFAULT_FORBIDDEN_WORDS_REGEX='Linux.?Mandrake|Mandrake[^ ]*Linux'
DEFAULT_VALID_BUILDHOST='\.mandrakesoft\.com$|\.mandrake\.org$'
DEFAULT_INVALID_REQUIRES=('^is$', '^not$', '^owned$', '^by$', '^any$', '^package$', '^libsafe\.so\.')

distribution=Config.getOption("Distribution", "Mandrake Linux")
VALID_GROUPS=Config.getOption('ValidGroups', DEFAULT_VALID_GROUPS)
VALID_LICENSES=Config.getOption('ValidLicenses', DEFAULT_VALID_LICENSES)
INVALID_REQUIRES=map(lambda x: re.compile(x), Config.getOption('InvalidRequires', DEFAULT_INVALID_REQUIRES))
packager_regex=re.compile(Config.getOption('Packager', DEFAULT_PACKAGER))
basename_regex=re.compile('/?([^/]+)$')
changelog_version_regex=re.compile('[^>]([^ >]+)\s*$')
release_ext=Config.getOption('ReleaseExtension', 'mdk')
extension_regex=release_ext and re.compile(release_ext + '$')
use_version_in_changelog=Config.getOption('UseVersionInChangelog', 1)
devel_regex=re.compile('(.*)-devel')
devel_number_regex=re.compile('(.*?)([0-9.]+)(_[0-9.]+)?-devel')
capital_regex=re.compile('[0-9A-Z]')
url_regex=re.compile('^(ftp|http|https)://')
so_regex=re.compile('\.so$')
leading_space_regex=re.compile('^\s+')
invalid_version_regex=re.compile('([0-9](?:rc|alpha|beta|pre).*)', re.IGNORECASE)
forbidden_words_regex=re.compile('(' + Config.getOption('ForbiddenWords', DEFAULT_FORBIDDEN_WORDS_REGEX) + ')', re.IGNORECASE)
valid_buildhost_regex=re.compile(Config.getOption('ValidBuildHost', DEFAULT_VALID_BUILDHOST))
epoch_regex=re.compile('^[0-9]+:')
use_epoch=Config.getOption('UseEpoch', 0)

def spell_check(pkg, str, tagname):
    for seq in string.split(str, ' '):
        for word in re.split('[^a-z]+', string.lower(seq)):
            if len(word) > 0:
                try:
                    if word[0] == '\'':
                        word=word[1:]
                    if word[-1] == '\'':
                        word=word[:-1]                
                    correct=BAD_WORDS[word]
                    printWarning(pkg, 'spelling-error-in-' + tagname, word, correct)
                except KeyError:
                    pass

class TagsCheck(AbstractCheck.AbstractCheck):
    
    def __init__(self):
	AbstractCheck.AbstractCheck.__init__(self, 'TagsCheck')

    def check(self, pkg):

        packager=pkg[rpm.RPMTAG_PACKAGER]
        if not packager:
	    printError(pkg, 'no-packager-tag')
        elif not packager_regex.search(packager):
            printWarning(pkg, 'invalid-packager', packager)
            
	version=pkg[rpm.RPMTAG_VERSION]
	if not version:
	    printError(pkg, 'no-version-tag')
        else:
            res=invalid_version_regex.search(version)
            if res:
                printError(pkg, 'invalid-version', version)
                
        release=pkg[rpm.RPMTAG_RELEASE]
	if not release:
	    printError(pkg, 'no-release-tag')
        elif release_ext and not extension_regex.search(release):
            printWarning(pkg, 'not-standard-release-extension', release)

        epoch=pkg[rpm.RPMTAG_EPOCH]
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

        deps=pkg.requires() + pkg.prereq()
        for d in deps:
            if use_epoch and d[1] and d[0][0:7] != 'rpmlib(' and not epoch_regex.search(d[1]):
                printWarning(pkg, 'no-epoch-in-dependency', d[0] + ' ' + d[1])
            for r in INVALID_REQUIRES:
                if r.search(d[0]):
                    printError(pkg, 'invalid-dependency', d[0])

	name=pkg[rpm.RPMTAG_NAME]
	if not name:
	    printError(pkg, 'no-name-tag')
	else:
            res=(not pkg.isSource()) and devel_regex.search(name)
            if res:
                base=res.group(1)
                dep=None
                has_so=0
                for f in pkg.files().keys():
                    if so_regex.search(f):
                        has_so=1
                        break
                if has_so:
                    for d in deps:
                        if d[0] == base:
                            dep=d
                            break
                    if not dep:
                        printWarning(pkg, 'no-dependency-on', base)
                    elif version:
                        if use_epoch:
                            expected=str(epoch) + ":" + version
                        else:
                            expected=version
                        if dep[1][:len(expected)] != expected:
                            if dep[1] != '':
                                printWarning(pkg, 'incoherent-version-dependency-on', base, dep[1], expected)
                            else:
                                printWarning(pkg, 'no-version-dependency-on', base, expected)
                    res=devel_number_regex.search(name)
                    if not res:
                        printWarning(pkg, 'no-major-in-name', name)
                    else:
                        if res.group(3):
                            prov=res.group(1) + res.group(2) + '-devel'
                        else:
                            prov=res.group(1) + '-devel'
                            
                        if not prov in map(lambda x: x[0], pkg.provides()):
                            printWarning(pkg, 'no-provides', prov)
                    
	summary=pkg[rpm.RPMTAG_SUMMARY]
	if not summary:
	    printError(pkg, 'no-summary-tag')
	else:
            spell_check(pkg, summary, 'summary')
            if string.find(summary, '\n') != -1:
                printError(pkg, 'summary-on-multiple-lines')
            if not capital_regex.search(summary[0]):
                printWarning(pkg, 'summary-not-capitalized', summary)
            if len(summary) >= 80:
                printError(pkg, 'summary-too-long', summary)
            if leading_space_regex.search(summary):
                printError(pkg, 'summary-has-leading-spaces', summary)
            res=forbidden_words_regex.search(summary)
            if res:
                printWarning(pkg, 'summary-use-invalid-word', res.group(1))

        description=pkg[rpm.RPMTAG_DESCRIPTION]
	if not description:
	    printError(pkg, 'no-description-tag')
        else:
            spell_check(pkg, description, 'description')
            for l in string.split(description, "\n"):
                if len(l) >= 80:
                    printError(pkg, 'description-line-too-long', l)
                res=forbidden_words_regex.search(l)
                if res:
                    printWarning(pkg, 'description-use-invalid-word', res.group(1))
                
                    
	group=pkg[rpm.RPMTAG_GROUP]
        if not group:
	    printError(pkg, 'no-group-tag')
	else:
	    if not group in VALID_GROUPS:
		printWarning(pkg, 'non-standard-group', group)

        buildhost=pkg[rpm.RPMTAG_BUILDHOST]
        if not buildhost:
            printError(pkg, 'no-buildhost-tag')
        else:
            if not valid_buildhost_regex.search(buildhost):
                printWarning(pkg, 'invalid-buildhost', buildhost)
                
	changelog=pkg[rpm.RPMTAG_CHANGELOGNAME]
        if not changelog:
	    printError(pkg, 'no-changelogname-tag')
        elif use_version_in_changelog and not pkg.isSource():
            ret=changelog_version_regex.search(changelog[0])
            if not ret:
                printWarning(pkg, 'no-version-in-last-changelog')
            elif version and release:
                srpm=pkg[rpm.RPMTAG_SOURCERPM]
                # only check when source name correspond to name
                if srpm[0:-8] == '%s-%s-%s' % (name, version, release):
                    expected=version + '-' + release
                    if use_epoch and epoch is not None:
                        expected=str(epoch) + ':' + expected
                    if expected != ret.group(1):
                        printWarning(pkg, 'incoherent-version-in-changelog', ret.group(1), expected)

#         provides=pkg.provides()
#         for (provide_name, provide_version, provide_flags) in provides:
#             if name == provide_name:
#                 printWarning(pkg, 'package-provides-itself')
#                 break

        license=pkg[rpm.RPMTAG_LICENSE]
        if not license:
            printError(pkg, 'no-license')
        else:
            if license not in VALID_LICENSES:
                licenses=re.split('(?:[- ]like|/|ish|[- ]style|[- ]Style|and|or|&|\s|-)+', license)
                for l in licenses:
                    if l != '' and not l in VALID_LICENSES:
                        printWarning(pkg, 'invalid-license', license)
                        break

        url=pkg[rpm.RPMTAG_URL]
        if url and url != 'none':
            if not url_regex.search(url):
                printWarning(pkg, 'invalid-url', url)
        else:
            printWarning(pkg, 'no-url-tag')

        obs=map(lambda x: x[0], pkg.obsoletes())
        provs=map(lambda x: x[0], pkg.provides())
        for o in obs:
            if not o in provs:
                printError(pkg, 'obsolete-not-provided', o)

        if pkg.isNoSource():
            arch='nosrc'
        elif pkg.isSource():
            arch='src'
        else:
            arch=pkg[rpm.RPMTAG_ARCH]

        expected='%s-%s-%s.%s.rpm' % (name, version, release, arch)
        basename=string.split(pkg.filename, '/')[-1]
        if basename != expected:
            printWarning(pkg, 'non-coherent-filename', basename)

# Create an object to enable the auto registration of the test
check=TagsCheck()

# Add information about checks
if Config.info:
    addDetails(
'summary-too-long',
'The "Summary:" must not exceed 80 characters.',

'invalid-version',
'''The version string must not contain the pre, alpha, beta or rc suffixes because
when the final version will be out, you will have to use an Epoch tag to make
you package upgradable. Instead put it in the release tag like 0.alpha8.1''' + release_ext + '.',

'spelling-error-in-description',
'''You made a mispelling in the Description. Please double-check.''',

'spelling-error-in-summary',
'''You made a mispelling in the Summary. Please double-check.''',

'no-packager-tag',
'''There is no Packager tag in your package. You have to specify a packager using
the Packager tag. Ex: Packager: Christian Belisle <cbelisle@mandrakesoft.com>.''',

'invalid-packager',
'''The packager email must finish with @mandrakesoft.com or must be bugs@linux-mandrake.com.
Please change it and rebuild your package.''',

'no-version-tag',
'''There is no Version tag in your package. You have to specify a version using the
Version tag.''',

'no-release-tag',
'''There is no Release tag in your package. You have to specify a release using the
Release tag.''',

'not-standard-release-extension',
'Your release number must finish with ' + release_ext + ' and must be valid.',

'no-name-tag',
'''There is no Name tag in your package. You have to specify a name using the Name tag.''',

'non-coherent-filename',
'''The file which contains the package should be named <NAME>-<VERSION>-<RELEASE>.<ARCH>.rpm.''',

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
'''The major number of the library isn't contained in the package name.
''',

'no-provides',
'''Your library package doesn't provide the -devel name without the major version
included.''',

'no-summary-tag',
'''There is no Summary tag in your package. You have to describe your package
using this tag. To insert it, just insert a tag 'Summary'.''',

'summary-on-multiple-lines',
'''Your summary must fit on one line. Please make it shorter and rebuilt your package.''',

'summary-not-capitalized',
'''Summary doesn't begin with a capital letter.''',

'summary-has-leading-spaces',
'''Summary begins with spaces and that will waste space when displayed.''',

'no-description-tag',
'''There is no %description tag in your spec file. To insert it, just insert a '%tag' in
your spec file and rebuild it.''',

'description-line-too-long',
'''Your description lines must no exceed 80 characters. If a line is exceeding this number,
cut it to fit in two lines.''',

'no-group-tag',
'''There is no Group tag in your package. You have to specify a valid group
in your spec file using the Group tag.''',

'non-standard-group',
'''The group specified in your spec file is not valid. To find a valid group,
please refer to the ''' + distribution + ' RPM documentation.''',

'no-changelogname-tag',
'''There is no %changelog tag in your spec file. To insert it, just insert a '%changelog' in
your spec file and rebuild it.''',

'no-version-in-last-changelog',
'''The last changelog entry doesn't contain a version. Please insert the coherent version and
rebuild your package.''',

'incoherent-version-in-changelog',
'''Your last entry in %changelog contains a version that is not coherent with the current
version of your package.''',

'no-license',
'''There is no License tag in your spec file. You have to specify one license for your
program (ie GPL). To insert this tag, just insert a 'License' in your file.''',

'invalid-license',
'''The license you specified is invalid. The valid licenses are:

-GPL					-LGPL
-Artistic				-BSD
-MIT					-QPL
-MPL					-IBM Public License
-Apache License				-PHP License
-Public Domain				-Modified CNRI Open Source License
-zlib License				-CVW License
-Ricoh Source Code Public License	-Python license
-Vovida Software License		-Sun Internet Standards Source License
-Intel Open Source License		-Jabber Open Source License

if the license is near an existing one, you can use '<license> style'.''',

'invalid-url',
'''Your URL is not valid. It must begin with http, https or ftp.''',

'obsolete-not-provided',
'''The obsoleted package must also be provided to allow a clean upgrade
and not to break depencencies.''',

'invalid-dependency',
'''An invalid dependency has been detected. It usually means that the build of the
package was buggy.''',

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

)
    
# TagsCheck.py ends here
