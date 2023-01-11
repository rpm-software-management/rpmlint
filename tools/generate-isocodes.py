#!/usr/bin/python3

# Generate ISO codes for use with e.g. locale subdir checks
# http://alioth.debian.org/projects/pkg-isocodes/

import codecs
import json
import os
from pprint import pprint
import sys
from urllib.request import urlopen


iso_3166_1_url = os.environ.get('ISO_3166_1_URL', 'https://salsa.debian.org/iso-codes-team/iso-codes/raw/main/data/iso_3166-1.json')
iso_639_3_url = os.environ.get('ISO_639_3_URL', 'https://salsa.debian.org/iso-codes-team/iso-codes/raw/main/data/iso_639-3.json')
iso_639_2_url = os.environ.get('ISO_639_2_URL', 'https://salsa.debian.org/iso-codes-team/iso-codes/raw/main/data/iso_639-2.json')

langs = set()
countries = set()

# country codes (2 letters)
with urlopen(iso_3166_1_url) as f:
    data = json.load(codecs.getreader('utf-8')(f))
    for entry in data['3166-1']:
        countries.add(entry['alpha_2'])

# language codes (2 or 3 letters, 3 only for ones we don't have 2-letter one)
with urlopen(iso_639_3_url) as f:
    data = json.load(codecs.getreader('utf-8')(f))
    for entry in data['639-3']:
        langs.add(entry.get('alpha_2') or entry['alpha_3'])
# Need to check iso-639-2 for collective language codes not in iso-639-3
with urlopen(iso_639_2_url) as f:
    data = json.load(codecs.getreader('utf-8')(f))
    for entry in data['639-2']:
        entry_code = entry.get('alpha_2') or entry['alpha_3']
        if entry_code not in langs:
            langs.add(entry_code)

print(f'# Generated with {sys.argv[0]}')
print('')
print('LANGUAGES = \\')
pprint(langs)
print('')
print('COUNTRIES = \\')
pprint(countries)
