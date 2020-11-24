from pathlib import Path
import re
import textwrap

from rpmlint.color import Color
from rpmlint.helpers import print_warning
import toml


class Filter(object):
    """
    Handle all printing/formatting/filtering of the rpmlint output.

    Nothing gets printed out until the end of all runs and all errors are
    sorted and formatted based on the rules specified by the user/config
    """

    def __init__(self, config):
        """
        Initialize options from configuration and load rpmlint descriptions.

        Args:
            config: Config object with parsed rpmlint configuration.
        """
        # badness stuff
        self.badness_threshold = config.configuration['BadnessThreshold']
        self.badness = config.configuration['Scoring']
        self.strict = config.strict
        # filters regular expression string, compiled from configuration[filter]
        self.filters_re = None
        self.non_named_group_re = re.compile(r'[^\\](\()[^:]')
        # compile filters regexp
        self._populate_filter_regexp(config.configuration['Filters'])
        # informative or quiet
        self.info = config.info
        # How many bad hits we already collected while collecting issues
        self.score = 0
        # Dictionary containing mapped values of descriptions for the errors.
        self.error_details = {}
        # Load it up with the toml descriptions
        self.error_details.update(self._load_descriptions())
        # Counter of how many issues we encountered
        self.printed_messages = {'I': 0, 'W': 0, 'E': 0}
        # Messages
        self.results = []

    @staticmethod
    def _load_descriptions():
        """
        Load rpmlint error/warning description texts from toml files.

        Detailed description for every rpmlint error/warning is stored in
        descriptions/<check_name>.toml file.

        Returns:
            A dictionary mapping error/warning/info names to their
            descriptions.
         """
        descriptions = {}
        descr_folder = Path(__file__).parent / 'descriptions'
        try:
            description_files = sorted(descr_folder.glob('*.toml'))
            descriptions = toml.load(description_files)
        except toml.decoder.TomlDecodeError as terr:
            print_warning(f'(none): W: unable to parse description files: {terr}')
        return descriptions

    def add_info(self, level, package, rpmlint_issue, *details):
        """
        Format rpmlint issue output and add it to self.results.

        It creates formatted and colored output consisting of all information
        about rpmlint issue given by the arguments.

        Args:
            level: A string with level of the rpmlint issue ('E' - Error,
                   'W' - Warning, 'I' - Info
            package: Pkg object representing processed package
            rpmlint_issue: A string representing the name of the rpmlint
                           issue
            *details: Details of the rpmlint issue
        """

        # filename in some cases can contain tmp paths and we don't need it
        # for the printout
        filename = Path(package.name).name
        # we can get badness treshold
        badness = None
        if rpmlint_issue in self.badness:
            badness = int(self.badness[rpmlint_issue])
            # If we have any badness configured then we 'stricten' and call the
            # result Error. Otherwise we downgrade the error to Warn.
            if badness > 0:
                level = 'E'
            elif level == 'E':
                level = 'W'
        # allow strict reporting where we override levels and treat everything
        # as an error
        if self.strict:
            level = 'E'

        if badness is None:
            badness = 1 if level == 'E' else 0
        # set coloring
        if level == 'E':
            lvl_color = Color.Red
        elif level == 'W':
            lvl_color = Color.Yellow
        else:
            lvl_color = Color.Bold
        # compile the message
        line = f'{package.current_linenum}:' if package.current_linenum else ''
        arch = f'.{package.arch}' if package.arch else ''
        bad_output = f' (Badness: {badness})' if badness > 1 else ''
        detail_output = ''
        for detail in details:
            if detail:
                detail_output += f' {detail}'
        result = f'{Color.Bold}{filename}{arch}:{line}{Color.Reset} {lvl_color}{level}: {rpmlint_issue}{Color.Reset}{bad_output}{detail_output}'

        # filter by the result message
        result_no_color = f'{filename}{arch}:{line} {level}: {rpmlint_issue}{detail_output}'
        if self.filters_re and self.filters_re.search(result_no_color):
            return

        # raise the counters
        self.score += badness
        self.printed_messages[level] += 1

        self.results.append(result)

    def print_results(self, results, config=None):
        """
        Provide all the information about the specified package.

        If there is description to be provided it needs to be provided only
        once per rpmlint_issue.

        Args:
            results: A list with rpmlint messages.
            config: parsed configuration file that is used as a source for
                    new description strings

        Returns:
            A string with final rpmlint output.
        """
        output = ''
        results.sort(key=self.__diag_sortkey, reverse=True)
        last_issue = ''
        for diag in results:
            if self.info:
                rpmlint_issue = diag.split()[2].rstrip(Color.Reset)
                # print out details for each rpmlint_issue we had
                if rpmlint_issue != last_issue:
                    if last_issue:
                        output += self.get_description(last_issue, config)
                    last_issue = rpmlint_issue
            output += diag + '\n'
        if self.info and last_issue:
            output += self.get_description(last_issue, config)
        # normalize the output as rpm 4.15 uses surrogates
        output = output.encode('utf-8', errors='surrogateescape').decode('utf-8', errors='replace')

        return output

    def get_description(self, rpmlint_issue, config=None):
        """
        Get description for specified rpmlint issue (error, warning or info).

        Args:
            rpmlint_issue: A string with the rpmlint error/warning/info name
            config: parsed configuration file that is used as a source for
                    custom description strings ([Descriptions] table in toml
                    syntax)

        Returns:
            A string with description for specified rpmlint issue. Empty
            content does not cause an issue and we just return empty content
        """
        description = ''
        if rpmlint_issue in self.error_details:

            # Update rpmlint error descriptions from configuration file
            if config and config.configuration.get('Descriptions').get(rpmlint_issue):
                self.error_details[rpmlint_issue] = config.configuration['Descriptions'][rpmlint_issue]

            # we need 2 enters at the end for whitespace purposes
            description = textwrap.fill(self.error_details[rpmlint_issue], 78, break_on_hyphens=False) + '\n\n'
        return description

    def _populate_filter_regexp(self, filters):
        """
        Generate regexp representing all rpmlint filters.

        From configuration "Filters" generate regexp that we will use later for
        results filtering/ignoring.
        """
        if not filters:
            return
        filters_re = '(?:' + filters[0] + ')'
        for idx in range(1, len(filters)):
            # to prevent named group overflow that happen when there is too
            # many () in a single regexp: AssertionError: sorry, but this
            # version only supports 100 named groups
            if '(' in filters[idx]:
                self.non_named_group_re.subn('(:?', filters[idx])
            filters_re = filters_re + '|(?:' + filters[idx] + ')'
        self.filters_re = re.compile(filters_re)

    def __diag_sortkey(self, x):
        """
        Sorting helper, xs[1] is packagename line architecture
                        xs[2] is the reason of the error
        """
        xs = x.split()
        return (xs[2], xs[1])
