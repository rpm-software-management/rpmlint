import sys

if hasattr(sys.stdout, 'isatty') and sys.stdout.isatty():
    class Color(object):
        """
        Colors used when doing printouts with rpmlint
        """
        Bold = '\x1b[1m'
        Red = '\x1b[31m'
        Yellow = '\x1b[33m'
        Reset = '\x1b[0m'
else:
    class Color(object):
        """
        Colors used when doing printouts with rpmlint
        """
        Bold = ''
        Red = ''
        Yellow = ''
        Reset = ''
