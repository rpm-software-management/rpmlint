from itertools import chain
import pathlib
import sys
import tempfile

import rpm
from rpmlint.helpers import byte_to_string, print_warning
from rpmlint.pkg import getInstalledPkgs, Pkg


class Rpmdiff(object):
    # constants
    TAGS = (rpm.RPMTAG_NAME, rpm.RPMTAG_SUMMARY,
            rpm.RPMTAG_DESCRIPTION, rpm.RPMTAG_GROUP,
            rpm.RPMTAG_LICENSE, rpm.RPMTAG_URL,
            rpm.RPMTAG_PREIN, rpm.RPMTAG_POSTIN,
            rpm.RPMTAG_PREUN, rpm.RPMTAG_POSTUN,
            rpm.RPMTAG_PRETRANS, rpm.RPMTAG_POSTTRANS)

    PRCO = ('REQUIRES', 'PROVIDES', 'CONFLICTS', 'OBSOLETES',
            'RECOMMENDS', 'SUGGESTS', 'ENHANCES', 'SUPPLEMENTS')

    # {fname : (size, mode, mtime, flags, dev, inode,
    #           nlink, state, vflags, user, group, digest)}
    __FILEIDX = [['S', 0],
                 ['M', 1],
                 ['5', 11],
                 ['D', 4],
                 ['N', 6],
                 ['L', 7],
                 ['V', 8],
                 ['U', 9],
                 ['G', 10],
                 ['F', 3],
                 ['T', 2]]

    DEPFORMAT = '%-12s%s %s %s %s'
    FORMAT = '%-12s%s'

    ADDED = 'added'
    REMOVED = 'removed'

    def __init__(self, old, new, ignore=None, exclude=None):
        self.result = []
        self.ignore = ignore or []
        self.exclude = exclude or []

        FILEIDX = self.__FILEIDX
        for tag in self.ignore:
            for entry in FILEIDX:
                if tag == entry[0]:
                    entry[1] = None
                    break

        try:
            old = self.__load_pkg(old).header
            new = self.__load_pkg(new).header
        except KeyError as e:
            print_warning(str(e))
            sys.exit(2)

        # Compare single tags
        for tag in self.TAGS:
            old_tag = old[tag]
            new_tag = new[tag]
            if old_tag != new_tag:
                tagname = rpm.tagnames[tag]
                if old_tag is None:
                    self.__add(self.FORMAT, (self.ADDED, tagname))
                elif new_tag is None:
                    self.__add(self.FORMAT, (self.REMOVED, tagname))
                else:
                    self.__add(self.FORMAT, ('S.5.....', tagname))

        # compare Provides, Requires, ...
        for tag in self.PRCO:
            self.__comparePRCOs(old, new, tag)

        # compare the files

        old_files_dict = self.__fileIteratorToDict(old.fiFromHeader())
        new_files_dict = self.__fileIteratorToDict(new.fiFromHeader())
        files = list(set(chain(iter(old_files_dict), iter(new_files_dict))))
        files.sort()

        for f in files:
            if self._excluded(f):
                continue

            diff = False

            old_file = old_files_dict.get(f)
            new_file = new_files_dict.get(f)

            if not old_file:
                self.__add(self.FORMAT, (self.ADDED, f))
            elif not new_file:
                self.__add(self.FORMAT, (self.REMOVED, f))
            else:
                fmt = ''
                for entry in FILEIDX:
                    if entry[1] is not None and \
                            old_file[entry[1]] != new_file[entry[1]]:
                        fmt += entry[0]
                        diff = True
                    else:
                        fmt += '.'
                if diff:
                    self.__add(self.FORMAT, (fmt, f))

    def _excluded(self, f):
        f = pathlib.PurePath(f)
        for glob in self.exclude:
            if f.match(glob):
                return True
            if glob.startswith('/'):
                for parent in f.parents:
                    if parent.match(glob):
                        return True
        return False

    # return a report of the differences
    def textdiff(self):
        return '\n'.join((fmt % data for fmt, data in self.result))

    # do the two rpms differ
    def differs(self):
        return bool(self.result)

    # add one differing item
    def __add(self, fmt, data):
        self.result.append((fmt, data))

    # load a package from a file or from the installed ones
    def __load_pkg(self, name):
        # FIXME: redo to try file/installed and proceed based on that, or pick
        # one of the selected first
        tmpdir = tempfile.gettempdir()
        try:
            if name.is_file():
                return Pkg(name, tmpdir)
        except TypeError:
            pass
        inst = getInstalledPkgs(name)
        if not inst:
            raise KeyError(f'No installed packages by name {name}')
        if len(inst) > 1:
            raise KeyError(f'More than one installed packages by name {name}')
        return inst[0]

    # output the right string according to RPMSENSE_* const
    def sense2str(self, sense):
        s = ''
        for tag, char in ((rpm.RPMSENSE_LESS, '<'),
                          (rpm.RPMSENSE_GREATER, '>'),
                          (rpm.RPMSENSE_EQUAL, '=')):
            if sense & tag:
                s += char
        return s

    # output the right requires string according to RPMSENSE_* const
    def req2str(self, req):
        s = 'REQUIRES'
        # we want to use 64 even with rpm versions that define RPMSENSE_PREREQ
        # as 0 to get sane results when comparing packages built with an old
        # (64) version and a new (0) one
        if req & (rpm.RPMSENSE_PREREQ or 64):
            s = 'PREREQ'

        ss = []
        if req & rpm.RPMSENSE_SCRIPT_PRE:
            ss.append('pre')
        if req & rpm.RPMSENSE_SCRIPT_POST:
            ss.append('post')
        if req & rpm.RPMSENSE_SCRIPT_PREUN:
            ss.append('preun')
        if req & rpm.RPMSENSE_SCRIPT_POSTUN:
            ss.append('postun')
        if req & getattr(rpm, 'RPMSENSE_PRETRANS', 1 << 7):  # rpm >= 4.9.0
            ss.append('pretrans')
        if req & getattr(rpm, 'RPMSENSE_POSTTRANS', 1 << 5):  # rpm >= 4.9.0
            ss.append('posttrans')
        if ss:
            s += '(%s)' % ','.join(ss)

        return s

    # compare Provides, Requires, Conflicts, Obsoletes
    def __comparePRCOs(self, old, new, name):
        try:
            oldflags = old[name[:-1] + 'FLAGS']
        except ValueError:
            # assume tag not supported, e.g. Recommends with older rpm
            return
        newflags = new[name[:-1] + 'FLAGS']
        # fix buggy rpm binding not returning list for single entries
        if not isinstance(oldflags, list):
            oldflags = [oldflags]
        if not isinstance(newflags, list):
            newflags = [newflags]

        o = zip(old[name], oldflags, old[name[:-1] + 'VERSION'])
        if not isinstance(o, list):
            o = list(o)
        n = zip(new[name], newflags, new[name[:-1] + 'VERSION'])
        if not isinstance(n, list):
            n = list(n)

        # filter self provides, TODO: self %name(%_isa) as well
        if name == 'PROVIDES':
            oldE = old['epoch'] is not None and str(old['epoch']) + ':' or ''
            oldV = '%s%s' % (oldE, old.format('%{VERSION}-%{RELEASE}'))
            oldNV = (old['name'], rpm.RPMSENSE_EQUAL, oldV.encode())
            newE = new['epoch'] is not None and str(new['epoch']) + ':' or ''
            newV = '%s%s' % (newE, new.format('%{VERSION}-%{RELEASE}'))
            newNV = (new['name'], rpm.RPMSENSE_EQUAL, newV.encode())
            o = [entry for entry in o if entry != oldNV]
            n = [entry for entry in n if entry != newNV]

        for oldentry in o:
            if oldentry not in n:
                namestr = name
                if namestr == 'REQUIRES':
                    namestr = self.req2str(oldentry[1])
                self.__add(self.DEPFORMAT,
                           (self.REMOVED, namestr, byte_to_string(oldentry[0]),
                            self.sense2str(oldentry[1]), byte_to_string(oldentry[2])))
        for newentry in n:
            if newentry not in o:
                namestr = name
                if namestr == 'REQUIRES':
                    namestr = self.req2str(newentry[1])
                self.__add(self.DEPFORMAT,
                           (self.ADDED, namestr, byte_to_string(newentry[0]),
                            self.sense2str(newentry[1]), byte_to_string(newentry[2])))

    def __fileIteratorToDict(self, fi):
        result = {}
        for filedata in fi:
            result[filedata[0]] = filedata[1:]
        return result
