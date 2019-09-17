# File containing various helper functions used across rpmlint

from shutil import get_terminal_size
import sys

from rpmlint.color import Color


def string_center(message, filler=' '):
    """
    Create string centered of the terminal
    """
    cols, rows = get_terminal_size()
    return (f' {message} ').center(cols, filler)


def print_centered(message, filler=' '):
    """
    Print message in the center of a terminal
    """
    print(string_center(message, filler))


def print_warning(message):
    """
    Print warning message to stderr.
    """
    print(f'{Color.Red}{message}{Color.Reset}', file=sys.stderr)


def byte_to_string(item):
    """
    Convert byte items to strings
    """
    # empty stuff or already existing string stays
    if item is None or isinstance(item, str):
        return item

    # if we have a list/tuple we have to recurse
    if isinstance(item, (list, tuple)):
        return [byte_to_string(i) for i in item]

    # everything else shall be decoded and fails replaced
    return item.decode(encoding='UTF-8', errors='replace')
