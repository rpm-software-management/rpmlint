# -*- coding: utf-8 -*-
#############################################################################
# File          : AbstractCheck.py
# Package       : rpmlint
# Author        : Frederic Lepied
# Created on    : Tue Sep 28 00:22:38 1999
# Purpose       : Abstract class to hold all the derived classes.
#############################################################################

import contextlib
import re
try:
    import urllib2
except ImportError:
    import urllib.request as urllib2

import rpmlint.Config as Config
from rpmlint.Filter import addDetails, printInfo, printWarning

# Note: do not add any capturing parentheses here
macro_regex = re.compile(r'%+[{(]?[a-zA-Z_]\w{2,}[)}]?')


class _HeadRequest(urllib2.Request):
    def get_method(self):
        return "HEAD"


class _HeadRedirectHandler(urllib2.HTTPRedirectHandler):
    def redirect_request(*args):
        res = urllib2.HTTPRedirectHandler.redirect_request(*args)
        if res:
            res = _HeadRequest(res.get_full_url())
        return res


class AbstractCheck(object):
    known_checks = {}

    def __init__(self, name):
        if not AbstractCheck.known_checks.get(name):
            AbstractCheck.known_checks[name] = self
        self.name = name
        self.verbose = False
        self.network_enabled = Config.getOption("NetworkEnabled", False)
        self.network_timeout = Config.getOption("NetworkTimeout", 10)

    def check(self, pkg):
        if pkg.isSource():
            return self.check_source(pkg)
        return self.check_binary(pkg)

    def check_source(self, pkg):
        return

    def check_binary(self, pkg):
        return

    def check_spec(self, pkg, spec_file, spec_lines=None):
        return

    def check_url(self, pkg, tag, url):
        """
        Check that URL points to something that seems to exist.
        Return info() of the response if available.
        """
        if not self.network_enabled:
            if self.verbose:
                printInfo(pkg, 'network-checks-disabled', url)
            return

        if self.verbose:
            printInfo(pkg, 'checking-url', url,
                      '(timeout %s seconds)' % self.network_timeout)

        res = None
        try:
            opener = urllib2.build_opener(_HeadRedirectHandler())
            opener.addheaders = [('User-Agent',
                                  'rpmlint/%s' % Config.__version__)]
            res = opener.open(_HeadRequest(url), timeout=self.network_timeout)
        except Exception as e:
            errstr = str(e) or repr(e) or type(e)
            printWarning(pkg, 'invalid-url', '%s:' % tag, url, errstr)
        info = None
        if res:
            with contextlib.closing(res):
                info = res.info()
        return info


class AbstractFilesCheck(AbstractCheck):
    def __init__(self, name, file_regexp):
        self.__files_re = re.compile(file_regexp)
        AbstractCheck.__init__(self, name)

    def check_binary(self, pkg):
        ghosts = pkg.ghostFiles()
        for filename in (x for x in pkg.files() if x not in ghosts):
            if self.__files_re.match(filename):
                self.check_file(pkg, filename)

    def check_file(self, pkg, filename):
        """Virtual method called for each file that match the regexp passed
        to the constructor.
        """
        raise NotImplementedError('check must be implemented in subclass')


addDetails(
'invalid-url',
'''The value should be a valid, public HTTP, HTTPS, or FTP URL.''',

'network-checks-disabled',
'''Checks requiring network access have not been enabled in configuration,
see the NetworkEnabled option.''',
)

# AbstractCheck.py ends here
