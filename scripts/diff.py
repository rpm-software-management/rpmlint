#!/usr/bin/python -tt
# -*- coding: utf-8 -*-
#
# Copyright (C) 2006 Mandriva; 2009 Red Hat, Inc.; 2009 Ville Skyttä
# Authors: Frederic Lepied, Florian Festi
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU Library General Public License as published by
# the Free Software Foundation; version 2 only
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Library General Public License for more details.
#
# You should have received a copy of the GNU Library General Public License
# along with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.

import getopt
import itertools
import os.path
import sys
import tempfile

import rpm
import rpmlint.Pkg


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

    # code starts here

    def __init__(self, old, new, ignore=None):
        self.result = []
        self.ignore = ignore
        if self.ignore is None:
            self.ignore = []

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
            Pkg.warn(str(e))
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
        files = list(set(itertools.chain(iter(old_files_dict),
                                         iter(new_files_dict))))
        files.sort()

        for f in files:
            diff = False

            old_file = old_files_dict.get(f)
            new_file = new_files_dict.get(f)

            if not old_file:
                self.__add(self.FORMAT, (self.ADDED, f))
            elif not new_file:
                self.__add(self.FORMAT, (self.REMOVED, f))
            else:
                format = ''
                for entry in FILEIDX:
                    if entry[1] is not None and \
                            old_file[entry[1]] != new_file[entry[1]]:
                        format = format + entry[0]
                        diff = True
                    else:
                        format = format + '.'
                if diff:
                    self.__add(self.FORMAT, (format, f))

    # return a report of the differences
    def textdiff(self):
        return '\n'.join((format % data for format, data in self.result))

    # do the two rpms differ
    def differs(self):
        return bool(self.result)

    # add one differing item
    def __add(self, format, data):
        self.result.append((format, data))

    # load a package from a file or from the installed ones
    def __load_pkg(self, name, tmpdir=tempfile.gettempdir()):
        try:
            if os.path.isfile(name):
                return Pkg.Pkg(name, tmpdir)
        except TypeError:
            pass
        inst = Pkg.getInstalledPkgs(name)
        if not inst:
            raise KeyError("No installed packages by name %s" % name)
        if len(inst) > 1:
            raise KeyError("More than one installed packages by name %s" % name)
        return inst[0]

    # output the right string according to RPMSENSE_* const
    def sense2str(self, sense):
        s = ""
        for tag, char in ((rpm.RPMSENSE_LESS, "<"),
                          (rpm.RPMSENSE_GREATER, ">"),
                          (rpm.RPMSENSE_EQUAL, "=")):
            if sense & tag:
                s += char
        return s

    # output the right requires string according to RPMSENSE_* const
    def req2str(self, req):
        s = "REQUIRES"
        # we want to use 64 even with rpm versions that define RPMSENSE_PREREQ
        # as 0 to get sane results when comparing packages built with an old
        # (64) version and a new (0) one
        if req & (rpm.RPMSENSE_PREREQ or 64):
            s = "PREREQ"

        ss = []
        if req & rpm.RPMSENSE_SCRIPT_PRE:
            ss.append("pre")
        if req & rpm.RPMSENSE_SCRIPT_POST:
            ss.append("post")
        if req & rpm.RPMSENSE_SCRIPT_PREUN:
            ss.append("preun")
        if req & rpm.RPMSENSE_SCRIPT_POSTUN:
            ss.append("postun")
        if req & getattr(rpm, "RPMSENSE_PRETRANS", 1 << 7):  # rpm >= 4.9.0
            ss.append("pretrans")
        if req & getattr(rpm, "RPMSENSE_POSTTRANS", 1 << 5):  # rpm >= 4.9.0
            ss.append("posttrans")
        if ss:
            s += "(%s)" % ",".join(ss)

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
            oldE = old['epoch'] is not None and str(old['epoch']) + ":" or ""
            oldV = "%s%s" % (oldE, old.format("%{VERSION}-%{RELEASE}"))
            oldNV = (old['name'], rpm.RPMSENSE_EQUAL, oldV.encode())
            newE = new['epoch'] is not None and str(new['epoch']) + ":" or ""
            newV = "%s%s" % (newE, new.format("%{VERSION}-%{RELEASE}"))
            newNV = (new['name'], rpm.RPMSENSE_EQUAL, newV.encode())
            o = [entry for entry in o if entry != oldNV]
            n = [entry for entry in n if entry != newNV]

        for oldentry in o:
            if oldentry not in n:
                namestr = name
                if namestr == 'REQUIRES':
                    namestr = self.req2str(oldentry[1])
                self.__add(self.DEPFORMAT,
                           (self.REMOVED, namestr, Pkg.b2s(oldentry[0]),
                            self.sense2str(oldentry[1]), Pkg.b2s(oldentry[2])))
        for newentry in n:
            if newentry not in o:
                namestr = name
                if namestr == 'REQUIRES':
                    namestr = self.req2str(newentry[1])
                self.__add(self.DEPFORMAT,
                           (self.ADDED, namestr, Pkg.b2s(newentry[0]),
                            self.sense2str(newentry[1]), Pkg.b2s(newentry[2])))

    def __fileIteratorToDict(self, fi):
        result = {}
        for filedata in fi:
            result[filedata[0]] = filedata[1:]
        return result


def _usage(exit=1):
    print('''Usage: %s [<options>] <old package> <new package>
Options:
  -h, --help     Output this message and exit
  -i, --ignore   File property to ignore when calculating differences (may be
                 used multiple times); valid values are: S (size), M (mode),
                 5 (checksum), D (device), N (inode), L (number of links),
                 V (vflags), U (user), G (group), F (digest), T (time)'''
          % sys.argv[0])
    sys.exit(exit)


def main():

    ignore_tags = []
    try:
        opts, args = getopt.getopt(sys.argv[1:],
                                   "hti:", ["help", "ignore-times", "ignore="])
    except getopt.GetoptError as e:
        Pkg.warn("Error: %s" % e)
        _usage()

    for option, argument in opts:
        if option in ("-h", "--help"):
            _usage(0)
        if option in ("-t", "--ignore-times"):
            # deprecated; --ignore=T should be used instead
            ignore_tags.append("T")
        if option in ("-i", "--ignore"):
            ignore_tags.append(argument)

    if len(args) != 2:
        _usage()

    d = Rpmdiff(args[0], args[1], ignore=ignore_tags)
    textdiff = d.textdiff()
    if textdiff:
        print(textdiff)
    sys.exit(int(d.differs()))


if __name__ == '__main__':
    main()

# rpmdiff ends here
