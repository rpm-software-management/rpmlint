from pathlib import Path
import stat

from rpmlint.checks import TmpfilesParser
from rpmlint.checks.AbstractCheck import AbstractCheck

# don't add tmp directories here, they could still be dangerous, since
# publicly accessible
WELL_KNOWN_PATHS = (
    '/var/lib', '/var/run', '/run', '/var/lock', '/var/cache',
    '/run/lock', '/var/log', '/var/spool', '/srv', '/etc',
    # some configs somehow reset /sys permissions here
    '/sys',
    # moderately well known, NIS stuff
    '/var/yp'
)

# chattr() flags that are not interesting security wise
BORING_ATTRS = (
    # disable copy-on-write on supported file-systems
    'C',
)


class SystemdTmpfilesCheck(AbstractCheck):
    """This check restricts content of systemd-tmpfiles configuration files.

    tmpfiles configuration can grant a wide range of properties from arbitrary
    file modes, ACLs to creating device files and more. Some of them can be
    security relevant, therefore we want to control what can and what cannot
    enter the distribution.
    """

    def __init__(self, config, output):
        super().__init__(config, output)
        # Build trie for fast lookup of restricted paths
        self.dropin_dir_trie = {}

        check_config = self.config.configuration['SystemdTmpfiles']
        # these are the tmpfiles.d drop-in dir locations we are restricting
        self.dropin_dirs = check_config['DropinDirs']
        # this is a list of base packages that we won't care about for
        # simplicity (like systemd packages themselves)
        self.ignore_packages = check_config['IgnorePackages']

        self._setup_location_trie()

        self.whitelist = self.config.configuration.get('SystemdTmpfilesWhitelist', [])
        for entry in self.whitelist:
            self._sanity_check_whitelist_entry(entry)
            self._normalize_whitelist_entry(entry)

    def _setup_location_trie(self):
        # Build trie of tmpfiles.d drop-in dir locations
        for location in self.dropin_dirs:
            path = Path(location)
            if not path.is_absolute():
                raise Exception(f'Absolute path expected: {path}')
            node = self.dropin_dir_trie
            # Skip initial '/'.
            parts = path.parts[1:]
            for part in parts[:-1]:
                node = node.setdefault(part, {})
                if node is None:
                    raise Exception(f'Conflicting paths in trie {location}')
            node[parts[-1]] = None

    def _is_path_restricted(self, pkgfile):
        """Returns True if the given path is within a tmpfiles.d drop in
        directory.
        """
        if stat.S_ISDIR(pkgfile.mode):
            # we only care for configuration files
            return False
        elif not pkgfile.name.endswith('.conf'):
            # systemd-tmpfiles only considers files ending in *.conf
            return False

        path = Path(pkgfile.name)

        # now check the trie if the path is in a restricted location

        # Skip initial '/'
        parts = path.parts[1:]
        node = self.dropin_dir_trie
        for part in parts:
            if node is None:
                return True
            if part not in node:
                return False
            node = node[part]
        return False

    def _normalize_whitelist_entry(self, entry):
        """Perform any operations on the whitelisting entry to make it match
        the format excepted by the rest of the checker.
        """
        packages = entry.setdefault('packages', [])
        if 'package' in entry:
            # _sanity_check_whitelist_entry() makes sure only one of both keys
            # is present in an entry
            packages.append(entry['package'])

        # normalize field separators
        entries = [' '.join(line.split()) for line in entry['entries']]
        entry['entries'] = entries

    def _sanity_check_whitelist_entry(self, entry):
        package = entry.get('package', None)
        packages = entry.get('packages', [])

        if not package and not packages:
            raise KeyError('SystemdTmpfilesCheck: missing "package" or "packages" key in whitelisting entry')
        elif package and packages:
            raise KeyError('SystemdTmpfilesCheck: encountered both "package" and "packages" keys in FileDigestGroup entry')

        if package and not isinstance(package, str):
            raise KeyError('SystemdTmpfilesCheck: "package" key contains non-string value')
        elif packages and not isinstance(packages, list):
            raise KeyError('SystemdTmpfilesCheck: "packages" key contains non-list value')

        if 'path' not in entry:
            raise KeyError('SystemdTmpfilesCheck: missing "path" key')

    def _is_in_safe_location(self, tf_entry):
        """Returns whether the given tmpfiles configuration entry affects a
        safe location that is usually okay to operate in."""
        # this loop only runs for files actually packaged in a tmpfiles.d
        # directory, so it shouldn't hurt performance much doing this linear
        # prefix check
        for known in WELL_KNOWN_PATHS:
            if tf_entry.get_target_path().startswith(known):
                return True

        return False

    def _is_sensitive_entry(self, tf_entry):
        """Returns whether the given tmpfiles configuration entry contains
        security sensitive settings."""
        base_type = tf_entry.get_type()[0]

        if base_type == 'L':
            # ignore symlinks for now. they are not often dangerous, mostly
            # only if well known config files are replaced by symlinks like
            # /etc/resolv.conf. Then it depends on the target file and
            # context. We could restrict these types in the future somewhen,
            # for now lets concentrate on more dangerous entries
            return False
        elif base_type in ('v', 'q', 'Q'):
            # deals with btrfs volumes, skip that for now
            return False
        elif base_type in ('r', 'R'):
            # removal of files, possibly recursively (upper case), often
            # restricted to boot time (! suffix)
            #
            # this could break stuff in the sense of a DoS if a bad pattern is
            # specified but for simplification skip that for now
            return False
        elif base_type in ('X', 'x'):
            # this only controls cleanup behaviour, not so interesting for us
            return False
        elif base_type.lower() in ('d', 'f', 'c', 'z', 'p'):
            # files or directories are created, copied into place or
            # permissions readjusted if already existing. 'f' may also write
            # string content from the config file into the file.
            if not self._is_in_safe_location(tf_entry):
                # if it's not in a well known place then it could be interesting
                return True
            if tf_entry.has_default_mode():
                # if the default mode applies then this is boring
                return False

            mode = tf_entry.get_octal_mode()
            # TODO: should we also check for sticky bits here? they are more
            # limiting than exposing, but in some special circumstances they
            # might ease exploits.
            danger_bits = (stat.S_IWOTH, stat.S_ISUID, stat.S_ISGID)
            if any([(mode & bit) != 0 for bit in danger_bits]):
                # a dangerous bit is set, so it's sensitive
                return True

            # otherwise it is pretty boring
            return False
        elif base_type in ('b', 'c'):
            # character/block devices
            if not tf_entry.get_target_path.startswith('/dev'):
                # if the device is not in /dev then it's unusual
                return True
            if tf_entry.has_non_root_owner() or tf_entry.has_non_root_group():
                # if its accessible by non-root in some way then it's sensitive
                return True

            mode = tf_entry.get_octal_mode()
            danger_bits = (stat.S_IROTH, stat.S_IWOTH)
            if any([(mode & bit) != 0 for bit in danger_bits]):
                # world readable or writeable, sensitive
                return True

            # root only access, should be fine
            return False
        elif base_type in ('h', 'H'):
            # sets chattr() attributes, possibly recursively (upper case)
            attr = tf_entry.get_arg()

            for prefix in ('+', '-', '='):
                # remove any possible prefix
                attr = attr.lstrip(prefix)

            for flag in attr:
                if flag not in BORING_ATTRS:
                    return True

            return False

        # other / yet unknown type, treat as sensitive
        return True

    def _check_for_whitelisting(self, pkg, pkgfile, tf_entry):
        """Checks whether the given tempfile entry has a valid whitelisting
        configured and returns the boolean result."""
        for wl_entry in self.whitelist:
            if pkg.name not in wl_entry['packages']:
                continue
            if tf_entry.get_config_file() != wl_entry['path']:
                continue

            if tf_entry.get_normalized_line() in wl_entry['entries']:
                return True

        return False

    def check_binary(self, pkg):
        """Check that all files in secured locations containing relevant
        entries are covered by a matching whitelisting entry.
        """
        if pkg.name in self.ignore_packages:
            return

        # Find all files in this package that fall in a tmpfiles.d drop-in directory
        for pkgfile in pkg.files.values():
            if not self._is_path_restricted(pkgfile):
                continue

            # now we know it's a systemd-tmpfiles configuration file

            if pkgfile.name in pkg.ghost_files:
                self.output.add_info('E', pkg, 'systemd-tmpfile-ghost', pkgfile.name)
                continue
            elif stat.S_ISLNK(pkgfile.mode):
                self.output.add_info('E', pkg, 'systemd-tmpfile-symlink', pkgfile.name)
                continue

            # parse the actual configuration file content
            entries = TmpfilesParser.parse(pkgfile)

            for entry in filter(lambda e: not e.is_valid(), entries):
                for warning in entry.get_warnings():
                    # collect any possible parse errors from the parser
                    self.output.add_info('E', pkg, 'systemd-tmpfile-parse-error', pkgfile.name, entry.get_line(), warning)

            # only consider security sensitive entries for whitelistings
            #
            # if no valid entry could be parsed then there's no point in
            # demanding a whitelisting, the parse-error above should be
            # emitted though.
            for entry in filter(lambda e: e.is_valid() and self._is_sensitive_entry(e), entries):
                # at this point we require a whitelisting for the sensitive
                # configuration entries we detected
                if self._check_for_whitelisting(pkg, pkgfile, entry):
                    continue

                # no whitelisting found, so emit a corresponding error
                self.output.add_info('E', pkg, 'systemd-tmpfile-entry-unauthorized', pkgfile.name, f'"{entry.get_line()}"')
