# rpmlint [![Build Status](https://travis-ci.org/rpm-software-management/rpmlint.svg)](https://travis-ci.org/rpm-software-management/rpmlint)

rpmlint is a tool for checking common errors in rpm packages.  rpmlint
can be used to test individual packages before uploading or to check
an entire distribution.  By default all applicable checks are
performed but specific checks can be performed by using command line
parameters.

rpmlint can check binary rpms (files and installed ones), source rpms,
and plain specfiles, but all checks do not apply to all argument
types.  For best check coverage, run rpmlint on source rpms instead of
plain specfiles, and installed binary rpms instead of uninstalled
binary rpm files.

The idea for rpmlint is from the lintian tool of the Debian project.

Comments and new checks welcome. See the project home page at
https://github.com/rpm-software-management/rpmlint

Implemented checks:

- Tag checks (TagsCheck).
- Distribution specific checks (MandrakeCheck).
- Binary checks (BinaryCheck).
- Configuration file checks (ConfigCheck).
- Location, permission, group and owner checks (FileCheck).
- suid warnings (FileCheck).
- Signature checks (SignatureCheck).
- FHS checks (FHSCheck).
- Source specific checks (SourceCheck).
- i18n checks (I18NCheck).
- Menu system checks (MenuCheck).
- Scriptlet checks (PostCheck).
- `/etc/rc.d/init.d` checks (InitScriptCheck).
- Spec file checks (SpecCheck).
- Zip/Jar file checks (ZipCheck).
- Pam configuration file checks (PamCheck).
- Rpm file checks (RpmFileCheck).
- Software Collections checks (SCLCheck).

If you want to change configuration options or the list of checks, use
the global configuration files `/etc/rpmlint/*config` or the user
configuration file `$XDG_CONFIG_HOME/rpmlint` (`~/.config/rpmlint` if
`$XDG_CONFIG_HOME` is empty or not set).

Configuration files are Python source files and should begin with the
following line:

```python
from rpmlint.Config import *
```

to load configuration functions.

Configuration functions:

`resetChecks()` resets the list of checks.

`addCheck(check)` adds the check to the list of checks to try.

`addCheckDir(path)` adds a path to look for checks.

`setOption(name, value)` sets the value of the configuration option.
See below for the list of available options.

`addFilter(regexp)` adds a filter to remove the output of a check, and
`removeFilter(regexp)` removes one (for use eg. in per-user configuration
files to remove filters added in system config files).

See the file `config` shipped with rpmlint for examples, available
options and their default values.
