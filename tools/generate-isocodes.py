#!/usr/bin/python3

# Generate ISO codes for use with e.g. locale subdir checks
# http://alioth.debian.org/projects/pkg-isocodes/

import codecs
import json
import os
from pprint import pprint
import sys
from urllib.request import urlopen


iso_3166_1_url = os.environ.get("ISO_3166_1_URL", "http://anonscm.debian.org/cgit/pkg-isocodes/iso-codes.git/plain/data/iso_3166-1.json")
iso_639_3_url = os.environ.get("ISO_639_3_URL", "http://anonscm.debian.org/cgit/pkg-isocodes/iso-codes.git/plain/data/iso_639-3.json")

langs = set()
countries = set()

# country codes (2 letters)
with urlopen(iso_3166_1_url) as f:
    data = json.load(codecs.getreader("utf-8")(f))
    for entry in data["3166-1"]:
        countries.add(entry["alpha_2"])

# language codes (2 or 3 letters, 3 only for ones we don't have 2-letter one)
with urlopen(iso_639_3_url) as f:
    data = json.load(codecs.getreader("utf-8")(f))
    for entry in data["639-3"]:
        langs.add(entry.get("alpha_2") or entry["alpha_3"])

# Note that we are not pprint()ing the set directly because with
# Python 3 it results in curly brace set initializers that are not
# compatible with Python 2.6, do it with set([...]) instead.

print("# Generated with %s" % sys.argv[0])
print("")
print("LANGUAGES = set(")
pprint(sorted(langs))
print(")")
print("")
print("COUNTRIES = set(")
pprint(sorted(countries))
print(")")
