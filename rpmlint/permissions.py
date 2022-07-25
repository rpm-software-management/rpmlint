import contextlib
import copy
import os


class ParseContext:
    def __init__(self, label):
        self.label = label
        self.active_entries = []


class PermissionsEntry:
    def __init__(self, profile, line_nr, path, owner, group, mode):
        # source profile path
        self.profile = profile
        # source profile line nr
        self.linenr = line_nr
        # target path
        self.path = path
        self.owner = owner
        self.group = group
        # mode as integer
        self.mode = mode
        self.caps = []
        # related paths from variable expansions
        self.related_paths = []

    def __str__(self):
        ret = f'{self.profile}:{self.linenr}: {self.path} {self.owner}:{self.group} {oct(self.mode)}'
        for cap in self.caps:
            ret += '\n+capability ' + cap

        for related in self.related_paths:
            ret += '\nrelated to ' + related

        return ret


class VariablesHandler:
    def __init__(self, variables_conf_path):
        self.variables = {}

        # this can happen during migration in OBS when the new permissions
        # package is not yet around
        with contextlib.suppress(FileNotFoundError), open(variables_conf_path) as fd:
            self._parse(variables_conf_path, fd)

    def _parse(self, label, fd):
        for nr, line in enumerate(fd.readlines(), 1):
            line = line.strip()

            if not line or line.startswith('#'):
                continue

            parts = line.split('=', 1)

            if len(parts) != 2:
                raise Exception(f'{label}:{nr}: parse error')

            varname = parts[0].strip()
            values = parts[1].split()
            # strip leading or trailing slashes
            values = [v.strip(os.path.sep) for v in values]

            self.variables[varname] = values

    def expand_paths(self, path):
        """Checks for %{...} variables in the given path and expands them, as
        necessary. Will return a list of expanded paths, will be only a single
        path if no variables are used."""

        ret = ['']

        for part in path.split(os.path.sep):
            if part.startswith('%{') and part.endswith('}'):
                # variable found
                variable = part[2:-1]
                try:
                    expansions = self.variables[variable]
                except KeyError:
                    raise Exception(f"Undeclared variable '{variable}' encountered in profile")

                new_ret = []
                for p in ret:
                    for value in expansions:
                        new_ret.append(os.path.sep.join([p, value]))

                ret = new_ret
            elif not part:
                # a leading slash, ignore
                continue
            else:
                # a regular, fixed string
                ret = [os.path.sep.join([p, part]) for p in ret]

        if path.endswith(os.path.sep):
            # restore trailing slashes since they signify that we
            # expect a directory
            ret = [p + os.path.sep for p in ret]

        return ret


class PermissionsParser:
    def __init__(self, var_handler, profile_path):
        self.var_handler = var_handler
        self.entries = {}

        with open(profile_path) as fd:
            self._parse_file(profile_path, fd)

    def _parse_file(self, label, fd):
        context = ParseContext(label)
        for nr, line in enumerate(fd.readlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            context.line_nr = nr
            self._parse_line(context, line)

    def _parse_line(self, context, line):
        if line.startswith('/') or line.startswith('%'):
            context.active_entries = []

            path, ownership, mode = line.split()
            # the format supports both "user.group" and
            # "user:group"
            owner, group = ownership.replace('.', ':').split(':')
            mode = int(mode, 8)
            entry = PermissionsEntry(context.label, context.line_nr, path, owner, group, mode)
            expanded = self.var_handler.expand_paths(path)

            for p in expanded:
                entry.path = p
                entry.related_paths = list(filter(lambda e: e != path, expanded))
                key = entry.path.rstrip(os.path.sep)
                if not key:
                    # this is the root node, keep the slash
                    key = '/'
                entry_copy = copy.deepcopy(entry)
                self.entries[key] = entry_copy
                context.active_entries.append(entry_copy)
        elif line.startswith('+'):
            # capability line
            _type, rest = line.split()
            _type = _type.lstrip('+')
            if _type != 'capabilities':
                raise Exception(f'Unexpected +[line] encountered in {context.label}:{context.line_nr}')

            caps = rest.split(',')
            if not context.active_entries:
                raise Exception(f'+capabilities line without active entries in {context.label}:{context.line_nr}')

            for entry in context.active_entries:
                entry.caps = caps
        else:
            raise Exception(f'Unexpected line encountered in {context.label}:{context.line_nr}')
