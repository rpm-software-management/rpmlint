import configparser

# This module contains helper types used by the FileDigestCheck to implement
# configuration-specific logic.
#
# Currently this relates to the "ContentCheck" configuration setting, which
# allows to specify a class name in this module which will be invoked to
# determine whether the whitelisting restriction should be applied to a
# specific file. A type needs to provide a is_restricted(self, path: str)
# member function to be usable as "ContentCheck".


def _open_socket_config(path):
    """Opens a systemd .socket unit in `path` as an INI configuration file and
    returns the ConfigParser instance resulting from it. On error None is
    returned."""
    # systemd services files are not 100 % compatible with regular INI
    # files, thus we make python's configparser a bit more relaxed.
    config = configparser.ConfigParser(
        interpolation=None,
        strict=False
    )

    # by default option keys are converted to lower-case, we don't want that
    config.optionxform = lambda opt: opt

    read = config.read(path)
    if len(read) == 1:
        return config

    return None


class VarlinkServiceCheck:
    """Checks a systemd .socket unit file whether it refers to a Varlink
    service."""

    def is_restricted(self, path: str):

        config = _open_socket_config(path)

        if not config:
            # failed to parse the file, assume it is restricted
            return True

        try:
            socket_section = config['Socket']
        except KeyError:
            # no socket section in a socket unit? not Varlink anyway.
            return False

        try:
            file_descriptor_name = socket_section['FileDescriptorName']
        except KeyError:
            # no varlink service
            return False

        # this is more of a convention, not a hard requirement, but so far all
        # Varlink services we have use this scheme.
        return file_descriptor_name == 'varlink'
