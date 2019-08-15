from pathlib import Path
import re

from rpmlint.helpers import print_warning
import toml
from xdg.BaseDirectory import xdg_config_dirs


class Config(object):
    """
    Class wrapping testing loading and parsing.
    By default it loads all default locations and initializes basic testing
    layout for the rpmlint binary.
    Based on the opening order 'newer' configuration takes precedence over
    already existing one.
    """

    re_filter = re.compile(r'\s*addFilter\([\"\'](.*)[\"\']\)')
    re_badness = re.compile(r'\s*setBadness\([\'\"](.*)[\'\"],\s*[\'\"]?(\d+)[\'\"]?\)')
    config_defaults = Path(__file__).parent / 'configdefaults.toml'

    def __init__(self, config=None):
        # ordered list of configuration files we loaded
        # usefull when debugging where from we got all the config options
        self.conf_files = list()
        # Configuration content parsed from the ini file
        self.configuration = None
        # wether to print more informations or not
        self.info = False
        # wether to treat all messages as errors or not
        self.strict = False
        self.find_configs(config)
        self.load_config()
        # loading of the configuration failed fall back only to defaults
        if not self.configuration:
            # reset the configs only to defaults
            self.conf_files = [self.config_defaults]
            self.load_config()

    def set_badness(self, result, badness):
        """
        Set specific badness for some result
        """
        self.configuration['Scoring'][result] = badness

    def find_configs(self, config=None):
        """
        Load all the configuration files from XDG_CONFIG_DIRS.
        User can override and then that is added too.
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

    def print_config(self):
        """
        Just pretty print the current state of the config
        """
        if self.configuration:
            print(toml.dumps(self.configuration))

    def load_config(self, config=None):
        """
        Load the configuration files and append it to local dictionary with the
        content of already loaded options.
        """
        if config and config not in self.conf_files:
            # just add the config at the end of the list, someone injected
            # config file to us
            if config.exists():
                self.conf_files.append(config)
        try:
            cfg = toml.load(self.conf_files)
        except toml.decoder.TomlDecodeError as terr:
            print_warning(f'(none): W: error parsing configuration files: {terr}')
            cfg = None
        self.configuration = cfg

    def load_rpmlintrc(self, rpmlint_file):
        """
        Function to load up existing rpmlintrc files
        Only setBadness and addFilter are processed
        """
        rpmlintrc_content = rpmlint_file.read_text()
        filters = self.re_filter.findall(rpmlintrc_content)
        self.configuration['Filters'] += filters
        badness = self.re_badness.findall(rpmlintrc_content)
        for entry in badness:
            self.configuration['Scoring'].update({entry[0]: entry[1]})
