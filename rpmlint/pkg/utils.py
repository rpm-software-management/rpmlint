import bz2
from collections import namedtuple
import contextlib
import gzip
import lzma
import re

try:
    import magic
    has_magic = True
except ImportError:
    has_magic = False
import rpm
import zstandard as zstd


DepInfo = namedtuple('DepInfo', ('name', 'flags', 'version'))

# 64: RPMSENSE_PREREQ is 0 with rpm 4.4..4.7, we want 64 here in order
# to do the right thing with those versions and packages built with other
# rpm versions
PREREQ_FLAG = (rpm.RPMSENSE_PREREQ or 64) | rpm.RPMSENSE_SCRIPT_PRE | \
    rpm.RPMSENSE_SCRIPT_POST | rpm.RPMSENSE_SCRIPT_PREUN | \
    rpm.RPMSENSE_SCRIPT_POSTUN

SCRIPT_TAGS = [
    (rpm.RPMTAG_PREIN, rpm.RPMTAG_PREINPROG, '%pre'),
    (rpm.RPMTAG_POSTIN, rpm.RPMTAG_POSTINPROG, '%post'),
    (rpm.RPMTAG_PREUN, rpm.RPMTAG_PREUNPROG, '%preun'),
    (rpm.RPMTAG_POSTUN, rpm.RPMTAG_POSTUNPROG, '%postun'),
    (rpm.RPMTAG_TRIGGERSCRIPTS, rpm.RPMTAG_TRIGGERSCRIPTPROG, '%trigger'),
    (rpm.RPMTAG_PRETRANS, rpm.RPMTAG_PRETRANSPROG, '%pretrans'),
    (rpm.RPMTAG_POSTTRANS, rpm.RPMTAG_POSTTRANSPROG, '%posttrans'),
    (rpm.RPMTAG_VERIFYSCRIPT, rpm.RPMTAG_VERIFYSCRIPTPROG, '%verifyscript'),
    # file triggers: rpm >= 4.12.90
    (getattr(rpm, 'RPMTAG_FILETRIGGERSCRIPTS', 5066),
     getattr(rpm, 'RPMTAG_FILETRIGGERSCRIPTPROG', 5067),
     '%filetrigger'),
    (getattr(rpm, 'RPMTAG_TRANSFILETRIGGERSCRIPTS', 5076),
     getattr(rpm, 'RPMTAG_TRANSFILETRIGGERSCRIPTPROG', 5077),
     '%transfiletrigger'),
]

RPM_SCRIPTLETS = ('pre', 'post', 'preun', 'postun', 'pretrans', 'posttrans',
                  'trigger', 'triggerin', 'triggerprein', 'triggerun',
                  'triggerpostun', 'verifyscript', 'filetriggerin',
                  'filetrigger', 'filetriggerun', 'filetriggerpostun',
                  'transfiletriggerin', 'transfiletrigger',
                  'transfiletriggerun', 'transfiletriggerun',
                  'transfiletriggerpostun')


gzip_regex = re.compile(r'\.t?gz?$')
bz2_regex = re.compile(r'\.t?bz2?$')
xz_regex = re.compile(r'\.(t[xl]z|xz|lzma)$')
zst_regex = re.compile(r'\.zst$')


def catcmd(fname):
    """Get a 'cat' command that handles possibly compressed files."""
    fname = str(fname)
    cat = 'gzip -dcf'
    if bz2_regex.search(fname):
        cat = 'bzip2 -dcf'
    elif xz_regex.search(fname):
        cat = 'xz -dc'
    elif zst_regex.search(fname):
        cat = 'zstd -dc'
    return cat


def compression_algorithm(fname):
    """Return compression algorithm based on filename if known, None otherwise."""
    fname = str(fname)
    if gzip_regex.search(fname):
        return gzip
    if bz2_regex.search(fname):
        return bz2
    if xz_regex.search(fname):
        return lzma
    if zst_regex.search(fname):
        return zstd
    return None


