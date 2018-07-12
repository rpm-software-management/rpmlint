# -*- coding: utf-8 -*-
# check the rpm file for various errors.
#
# Copyright (C) 2006 Michael Scherer <misc@zarb.org>
#                    Ville Skyttä <ville.skytta@iki.fi>
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; version 2 of the License.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA


import os

import rpmlint.AbstractCheck as AbstractCheck
from rpmlint.Filter import addDetails, printWarning


class RpmFileCheck(AbstractCheck.AbstractCheck):
    def __init__(self):
        AbstractCheck.AbstractCheck.__init__(self, "RpmFileCheck")

    def check(self, pkg):
        # http://en.wikipedia.org/wiki/Joliet_(file_system)
        rpmfile_name = os.path.basename(pkg.filename)
        if len(rpmfile_name) > 64:
            printWarning(pkg, 'filename-too-long-for-joliet', rpmfile_name)


check = RpmFileCheck()

addDetails(
'filename-too-long-for-joliet',
'''This filename is too long to fit on a joliet filesystem (limit is 64 unicode
chars).''',
)
