import json
import os
import os.path

import pytest
from rpmlint.checks.CronJobsCheck import CronCheck
from rpmlint.filter import Filter

from Testing import CONFIG, get_tested_package


@pytest.fixture(scope='function', autouse=True)
def cronjobscheck(tmpdir):
    CONFIG.info = True

    # make the cron check search for its allow list in 'tmpdir'
    CONFIG.configuration['WhitelistDataDir'] = [tmpdir]

    output = Filter(CONFIG)
    test = CronCheck(CONFIG, output)

    # make an empty allow list
    with open(os.path.join(tmpdir, test.allowlist_filenames[0]), 'w') as fd:
        json.dump({}, fd)

    return output, test


@pytest.mark.parametrize('package', ['binary/cronjobs'])
def test_cron_jobs(tmpdir, package, cronjobscheck):
    output, test = cronjobscheck
    test.check(get_tested_package(package, tmpdir))
    out = output.print_results(output.results)
    assert 'noproblem' not in out
    assert 'cronjob-unauthorized-file /etc/cron.d/job' in out
