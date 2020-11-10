import argparse
from pathlib import Path
import sys

from rpmlint.helpers import print_warning
from rpmlint.lint import Lint
from rpmlint.rpmdiff import Rpmdiff
from rpmlint.version import __version__


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
    Process the passed arguments and return the result
    :param argv: passed arguments
    """

    parser = argparse.ArgumentParser(prog='rpmdiff',
                                     description='Shows basic differences between two rpm packages')
    parser.add_argument('old_package', metavar='RPM_ORIG', type=Path, help='the old package')
    parser.add_argument('new_package', metavar='RPM_NEW', type=Path, help='the new package')
    parser.add_argument('-V', '--version', action='version', version=__version__, help='show package version and exit')
    parser.add_argument('-i', '--ignore', nargs='+', default=None, choices=['S', 'M', '5', 'D', 'N', 'L', 'V', 'U', 'G', 'F', 'T'],
                        help="""file property to ignore when calculating differences.
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
    if not options.old_package.exists():
        print_warning(f"The file '{options.old_package}' does not exist")
        exit(2)
    if not options.new_package.exists():
        print_warning(f"The file '{options.new_package}' does not exist")
        exit(2)

    # convert options to dict
    options_dict = vars(options)
    return options_dict


def process_lint_args(argv):
    """
    Process the passed arguments and return the result
    :param argv: passed arguments
    """

    parser = argparse.ArgumentParser(prog='rpmlint',
                                     description='Check for common problems in rpm packages')
    parser.add_argument('rpmfile', nargs='*', type=Path, help='files to be validated by rpmlint')
    parser.add_argument('-V', '--version', action='version', version=__version__, help='show package version and exit')
    parser.add_argument('-c', '--config', type=_validate_conf_location, help='load up additional configuration data from specified path (file or directory with *.toml files')
    parser.add_argument('-e', '--explain', nargs='+', default='', help='provide detailed explanation for one specific message id')
    parser.add_argument('-r', '--rpmlintrc', type=Path, help='load up specified rpmlintrc file')
    parser.add_argument('-v', '--verbose', '--info', action='store_true', help='provide detailed explanations where available')
    parser.add_argument('-p', '--print-config', action='store_true', help='print the settings that are in effect when using the rpmlint')
    parser.add_argument('-i', '--installed', nargs='+', default='', help='installed packages to be validated by rpmlint')
    parser.add_argument('-t', '--time-report', action='store_true', help='print time report for run checks')
    parser.add_argument('-T', '--profile', action='store_true', help='print cProfile report')
    lint_modes_parser = parser.add_mutually_exclusive_group()
    lint_modes_parser.add_argument('-s', '--strict', action='store_true', help='treat all messages as errors')
    lint_modes_parser.add_argument('-P', '--permissive', action='store_true', help='treat individual errors as non-fatal')

    # print help if there is no argument
    if len(argv) < 1:
        parser.print_help()
        sys.exit(0)

    options = parser.parse_args(args=argv)

    # make sure rpmlintrc exists
    if options.rpmlintrc:
        if not options.rpmlintrc.exists():
            print_warning(f"User specified rpmlintrc '{options.rpmlintrc}' does not exist")
            exit(2)
    # validate all the rpmlfile options to be either file or folder
    f_path = []
    invalid_path = False
    for item in options.rpmfile:
        p_path = Path()
        pattern = None
        for pos, component in enumerate(item.parts):
            if ('*' in component) or ('?' in component):
                pattern = '/'.join(item.parts[pos:])
                break
            p_path = p_path / component
        p_path = list(p_path.glob(pattern)) if pattern else [p_path]

        for path in p_path:
            if not path.exists():
                print_warning(f"The file or directory '{path}' does not exist")
                invalid_path = True
        f_path += p_path

    if invalid_path:
        exit(2)
    # convert options to dict
    options_dict = vars(options)
    # use computed rpmfile
    options_dict['rpmfile'] = f_path
    return options_dict


def _validate_conf_location(string):
    """
    Help validate configuration location during argument parsing.

    We accept either one configuration file or a directory (then it processes
    all *.toml files in this directory). It exits the program if location
    doesn't exist.

    Args:
        string: A string representing configuration path (file or directory).

    Returns:
        A list with individual paths for each configuration file found.
    """
    config_paths = []
    path = Path(string)

    # Exit if file or dir doesn't exist
    if not path.exists():
        print_warning(
            f"File or dir with user specified configuration '{string}' does not exist")
        exit(2)

    if path.is_dir():
        config_paths.extend(path.glob('*.toml'))
    elif path.is_file():
        config_paths.append(path)

    return config_paths


def lint():
    """
    Main wrapper for lint command processing
    """
    options = process_lint_args(sys.argv[1:])

    lint = Lint(options)
    sys.exit(lint.run())


def diff():
    """
    Main wrapper for diff command processing
    """
    options = process_diff_args(sys.argv[1:])
    d = Rpmdiff(options['old_package'], options['new_package'],
                ignore=options['ignore'], exclude=options['exclude'])
    textdiff = d.textdiff()
    if textdiff:
        print(textdiff)
    sys.exit(int(d.differs()))
