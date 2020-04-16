from pathlib import Path
import re

from rpmlint.helpers import print_warning
import toml
from xdg.BaseDirectory import xdg_config_dirs


class Config(object):
    """
    Load and parse rpmlint configuration.

    Configuration files are written in toml and should be placed in one of
    the XDG_CONFIG_DIRS directory or passed as "config" argument directly.

    By default it loads configdefaults.toml and all default locations and
    initializes basic testing layout for the rpmlint binary. Based on the
    opening order 'newer' configuration takes precedence over already
    existing one.
    """

    re_filter = re.compile(r'\s*addFilter\([\"\'](.*)[\"\']\)')
    re_badness = re.compile(r'\s*setBadness\([\'\"](.*)[\'\"],\s*[\'\"]?(\d+)[\'\"]?\)')
    config_defaults = Path(__file__).parent / 'configdefaults.toml'

    def __init__(self, config=None):
        """Initialize basic options and load rpmlint configuration."""
        # ordered list of configuration files we loaded
        # useful when debugging where from we got all the config options
        self.conf_files = []
        # Configuration content parsed from the toml configuration file
        self.configuration = None
        # whether to print more information or not
        self.info = False
        # whether to treat all messages as errors or not
        self.strict = False
        # whether to treat individual errors as non-fatal
        self.permissive = False

        # find configuration files and load them
        self.find_configs(config)
        self.load_config()
        # if loading of the configuration failed -> fall back only to defaults
        if not self.configuration:
            # reset the configs only to defaults
            self.conf_files = [self.config_defaults]
            self.load_config()

    def find_configs(self, config=None):
        """
        Find and store paths to all config files.

        It searches for default configuration, files in XDG_CONFIG_DIRS and
        user defined configuration (argument "config"). All configuration
        file paths found are then stored in self.conf_files variable.
        XDG_CONFIG_DIRS contains preference-ordered set of base directories
        to search for configuration files. Users can override it by their
        own configuration file (config parameter) and then that is
        added too.
        """
        # first load up the file that contains defaults
        self.conf_files.append(self.config_defaults)

        # Then load up config directories on system
        for directory in reversed(xdg_config_dirs):
            confdir = Path(directory) / 'rpmlint'
            if confdir.is_dir():
                # load all configs in the folders
                confopts = sorted(confdir.glob('*config'))
                self.conf_files += confopts

        # As a last item load up the user configuration
        if config:
            if config.exists():
                # load this only if it really exist
                self.conf_files.append(config)
            else:
                print_warning('(none): W: error locating user requested configuration: {}'.format(config))

    def load_config(self, config=None):
        """
        Load the configuration files and append it to local dictionary.

        It's stored in self.configuration with the content of already loaded
        options.
        """
        if config and config not in self.conf_files:
            # just add the new config at the end of the list, someone injected
            # config file to us
            if config.exists():
                self.conf_files.append(config)
        try:
            cfg = toml.load(self.conf_files)
        except toml.decoder.TomlDecodeError as terr:
            print_warning(f'(none): W: error parsing configuration files: {terr}')
            cfg = None
        self.configuration = cfg

    def load_rpmlintrc(self, rpmlintrc_file):
        """
        Load existing rpmlintrc files.

        Only setBadness and addFilter are processed.
        """
        rpmlintrc_content = rpmlintrc_file.read_text()
        filters = self.re_filter.findall(rpmlintrc_content)
        self.configuration['Filters'] += filters
        badness = self.re_badness.findall(rpmlintrc_content)
        for entry in badness:
            self.configuration['Scoring'].update({entry[0]: entry[1]})

    def print_config(self):
        """Print the current state of the configuration."""
        if self.configuration:
            print(toml.dumps(self.configuration))

    def set_badness(self, result, badness):
        """Set specific badness for some result."""
        self.configuration['Scoring'][result] = badness
