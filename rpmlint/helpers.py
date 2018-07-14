# File containing various helper functions used across rpmlint

import sys


def print_warning(message):
    """
    Print warning message to stderr.
    """
    print(message, file=sys.stderr)
