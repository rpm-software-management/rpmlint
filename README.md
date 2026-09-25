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
which you can install individually or by running:

    pip install -e ".[test]"

If all the dependencies are present you can just execute tests using:

    python3 -m pytest

Or even pick one of the tests using `pytest`:

    python3 -m pytest test/test_config.py

## Bugfixing and contributing

Any help is, of course, welcome but honestly most probable cause for your visit
here is that `rpmlint` is marking something as invalid while it shouldn't or
it is marking something as correct while it should not either :)

Now there is an easy way how to fix that. Our testsuite simply needs an
extension to take the above problem into the account.

Primarily we just need the offending rpm file (best the smallest you can
find or we would soon take few GB to take a checkout) and some basic
expectation of what should happen.

### Building the installable rpm and installing
This section focuses on how to build the tool as you develop it.

To build the tool, we'll use a tool called `packit`. First, install `packit` on your system:

    dnf install packit

Then, build the project using:

    packit build locally

If you encounter any errors, install the missing dependencies and run the same command again. Once the build is successful, you'll find a RPM file under the `noarch` directory. To install the package on your system, run:

    dnf install <the_rpm_you_just_built>

Alternatively, the built binary can be found in the `rpmlint` directory under the `.packit` directory, which you can run directly.

### Example workflow for testing a functionality

1) I have a zip file that should report as unreadable
2) I check what `check` should test this, in this case `ZipCheck` covered by `test_zip.py`
3) For the testing I devise a small function that validates my expectations:

```
@pytest.mark.parametrize('package', [EncryptedZipPackage])
def test_zip1(package, zipcheck):
    output, test = zipcheck
    test.check(package)
    out = output.print_results(output.results)
    assert 'W: unable-to-read-zip' in out
```

As you can see it is not so hard and with each added test we get better
coverage on what is really expected from rpmlint and avoid naughty regressions
in the long run.

No binary RPMs are stored in git for tests. Pick the lightest approach that
covers your case:
* For check-level tests use a `FakePkg`-based mock in `test/mockdata/mock_*.py`
  built with `get_tested_mock_package()` from `test/Testing.py`. Mock the
  header tags directly for metadata checks (see `mock_tags.py`); for payload
  content checks point `content-path` at a small real fixture file under
  `test/files/` (see `mock_zip.py`).
* When the code under test needs real RPM parsing or extraction, build a tiny
  RPM at test time with `build_tiny_rpm()` from `test/Testing.py` (uses
  `rpmbuild`, no network needed). See `test_pkg.py` and `test_diff.py`.
* Small real payloads (ELF objects, zip files) live in `test/files/`; the ELF
  ones can be regenerated with `test/files/build-elf-fixtures.sh`.

The only real RPMs kept in git are the three signature fixtures in
`test/binary/` (`hello-*-signed.rpm`, `no-signature-*.rpm`,
`unknown-key-*.rpm`) because GPG signature verification cannot be faked.

Run `flake8` on changed files before pushing; CI gates on it.

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
