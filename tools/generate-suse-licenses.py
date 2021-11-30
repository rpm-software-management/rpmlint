#!/usr/bin/python3

import os

import requests

SUSE_EXCEPTIONS = """
AGPL-3.0 AGPL-3.0+ GFDL-1.1 GFDL-1.1+ GFDL-1.2 GFDL-1.2+ GFDL-1.3 GFDL-1.3+ GPL-3.0-with-GCC-exception \
GPL-2.0-with-classpath-exception GPL-2.0-with-font-exception SUSE-LGPL-2.1+-with-GCC-exception SUSE-NonFree \
GPL-1.0+ GPL-1.0 GPL-2.0+ GPL-2.0 GPL-3.0+ GPL-3.0 LGPL-2.0 LGPL-2.0+ LGPL-2.1+ LGPL-2.1 LGPL-3.0+ LGPL-3.0
"""
IGNORED_FOR_PLUS = (' with ', '-with-', ' or ')

licenses = requests.get('https://raw.githubusercontent.com/openSUSE/obs-service-format_spec_file/master/licenses_changes.txt')

with open('../configs/openSUSE/licenses.toml', 'w') as wfile:
    script_name = os.path.basename(__file__)
    wfile.write('# Generated with %s script:\n' % script_name)
    wfile.write('ValidLicenses = [\n')
    added = set()
    for line in licenses.text.splitlines():
        if line == 'First line':
            continue
        name = line.strip().split('\t')[0]
        if name not in added:
            wfile.write(f'    "{name}",\n')
            added.add(name)

        if not name.endswith('+') and not any(i in name.lower() for i in IGNORED_FOR_PLUS):
            plus_name = f'{name}+'
            if plus_name not in added:
                wfile.write(f'    "{plus_name}",\n')
                added.add(plus_name)
    wfile.write('    # SUSE EXCEPTIONS\n')
    for name in SUSE_EXCEPTIONS.strip().split(' '):
        wfile.write(f'    "{name}",\n')
    wfile.write(']\n')
