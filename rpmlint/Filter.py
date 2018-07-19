import re
import textwrap


class Filter(object):
    """
    Class containing all printing/formatting/filtering of the rpmlint output.
    Nothing gets printed out until the end of all runs and all errors are
    sorted and formatted based on the rules specified by the user/config
    """

    def __init__(self, config):
        # badness stuff
        self.badness_threshold = config.configuration['BadnessThreshold']
        self.badness = config.configuration['Scoring']
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
        # This must get populated by the tests for each of the issues it finds.
        # You can populate this by having conffile that generates the
        # dictionary content for you, or you can just pass the dictionary
        self.error_details = {}
        # Counter of how many issues we encountered
        self.printed_messages = {"I": 0, "W": 0, "E": 0}
        # Messages
        self.results = list()

    def add_info(self, level, package, reason, *details):
        """
        Add the issue to the store for later usage
        """
        # we can be completely filtered for the reason
        if self.filters_re and self.filters_re.search(reason):
            return

        # we can get badness treshold
        badness = 0
        if reason in self.badness:
            badness = int(self.badness[reason])
            # If we have any badness configured then we "stricten" and call the
            # result Error. Otherwise we downgrade the error to Warn.
            if badness > 0:
                level = 'E'
            elif badness <= 0 and level == 'E':
                level = 'W'
        # raise the counters
        self.score += badness
        self.printed_messages[level] += 1
        # compile the message
        line = '{}:'.format(package.current_linenum) if package.current_linenum else ''
        arch = '.{}'.format(package.arch) if package.arch else ''
        bad_output = ' (Badness: {})'.format(badness) if badness else ''
        detail_output = ''
        for detail in details:
            if detail:
                detail_output += ' {}'.format(detail)
        result = '{}{}:{} {}: {}'.format(package.name, arch, line, level, reason)
        result += bad_output
        result += detail_output
        self.results.append(result)

    def print_results(self, results):
        """
        Printout function to provide all the information about the specified
        package as a return content.
        If there is description to be provided it needs to be provided only
        once per reason.
        """
        output = ""
        results.sort(key=self.__diag_sortkey, reverse=True)
        last_reason = ''
        for diag in results:
            if self.info:
                reason = diag.split()[2]
                # print out details for each reason we had
                if reason != last_reason:
                    if last_reason:
                        output += self._get_description(last_reason)
                    last_reason = reason
            output += diag + '\n'
        if self.info and last_reason:
            output += self._get_description(last_reason)
        return output

    def _get_description(self, reason):
        """
        Return description for specified result.
        Empty content does not cause an issue and we just return empty content
        """
        description = ''
        if reason in self.error_details:
            # we need 2 enters at the end for whitespace purposes
            description = textwrap.fill(self.error_details[reason], 78) + '\n\n'
        return description

    def _populate_filter_regexp(self, filters):
        """
        From configuration Filters generate regexp we will use later for results
        filtering/ignoring.
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
