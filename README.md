# rpmlint

[![Build Status](https://travis-ci.org/rpm-software-management/rpmlint.svg)](https://travis-ci.org/rpm-software-management/rpmlint)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/rpm-software-management/rpmlint.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/rpm-software-management/rpmlint/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/rpm-software-management/rpmlint.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/rpm-software-management/rpmlint/context:python)
[![Coverage Status](https://coveralls.io/repos/github/rpm-software-management/rpmlint/badge.svg?branch=master)](https://coveralls.io/github/rpm-software-management/rpmlint?branch=master)

rpmlint is a tool for checking common errors in rpm packages.
rpmlint can be used to test individual packages before uploading or to check
an entire distribution.

rpmlint can check binary rpms, source rpms, and plain specfiles, but all
checks do not apply to all argument types.
For best check coverage, run rpmlint on source rpms instead of
plain specfiles.

The idea for rpmlint is from the lintian tool of the Debian project.
All the checks reside in rpmlint/ folder. Feel free to provide new
checks and suggestions at:

https://github.com/rpm-software-management/rpmlint

## Install

For installation on your machine you will need following packages:

- Python 3.6 or newer
- Python setuptoools
- rpm and its python bindings
- readelf, cpio, gzip, bzip and xz
- libmagic and its python bindings (optional)
- groff and gtbl (optional)
- enchant and its python bindings (optional)
- appstream-util, part of appstream-glib (optional)

## Testing

If you want to test the rpmlint when developing best is to use docker
to provide the enviroment for you. There are various distribution
dockerfiles in `test/` folder.

Ie. if you want to test on latest openSUSE you can test using following commands:

`docker build -t opensusetw -f test/Dockerfile-opensusetw .`

`docker run -v $(pwd):/usr/src/rpmlint/ opensusetw python3 setup.py test`

Another option is to run the tests on your system directly. If you
have all the required modules as listed on the Install section above.
You will also need `pytest` and `pytest-cov` and `pytest-flake8`.

If all the dependencies are present you can just execute tests using:

`python3 setup.py test`

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
