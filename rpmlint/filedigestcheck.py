import configparser

# This module contains helper types used by the FileDigestCheck to implement
# configuration-specific logic.

# ContentCheck types
#
# The following types relate to the "ContentCheck" configuration setting,
# which allows to specify a class name in this module which will be invoked to
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

# Digester types

# We support different "filters" for calculating file digests for whitelisting
# purposes. The reasoning behind this is that we want to detect *functional*
# changes to certain files but we don't want to be bothered by any other
# changes like changes in comments, copyright headers, whitespace and so on.
#
# To avoid such bogus changes showing up in the checker we can filter the
# target files depending on their file type. Currently we have two common
# special cases:
#
# - shell-like files (configuration files, shell scripts, Python
# scripts, Perl scripts etc) that can contain empty lines or comments
# introduced by '#'.
# - XML files for things like D-Bus configuration files or polkit policies.
# Here also XML style comments and whitespace can occur.
#
# The filter classes help in calculating a file digest for a filtered version
# of the target file that is normalized and therefore stable against the
# outlined kinds of changes. Since this makes getting the right whitelisting
# digests hard, a small companion tool in tools/get_whitelisting_digest.py
# exists.


class DefaultDigester:
    """This class performs the default digest calculation of arbitrary file
    contents as is."""

    def __init__(self, path, halg):
        self.path = path
        self.halg = halg

    def parse_content(self):
        # simply generate chunks on binary level
        with open(self.path, 'rb') as fd:
            while True:
                chunk = fd.read(4096)
                if not chunk:
                    break
                yield chunk

    def get_digest(self):
        """This returns the hash digest of the *un*filtered input file."""
        import hashlib
        hasher = hashlib.new(self.halg)

        for chunk in self.parse_content():
            hasher.update(chunk)

        return hasher.hexdigest()


class ShellDigester(DefaultDigester):
    """This class performs digest calculation of shell style configuration
    files or scripts. Certain aspects like comments and whitespace will be
    filtered out of the digest calculation."""

    def parse_content(self):
        import re

        # generate filtered lines
        with open(self.path) as fd:
            for line_nr, line in enumerate(fd):
                stripped = line.strip()
                if not stripped:
                    # skip empty lines
                    continue
                elif line_nr == 0 and stripped.startswith('#!'):
                    # keep shebang lines mostly intact,
                    # but ignore minor interpreter versions
                    line = re.sub(r'\bpython3\.\d+\b', 'python3', line)
                elif stripped.startswith('#'):
                    # skip comments
                    # NOTE: we don't strip trailing comments like in
                    # 'if [ 5 -eq $NUM ]; then # compare to 5'
                    # because the danger would be too high to remove actual
                    # content instead of just comments
                    continue

                # don't use the completely stripped version, in Python for
                # example the indentation is part of the syntax and changes
                # here could change the meaning
                yield (line.rstrip() + '\n').encode()


class XmlDigester(DefaultDigester):
    """This class performs digest calculation of XML configuration files.
    Certain aspects like comments and whitespace will be filtered out of the
    digest calculation."""

    def parse_content(self):
        import xml.etree.ElementTree as ET
        # NOTE: the ElementTree is not robust against malicious input. Rpmlint
        # processes a lot of untrusted input. In the OBS context this only
        # happens within the virtual machines where packagers can manipulate a
        # lot of things anyway so it should be okay.

        # this returns a canonicalized form of the XML without comments or
        # anything. It is missing the XML preamble and DOCTYPE declaration,
        # though. It's as good as I could get it to be without parsing XML on
        # foot or relying on third party XML modules.

        # chunked / line wise processing is likely impossible for XML so
        # return the whole bunch
        yield ET.canonicalize(from_file=self.path, strip_text=True).encode()


class SocketUnitDigester(DefaultDigester):

    # [Socket] section configuration keys to include in the digest
    # calculation.
    #
    # see systemd.socket(5) man page for reference.
    #
    # we're only interested in settings related to API / permissions / network
    # entry points.
    KEYS_TO_HASH = {
        'ListenStream',
        'ListenDatagram',
        'ListenSequentialPacket',
        'ListenFIFO',
        'ListenSpecial',
        'ListenNetlink',
        'ListenMessageQueue',
        'SocketProtocol',
        'BindToDevice',
        'SocketUser',
        'SocketGroup',
        'SocketMode',
        'DirectoryMode',
        'PassSecurity',
        'AcceptFileDescriptors',
        'ExecStartPre',
        'ExecStartPost',
        'ExecStopPre',
        'ExecStopPost',
        'FileDescriptorName',
        'PassFileDescriptorsToExec'
    }

    def parse_content(self):
        config = _open_socket_config(self.path)

        if not config:
            # shouldn't happen since VarlinkServiceCheck above should have
            # already read the file successfully before.
            raise Exception(f'failed to parse {self.path}')

        try:
            socket_section = config['Socket']
        except KeyError:
            # VarlinkServiceCheck must have seen a [Socket] section so this
            # shouldn't happen.
            raise Exception(f'[Socket] section in {self.path} disappeared?')

        # yield all key/value pairs we're interested in for hashing
        for key in socket_section:
            if key in self.KEYS_TO_HASH:
                value = socket_section[key]
                yield f'{key}={value}\n'.encode()
