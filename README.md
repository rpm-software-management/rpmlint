# rpmlint

[![Build Status](https://travis-ci.org/rpm-software-management/rpmlint.svg)](https://travis-ci.org/rpm-software-management/rpmlint)
[![Total alerts](https://img.shields.io/lgtm/alerts/g/rpm-software-management/rpmlint.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/rpm-software-management/rpmlint/alerts/)
[![Language grade: Python](https://img.shields.io/lgtm/grade/python/g/rpm-software-management/rpmlint.svg?logo=lgtm&logoWidth=18)](https://lgtm.com/projects/g/rpm-software-management/rpmlint/context:python)
[![Coverage Status](https://coveralls.io/repos/github/rpm-software-management/rpmlint/badge.svg?branch=master)](https://coveralls.io/github/rpm-software-management/rpmlint?branch=master)

`rpmlint` is a tool for checking common errors in RPM packages.
`rpmlint` can be used to test individual packages before uploading or to check
an entire distribution.

`rpmlint` can check binary RPMs, source RPMs, and plain specfiles, but all
checks do not apply to all argument types.
For best check coverage, run `rpmlint` on source RPMs instead of
plain specfiles.

The idea for `rpmlint` is from the lintian tool of the Debian project.
All the checks reside in `rpmlint/checks` folder. Feel free to provide new
checks and suggestions at:

https://github.com/rpm-software-management/rpmlint

## Install

For installation on your machine you will need the following packages:

Mandatory
- Python 3.6 or newer
- Python setuptoools, python3-toml, python3-pyxdg
- rpm and its python bindings
- readelf, cpio, gzip, bzip and xz

Optional
- libmagic and its python bindings
- groff and gtbl
- enchant and its python bindings
- appstream-util, part of appstream-glib

## Testing

### Docker
If you want to test the `rpmlint` when developing best is to use docker
to provide the environment for you. There are various distribution
dockerfiles in `test/` folder.

I.e. if you want to test on the latest openSUSE you can test using the following commands:

`docker build -t opensusetw -f test/Dockerfile-opensusetw .`

`docker run -v $(pwd):/usr/src/rpmlint/ opensusetw python3 setup.py test`

### Directly

Another option is to run the tests on your system directly. If you
have all the required modules as listed on the Install section above.
You will also need `pytest` and `pytest-cov` and `pytest-flake8`.

If all the dependencies are present you can just execute tests using:

`python3 setup.py test`

Or even pick one of the tests using `pytest`:

`python3 -m pytest test/test_config.py`

## Bugfixing and contributing

Any help is, of course, welcome but honestly most probable cause for your visit
here is that `rpmlint` is marking something as invalid while it shouldn't or
it is marking something as correct while it should not either :)

Now there is an easy way how to fix that. Our testsuite simply needs an
extension to take the above problem into the account.

Primarily we just need the offending rpm file (best the smallest you can
find or we would soon take few GB to take a checkout) and some basic
expectation of what should happen.

### Example workflow

1) I have rpmfile that should report unreadable zip file
2) I store this file in git under `test/binary/texlive-codepage-doc-2018.151.svn21126-38.1.noarch.rpm`
3) Now I need to figure out what `check` should test this, in this case `test_zip.py`
4) For the testing I will have to devise a small function that validates my expectations:

```
@pytest.mark.parametrize('package', ['binary/texlive-codepage-doc'])
def test_zip2(tmpdir, package, zipcheck):
    output, test = zipcheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'W: unable-to-read-zip' in out
```

As you can see it is not so hard and with each added test we get better
coverage on what is really expected from rpmlint and avoid naughty regressions
in the long run.

## Configuration

If you want to change configuration options or the list of checks you can
use the following locations:

`/etc/xdg/rpmlint/*config`

`$XDG_CONFIG_HOME/rpmlint/*config`

The configuration itself is a `toml` file where for some basic inspiration
you can check up `rpmlint/configdefaults.toml` which specifies format/defaults.

Additional option to control `rpmlint` behaviour is the addition of `rpmlintrc` file
which uses old syntax for compatibility with old `rpmlint` releases, yet
it can be normal `toml` file if you wish:

`setBadness('check', 0)`

`addFilter('test-i-ignore')`