def is_utf8(fname):
    compression = compression_algorithm(fname)
    if compression is None:
        with open(fname, 'rb') as f:
            return is_utf8_bytestr(f.read())

    with compression.open(fname, 'rb') as f:
        try:
            return is_utf8_bytestr(f.read())
        except OSError:
            return True


def is_utf8_bytestr(s):
    """Returns True whether the given text is UTF-8.
    Due to changes in rpm, needs to handle both bytes and unicode."""
    if not isinstance(s, (bytes, str)):
        unexpected = type(s).__name__
        raise TypeError(f'Expected str/bytes, not {unexpected}')

    try:
        if isinstance(s, bytes):
            s.decode('utf-8')
    except UnicodeError:
        return False

    return True


def has_forbidden_controlchars(val):
    if isinstance(val, (str, bytes)):
        string = val
        if isinstance(val, bytes):
            val = memoryview(val)
        for c in val:
            if isinstance(c, str):
                c = ord(c)
            if c < 32 and (c not in (9, 10, 13)):
                return string
    if isinstance(val, (tuple, list)):
        for item in val:
            return has_forbidden_controlchars(item)
    return False


# from yum 3.2.27, rpmUtils.miscutils, with rpmlint modifications
def compareEVR(evr1, evr2):
    (e1, v1, r1) = evr1
    (e2, v2, r2) = evr2
    # return 1: a is newer than b
    # 0: a and b are the same version
    # -1: b is newer than a
    # rpmlint mod: don't stringify None epochs to 'None' strings
    if e1 is not None:
        e1 = str(e1)
    v1 = str(v1)
    r1 = str(r1)
    if e2 is not None:
        e2 = str(e2)
    v2 = str(v2)
    r2 = str(r2)
    rc = rpm.labelCompare((e1, v1, r1), (e2, v2, r2))
    return rc


# from yum 3.2.27, rpmUtils.miscutils, with rpmlint modifications
def rangeCompare(reqtuple, provtuple):
    """returns true if provtuple satisfies reqtuple"""
    (reqn, reqf, (reqe, reqv, reqr)) = reqtuple
    (n, f, (e, v, r)) = provtuple
    if reqn != n:
        return 0

    # unversioned satisfies everything
    if not f or not reqf:
        return 1

    # and you thought we were done having fun
    # if the requested release is left out then we have
    # to remove release from the package prco to make sure the match
    # is a success - ie: if the request is EQ foo 1:3.0.0 and we have
    # foo 1:3.0.0-15 then we have to drop the 15 so we can match
    if reqr is None:
        r = None
    # rpmlint mod: don't mess with provided Epoch, doing so breaks e.g.
    # 'Requires: foo < 1.0' should not be satisfied by 'Provides: foo = 1:0.5'
    # if reqe is None:
    #    e = None
    if reqv is None:  # just for the record if ver is None then we're going to segfault
        v = None

    # if we just require foo-version, then foo-version-* will match
    if r is None:
        reqr = None

    rc = compareEVR((e, v, r), (reqe, reqv, reqr))

    # does not match unless
    if rc >= 1:
        if reqf in ['GT', 'GE', 4, 12]:
            return 1
        if reqf in ['EQ', 8] and f in ['LE', 10, 'LT', 2]:
            return 1
        if reqf in ['LE', 'LT', 'EQ', 10, 2, 8] and f in ['LE', 'LT', 10, 2]:
            return 1

    if rc == 0:
        if reqf in ['GT', 4] and f in ['GT', 'GE', 4, 12]:
            return 1
        if reqf in ['GE', 12] and f in ['GT', 'GE', 'EQ', 'LE', 4, 12, 8, 10]:
            return 1
        if reqf in ['EQ', 8] and f in ['EQ', 'GE', 'LE', 8, 12, 10]:
            return 1
        if reqf in ['LE', 10] and f in ['EQ', 'LE', 'LT', 'GE', 8, 10, 2, 12]:
            return 1
        if reqf in ['LT', 2] and f in ['LE', 'LT', 10, 2]:
            return 1
    if rc <= -1:
        if reqf in ['GT', 'GE', 'EQ', 4, 12, 8] and f in ['GT', 'GE', 4, 12]:
            return 1
        if reqf in ['LE', 'LT', 10, 2]:
            return 1

    return 0


