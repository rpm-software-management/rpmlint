# These defaults are here just because of limitation of configobj which can't
# read multiline string as default value for verification.
# Checking the code it has syntax of 'default="""' whereas the configobj parser
# actually can start only on values that directly start with triple quotes.
# They are named as DEFAULT_<theoption>
DEFAULTS = {}
DICT_DEFAULTS = {}
DEFAULTS['Checks'] = """
    DistributionCheck
    TagsCheck
    BinariesCheck
    ConfigCheck
    FilesCheck
    DocFilesCheck
    FHSCheck
    SignatureCheck
    I18NCheck
    MenuCheck
    PostCheck
    InitScriptCheck
    SourceCheck
    SpecCheck
    NamingPolicyCheck
    ZipCheck
    PamCheck
    RpmFileCheck
    MenuXDGCheck
    AppDataCheck
"""
DEFAULTS['ExtraMenuNeeds'] = """
    gnome
    icewm
    kde
    wmaker
"""
DEFAULTS['ValidMenuSections'] = """
    Office/Accessories
    Office/Address Books
    Office/Communications/Fax
    Office/Communications/PDA
    Office/Communications/Phone
    Office/Communications/Other
    Office/Drawing
    Office/Graphs
    Office/Presentations
    Office/Publishing
    Office/Spreadsheets
    Office/Tasks Management
    Office/Time Management
    Office/Wordprocessors
    Office/Other
    Internet/Chat
    Internet/File Transfer
    Internet/Instant Messaging
    Internet/Mail
    Internet/News
    Internet/Remote Access
    Internet/Video Conference
    Internet/Web Browsers
    Internet/Web Editors
    Internet/Other
    Multimedia/Graphics
    Multimedia/Sound
    Multimedia/Video
    Multimedia/Other
    System/Archiving/Backup
    System/Archiving/CD Burning
    System/Archiving/Compression
    System/Archiving/Other
    System/Configuration/Boot and Init
    System/Configuration/GNOME
    System/Configuration/Hardware
    System/Configuration/KDE
    System/Configuration/Networking
    System/Configuration/Packaging
    System/Configuration/Printing
    System/Configuration/Users
    System/Configuration/Other
    System/File Tools
    System/Monitoring
    System/Session/Windowmanagers
    System/Terminals
    System/Text Tools
    System/Other
    More Applications/Accessibility
    More Applications/Communications
    More Applications/Databases
    More Applications/Development/Code Generators
    More Applications/Development/Development Environments
    More Applications/Development/Interpreters
    More Applications/Development/Tools
    More Applications/Development/Other
    More Applications/Documentation
    More Applications/Editors
    More Applications/Education/Economy
    More Applications/Education/Geography
    More Applications/Education/History
    More Applications/Education/Languages
    More Applications/Education/Literature
    More Applications/Education/Sciences
    More Applications/Education/Sports
    More Applications/Education/Other
    More Applications/Emulators
    More Applications/Finances
    More Applications/Games/Adventure
    More Applications/Games/Arcade
    More Applications/Games/Boards
    More Applications/Games/Cards
    More Applications/Games/Puzzles
    More Applications/Games/Sports
    More Applications/Games/Strategy
    More Applications/Games/Toys
    More Applications/Games/Other
    More Applications/Sciences/Artificial Intelligence
    More Applications/Sciences/Astronomy
    More Applications/Sciences/Biology
    More Applications/Sciences/Chemistry
    More Applications/Sciences/Computer Science
    More Applications/Sciences/Data visualization
    More Applications/Sciences/Electricity
    More Applications/Sciences/Geosciences
    More Applications/Sciences/Image Processing
    More Applications/Sciences/Mathematics
    More Applications/Sciences/Numerical Analysis
    More Applications/Sciences/Parallel Computing
    More Applications/Sciences/Physics
    More Applications/Sciences/Robotics
    More Applications/Sciences/Other
    More Applications/Other
"""
DEFAULTS['InvalidRequires'] = """
    ^is$
    ^not$
    ^owned$
    ^by$
    ^any$
    ^package$
    r'^libsafe\.so\.'
"""
DEFAULTS['DisallowedDirs'] = """
    /home
    /mnt
    /opt
    /tmp
    /usr/local
    /usr/tmp
    /var/local
    /var/lock
    /var/run
    /var/tmp
"""
DEFAULTS['StandardGroups'] = """
    root
    bin
    daemon
    adm
    lp
    sync
    shutdown
    halt
    mail
    news
    uucp
    man
    nobody
"""
DEFAULTS['StandardUsers'] = """
    root
    bin
    daemon
    adm
    lp
    sync
    shutdown
    halt
    mail
    news
    uucp
    operator
    man
    nobody
"""
DEFAULTS['SystemLibPaths'] = """
    /lib
    /usr/lib
    /usr/X11R6/lib
    /lib64
    /usr/lib64
    /usr/X11R6/lib64
"""
DEFAULTS['ValidEmptyShells'] = """
    /sbin/ldconfig
"""
DEFAULTS['ValidShells'] = """
    <lua>
    /bin/sh
    /bin/bash
    /sbin/sash
    /usr/bin/perl
    /sbin/ldconfig
"""
DEFAULTS['ValidLicenses'] = """
    # OSI approved licenses, http://www.opensource.org/licenses/ (unversioned,
    # trailing 'license' dropped based on fuzzy logic, and in well-known cases,
    # the abbreviation used instead of the full name, but list kept sorted by
    # the full name).  Updated 2010-02-01.
    Academic Free License
    Adaptive Public License
    AGPLv3
    AGPLv3+
    Apache License
    Apache Software License
    Apple Public Source License
    Artistic
    Attribution Assurance License
    BSD
    Boost Software License
    Computer Associates Trusted Open Source License
    CDDL
    Common Public Attribution License
    CUA Office Public License
    EU DataGrid Software License
    Eclipse Public License
    Educational Community License
    Eiffel Forum License
    Entessa Public License
    European Union Public License
    Fair License
    Frameworx License
    GPLv1
    GPLv1+
    GPLv2
    GPLv2+
    GPLv3
    GPLv3+
    LGPLv2
    LGPLv2+
    LGPLv3
    LGPLv3+
    Historical Permission Notice and Disclaimer
    IBM Public License
    IPA Font License
    ISC License
    Lucent Public License
    Microsoft Public License
    Microsoft Reciprocal License
    MirOS License
    MIT
    Motosoto License
    MPL
    Multics License
    NASA Open Source Agreement
    Naumen Public License
    Nethack General Public License
    Nokia Open Source License
    Non-profit Open Software License
    NTP License
    OCLC Research Public License
    OFL
    Open Group Test Suite License
    Open Software License
    PHP License
    Python license
    Python Software Foundation License
    QPL
    RealNetworks Public Source License
    Reciprocal Public License
    Ricoh Source Code Public License
    Simple Public License
    Sleepycat License
    Sun Public License
    Sybase Open Watcom Public License
    University of Illinois/NCSA Open Source License
    Vovida Software License
    W3C License
    wxWindows Library License
    X.Net License
    Zope Public License
    zlib/libpng License
    # Creative commons licenses, http://creativecommons.org/licenses/:
    Creative Commons Attribution
    Creative Commons Attribution-NoDerivs
    Creative Commons Attribution-NonCommercial-NoDerivs
    Creative Commons Attribution-NonCommercial
    Creative Commons Attribution-NonCommercial-ShareAlike
    Creative Commons Attribution-ShareAlike
    # Others:
    Design Public License
    FSFAP
    GFDL
    LaTeX Project Public License
    OpenContent License
    Open Publication License
    Public Domain
    Ruby License
    SIL Open Font License
    # Non open source licences:
    Charityware
    Commercial
    Distributable
    Freeware
    Non-distributable
    Proprietary
    Shareware
"""
DICT_DEFAULTS['IconPath'] = {
    '/usr/share/icons/': {
        'path': '/usr/share/icons/',
        'type': 'normal',
    },
    '/usr/share/icons/mini': {
        'path': '/usr/share/icons/mini',
        'type': 'mini',
    },
    '/usr/share/icons/large': {
        'path': '/usr/share/icons/large',
        'type': 'large',
    },
}
DICT_DEFAULTS['MenuLaunchers'] = {
    'kdesu': {
        'regexp': '(?:/usr/bin/)?kdesu',
        'binaries': ['/usr/bin/kdesu', 'kdesu'],
    },
    'x11_clanapp': {
        'regexp': '(?:/usr/bin/)?launch_x11_clanapp',
        'binaries': ['/usr/bin/launch_x11_clanapp', 'clanlib', 'libclanlib0'],
    },
    'soundwrapper': {
        'regexp': '(?:/usr/bin/)?soundwrapper',
        'binaries': None,
    },
}
DICT_DEFAULTS['DanglingSymlinkExceptions'] = {}
