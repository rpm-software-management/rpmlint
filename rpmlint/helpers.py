# File containing various helper functions used across rpmlint

import sys


def print_warning(message):
    """
    Print warning message to stderr.
    """
    print(message, file=sys.stderr)


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