# from yum 3.2.23, rpmUtils.miscutils, with rpmlint modifications
def formatRequire(name, flags, evr):
    s = name

    if flags and flags & (rpm.RPMSENSE_LESS | rpm.RPMSENSE_GREATER |
                          rpm.RPMSENSE_EQUAL):
        s = s + ' '
        if flags & rpm.RPMSENSE_LESS:
            s = s + '<'
        if flags & rpm.RPMSENSE_GREATER:
            s = s + '>'
        if flags & rpm.RPMSENSE_EQUAL:
            s = s + '='
        s = f'{s} {versionToString(evr)}'
    return s


def versionToString(evr):
    if not isinstance(evr, (list, tuple)):
        # assume string
        return evr
    ret = ''
    if evr[0] is not None and evr[0] != '':
        ret += str(evr[0]) + ':'
    if evr[1] is not None:
        ret += evr[1]
        if evr[2] is not None and evr[2] != '':
            ret += '-' + evr[2]
    return ret


# from yum 3.2.23, rpmUtils.miscutils, with some rpmlint modifications
def stringToVersion(verstring):
    if verstring in (None, ''):
        return (None, None, None)
    epoch = None
    i = verstring.find(':')
    if i != -1:
        with contextlib.suppress(ValueError):
            # garbage in epoch, ignore it
            epoch = int(verstring[:i])
    i += 1
    j = verstring.find('-', i)
    if j != -1:
        if verstring[i:j] == '':
            version = None
        else:
            version = verstring[i:j]
        release = verstring[j + 1:]
    else:
        if verstring[i:] == '':
            version = None
        else:
            version = verstring[i:]
        release = None
    return (epoch, version, release)


def parse_deps(line):
    """
    Parse provides/requires/conflicts/obsoletes line to list of
    (name, flags, (epoch, version, release)) tuples.
    """

    prcos = []
    tokens = re.split(r'[\s,]+', line.strip())

    # Drop line continuation backslash in multiline macro definition (for
    # spec file parsing), e.g.
    # [...] \
    # Obsoletes: foo-%1 <= 1.0.0 \
    # [...] \
    # (yes, this is an ugly hack and we probably have other problems with
    #  multiline macro definitions elsewhere...)
    if tokens[-1] == '\\':
        del tokens[-1]

    prco = []
    while tokens:
        token = tokens.pop(0)
        if not token:
            # skip empty tokens
            continue

        plen = len(prco)

        if plen == 0:
            prco.append(token)

        elif plen == 1:
            flags = 0
            if token[0] in ('=', '<', '<=', '>', '>='):
                # versioned, flags
                if '=' in token:
                    flags |= rpm.RPMSENSE_EQUAL
                if '<' in token:
                    flags |= rpm.RPMSENSE_LESS
                if '>' in token:
                    flags |= rpm.RPMSENSE_GREATER
                prco.append(flags)
            else:
                # no flags following name, treat as unversioned, add and reset
                prco.extend((flags, (None, None, None)))
                prcos.append(tuple(prco))
                prco = [token]

        elif plen == 2:
            # last token of versioned one, add and reset
            prco.append(stringToVersion(token))
            prcos.append(tuple(prco))
            prco = []

    plen = len(prco)
    if plen:
        if plen == 1:
            prco.extend((0, (None, None, None)))
        elif plen == 2:
            prco.append((None, None, None))
        prcos.append(tuple(prco))

    return prcos


def _get_magic_libmagic(path):
    return magic.detect_from_filename(path).name


def _get_magic_python_magic(path):
    return magic.from_file(path)


def get_magic(path):
    # python-magic & libmagic compatibility code
    # https://github.com/ahupp/python-magic/blob/master/COMPAT.md
    detect_magic = _get_magic_python_magic
    if not hasattr(magic, 'from_file'):
        # libmagic python bindings
        detect_magic = _get_magic_libmagic

    try:
        return detect_magic(path)
    except (ValueError, FileNotFoundError):
        return ''
