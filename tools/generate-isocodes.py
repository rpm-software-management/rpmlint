#!/usr/bin/python3

# Generate ISO codes for use with e.g. locale subdir checks
# http://alioth.debian.org/projects/pkg-isocodes/

import sys
from pprint import pprint
from xml.etree.ElementTree import ElementTree


langs = set()
countries = set()

# 2-letter country codes
tree = ElementTree(file="/usr/share/xml/iso-codes/iso_3166.xml")
for entry in tree.findall("iso_3166_entry"):
    countries.add(entry.get("alpha_2_code"))

# 2-letter codes
tree = ElementTree(file="/usr/share/xml/iso-codes/iso_639.xml")
for entry in tree.findall("iso_639_entry"):
    for attr in ("iso_639_1_code", "iso_639_2T_code"):
        code = entry.get(attr)
        if code:
            langs.add(code)
            break

# Remaining 2-letter codes plus 3-letter ones for which we have no 2-letter one
tree = ElementTree(file="/usr/share/xml/iso-codes/iso_639_3.xml")
for entry in tree.findall("iso_639_3_entry"):
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
