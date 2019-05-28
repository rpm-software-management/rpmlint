import argparse
import os
import sys

from rpmlint.rpmdiff import Rpmdiff


__version__ = '2.0.0'
__copyright__ = """
    Copyright (C) 2006 Mandriva
    Copyright (C) 2009 Red Hat, Inc.
    Copyright (C) 2009 Ville Skyttä
    Copyright (C) 2017 SUSE LINUX GmbH
    This program is free software; you can redistribute it and/or
    modify it under the terms of the GNU General Public License
    as published by the Free Software Foundation; either version 2
    of the License, or (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program; if not, write to the Free Software
    Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.
"""


def process_diff_args(argv):
    """
    Process the parsed arguments and return the result
    :param argv: passed arguments
    """

    parser = argparse.ArgumentParser(prog='rpmdiff',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter,
                                     description='Shows basic differences between two rpm packages')
    parser.add_argument('old_package', metavar='RPM_ORIG', type=str, help='The old package')
    parser.add_argument('new_package', metavar='RPM_NEW', type=str, help='The new package')
    parser.add_argument('-i', '--ignore', nargs='+', default=None, choices=['S', 'M', '5', 'D', 'N', 'L', 'V', 'U', 'G', 'F', 'T'],
                        help="""File property to ignore when calculating differences.
                                Valid values are: S (size), M (mode), 5 (checksum), D (device),
                                N (inode), L (number of links), V (vflags), U (user), G (group),
                                F (digest), T (time)""")
    parser.add_argument('-e', '--exclude', metavar='GLOB', nargs='+', default=None,
                        help="""Paths to exclude when showing differences.
                                Takes a glob. When absolute (starting with /)
                                all files in a matching directory are excluded as well.
                                When relative, files matching the pattern anywhere
                                are excluded but not directory contents.""")

    # print help if there is no argument or less than the 2 mandatory ones
    if len(argv) < 2:
        parser.print_help()
        sys.exit(0)

    options = parser.parse_args(args=argv)
    # the rpms must exist for us to do anything
    if not os.path.exists(options.old_package):
        print(f'The file \'{options.old_package}\' does not exist')
        exit(2)
    if not os.path.exists(options.old_package):
        print(f'The file \'{options.new_package}\' does not exist')
        exit(2)

    # convert options to dict
    options_dict = vars(options)
    return options_dict


def diff():
    """
    Main wrapper for diff command parsing arguments and passing them out
    """
    options = process_diff_args(sys.argv[1:])
    d = Rpmdiff(options['old_package'], options['new_package'],
                ignore=options['ignore'], exclude=options['exclude'])
    textdiff = d.textdiff()
    if textdiff:
        print(textdiff)
    sys.exit(int(d.differs()))
