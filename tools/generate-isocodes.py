#!/usr/bin/python3

# Generate ISO codes for use with e.g. locale subdir checks
# http://alioth.debian.org/projects/pkg-isocodes/

import os
import sys
from pprint import pprint
from urllib.request import urlopen
from xml.etree.ElementTree import ElementTree


iso_3166_url = os.environ.get("ISO_3166_URL", "http://anonscm.debian.org/cgit/pkg-isocodes/iso-codes.git/plain/iso_3166/iso_3166.xml")
iso_639_url = os.environ.get("ISO_639_URL", "http://anonscm.debian.org/cgit/pkg-isocodes/iso-codes.git/plain/iso_639/iso_639.xml")
iso_639_3_url = os.environ.get("ISO_639_3_URL", "http://anonscm.debian.org/cgit/pkg-isocodes/iso-codes.git/plain/iso_639_3/iso_639_3.xml")

langs = set()
countries = set()

# 2-letter country codes
with urlopen(iso_3166_url) as f:
    for entry in ElementTree(file=f).findall("iso_3166_entry"):
        countries.add(entry.get("alpha_2_code"))

# 2-letter codes
with urlopen(iso_639_url) as f:
    for entry in ElementTree(file=f).findall("iso_639_entry"):
        for attr in ("iso_639_1_code", "iso_639_2T_code"):
            code = entry.get(attr)
            if code:
                langs.add(code)
                break

# Remaining 2-letter codes plus 3-letter ones for which we have no 2-letter one
with urlopen(iso_639_3_url) as f:
    for entry in ElementTree(file=f).findall("iso_639_3_entry"):
        code = entry.get("part1_code")
        if code:
            langs.add(code)
        if not code:
            langs.add(entry.get("id"))

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
