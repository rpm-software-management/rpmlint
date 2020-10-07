""" Enforce cron jobs in /etc/cron.* directories to be on a allow list """

from rpmlint.checks.Allowlisting import AbstractAllowlistCheck


class CronCheck(AbstractAllowlistCheck):
    allowlist_filenames = ('cron-whitelist.toml',)
    restricted_paths = (
        '/etc/cron.d/', '/etc/cron.hourly/', '/etc/cron.daily/',
        '/etc/cron.weekly/', '/etc/cron.monthly/'
    )
    error_map = {
        'unauthorized': 'cronjob-unauthorized-file',
        'changed': 'cronjob-changed-file',
        'ghost': 'cronjob-ghost-file'
    }
