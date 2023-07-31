# rpmlint

<h1 align="center">
  <img src="rpmlint.svg" width="200">
</h1>

[![Build and Test](https://github.com/rpm-software-management/rpmlint/actions/workflows/main.yml/badge.svg?branch=main)](https://github.com/rpm-software-management/rpmlint/actions/workflows/main.yml)
[![Build and Test 2](https://github.com/rpm-software-management/rpmlint/actions/workflows/main.yml/badge.svg?branch=opensuse)](https://github.com/rpm-software-management/rpmlint/actions/workflows/main.yml)
[![build result](https://build.opensuse.org/projects/devel:openSUSE:Factory:rpmlint/packages/rpmlint/badge.svg?type=default)](https://build.opensuse.org/package/show/devel:openSUSE:Factory:rpmlint/rpmlint)
[![repology](https://repology.org/badge/latest-versions/rpmlint.svg)](https://repology.org/project/rpmlint/versions)
[![Coverage Status](https://coveralls.io/repos/github/rpm-software-management/rpmlint/badge.svg)](https://coveralls.io/github/rpm-software-management/rpmlint)

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

Mandatory:
- Python 3.8 or newer
- python3-setuptools, python3-tomli (for `python3 < 3.11`), python3-tomli-w,
  python3-pyxdg, python3-pybeam
- rpm and its python bindings
- binutils, cpio, gzip, bzip, xz and zstd

Optional, for running the test suite:
- devscripts
- dash
- a 32-bit glibc if on a 64-bit architecture
- desktop-file-utils
- libmagic and its python bindings
- enchant and its python bindings, along with en_US and cs_CZ dictionaries
- appstream-util, part of appstream-glib

`rpmlint` is part of most distributions and as an user you can simply

    dnf install rpmlint

## Testing

You will need to have all the required modules as listed on the Install section above.
You will also need `pytest`,`pytest-cov` and `pytest-xdist`, 
which you can install individually or by running `pip install -e ".[test]"`.

If all the dependencies are present you can just execute tests using:

`python3 -m pytest`

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

Preferable approach for binary packages is to create artificial testcase (to keep binaries small and trivial).
We are currently using OBS to produce binaries:
https://build.opensuse.org/project/show/devel:openSUSE:Factory:rpmlint:tests

For a sample package see:
https://build.opensuse.org/package/show/devel:openSUSE:Factory:rpmlint:tests/non-position-independent-exec

## Configuration

If you want to change configuration options or the list of checks you can
use the following locations:

`/etc/xdg/rpmlint/*toml`

`$XDG_CONFIG_HOME/rpmlint/*toml`

The configuration itself is a `toml` file where for some basic inspiration
you can check up [`rpmlint/configdefaults.toml`](rpmlint/configdefaults.toml) which specifies format/defaults.

One can also include additional configuration files (or directories) by using the `--config` option.
Note that all TOML configuration values are merged and not overridden.
So e.g. values in a list are concatenated. If you need an override,
use `*.override.*toml` configuration file, where all defined values are selected as default.

Additional option to control `rpmlint` behaviour is the addition of `rpmlintrc` file
which uses old syntax for compatibility with old `rpmlint` releases, yet
it can be normal `toml` file if you wish:

    setBadness('check', 0)
    addFilter('test-i-ignore')

The location of `rpmlintrc` can be set using `--rpmlintrc` option.
Or it can load any `*.rpmlintrc` or `*-rpmlintrc` that are located in the same
folder as check RPM file (or a specfile). Note the auto-loading happens only
when one RPM file (or a specfile) is used.
The best practice is to store the name in `$PACKAGE_NAME.rpmlintrc`.

`setBadness` overrides a default badness for a given check and `addFilter` ignores all errors
that match the given regular expression (one cannot filter out errors that are listed in `BlockedFilters`
in a configuration file).
