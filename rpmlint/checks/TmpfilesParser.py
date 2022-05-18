import shlex


# NOTE: for 'C' the table in the man page does not list permissions
# support but actually they *are* supported.
TYPES_WITH_PERMS = (
    'f', 'd', 'D', 'e',
    'v', 'q', 'Q', 'p', 'p+',
    'c', 'C', 'b', 'z', 'Z'
)


class TmpfilesEntry:
    """This type represents a single systemd-tmpfiles configuration file
    entry."""

    def __init__(self, source, line, comments):
        """Parses the given tmpfiles configuration line and stores the
        resulting information in the object.

        `source` is the configuration file name, `line` the line number of the
        entry to be parsed and `comments` is a list of context lines that
        likely belong to this entry."""
        self.source = source
        self.line = line
        self.comments = comments
        self.valid = False
        self.warnings = []
        self._parse()

    def _add_warning(self, msg):
        self.warnings.append(f'{self.source}:{self.line}: {msg}')

    def get_warnings(self):
        """Returns a list of parse errors/warnings that have been encountered
        during parsing the tmpfiles entry."""
        return self.warnings

    def _parse(self):
        # each field may be quoted, so use shell like parsing to cope with that
        fields = shlex.split(self.line)
        if len(fields) > 7:
            self._add_warning('Too many fields encountered')
            return
        elif len(fields) < 2:
            self._add_warning('Too few fields encountered')
            return

        self.type = fields[0]
        self.target = fields[1]

        findex = 2

        def next_field():
            nonlocal findex
            if findex >= len(fields):
                return None

            ret = fields[findex]
            findex += 1
            return ret if ret != '-' else None

        self.mode = next_field()
        self.owner = next_field()
        self.group = next_field()
        self.age = next_field()
        self.arg = next_field()

        if (self.mode or self.owner or self.group) and not self._supports_perms():
            self._add_warning("Permissions specified for entry type that doesn't support perms")

        self._normalize()
        self.valid = True

    def is_valid(self):
        """Returns whether a valid entry could be parsed."""
        return self.valid

    def _normalize(self):
        """Normalizes any data of the current entry for simplification."""
        # F is a deprecated form of 'f+'
        if self.type[0] == 'F':
            self.type = 'f+' + self.type[1:]

    def _supports_perms(self):
        """Returns whether the current tmpfiles entry supports a file
        permissions field."""
        return self.type[0] in TYPES_WITH_PERMS

    def _get_def_mode_label(self):
        return '-' if self._supports_perms() else 'N/A'

    def get_type(self):
        return self.type

    def get_config_file(self):
        return self.source

    def get_target_path(self):
        return self.target

    def has_default_mode(self):
        return self.mode is None

    def get_mode(self):
        if not self.mode:
            return self._get_def_mode_label()
        return self.mode

    def get_octal_mode(self):
        if not self.mode:
            raise Exception('No mode to convert into octal')
        mode = self.mode
        # this means that the mode is masked with the permissions of the
        # (maybe) already existing file, should not be too relevant for us so
        # ignore
        if mode.startswith('~'):
            mode = mode[1:]
        return int(mode, 8)

    def get_owner(self):
        if not self.owner:
            return self._get_def_mode_label()
        return self.owner

    def has_non_root_owner(self):
        if self.owner and self.owner != 'root':
            return True
        return False

    def get_group(self):
        if not self.group:
            return self._get_def_mode_label()
        return self._group

    def has_non_root_group(self):
        if self.group and self.group != 'root':
            return True
        return False

    def get_arg(self):
        """Returns the custom argument field, the meaning depends on the entry
        type."""
        return self._arg if self._args else '-'

    def get_comments(self):
        return self.comments

    def get_line(self):
        """Returns the full line (stripped of whitespace) that makes up the
        entry."""
        return self.line


def parse(pkgfile):
    """Parses the given systemd-tmpfiles.d configuration file and returns a
    list of TmpfilesEntry objects corresponding to the file's content."""
    entries = []
    context = []

    for line in open(pkgfile.path):
        line = line.strip()
        if not line:
            context = []
        elif line.startswith('#'):
            context.append(line)
        else:
            entry = TmpfilesEntry(pkgfile.name, line, context)
            entries.append(entry)
            context = []

    return entries
