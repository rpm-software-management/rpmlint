# rpmlint

[![Build Status](https://travis-ci.org/rpm-software-management/rpmlint.svg)](https://travis-ci.org/rpm-software-management/rpmlint)
[![Codacy Badge](https://api.codacy.com/project/badge/Grade/3539541ffbaf442ab34a098d30af166f)](https://www.codacy.com/app/scarabeusiv/rpmlint?utm_source=github.com&amp;utm_medium=referral&amp;utm_content=rpm-software-management/rpmlint&amp;utm_campaign=Badge_Grade)

rpmlint is a tool for checking common errors in rpm packages.
rpmlint can be used to test individual packages before uploading or to check
an entire distribution.

By default all applicable checks are performed but specific checks can be
performed by using command line parameters.

rpmlint can check binary rpms (files and installed ones), source rpms,
and plain specfiles, but all checks do not apply to all argument
types. For best check coverage, run rpmlint on source rpms instead of
plain specfiles, and installed binary rpms instead of uninstalled
binary rpm files.

The idea for rpmlint is from the lintian tool of the Debian project.
All the checks reside in rpmlint/ folder. Feel free to provide new
checks and suggestions at:

https://github.com/rpm-software-management/rpmlint

## Configuration

If you want to change configuration options or the list of checks you can
use following locations:

`/etc/rpmlint/*config`

`$XDG_CONFIG_HOME/rpmlint/*config`

Configuration itself is a normal ini file where for some basic inspiration
you can check up `rpmlint/configspec.cfg` which specifies format/defaults.

Additional option to control rpmlint behaviour is addition of rpmlintrc file
which uses old syntax for compatibility with old rpmlint releases, yet
it can be normal ini file if you wish:

`setBadness('check', 0)`

`addFilter('test-i-ignore')`
