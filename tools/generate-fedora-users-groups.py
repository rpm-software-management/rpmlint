#!/usr/bin/python3
""" This script is used to generate values for
    config/Fedora/configs/Fedora/users-groups.toml
"""
import os
import re
users = set()
groups = set()
uidgid_regex = re.compile(r'^\s*(\S+)\s+(-|\d+)\s+(-|\d+|\(\d+\))\s')
for uidgid_file in ['/usr/share/doc/setup/uidgid']:
    if os.path.exists(uidgid_file):
        fobj = open(uidgid_file)
        try:
            for line in fobj.read().strip().splitlines():
                res = uidgid_regex.search(line)
                if res:
                    name = res.group(1)
                    if res.group(2) != '-':
                        users.add(name)
                    if res.group(3) != '-' and '(' not in res.group(3):
                        groups.add(name)
                del res
            del line
        finally:
            fobj.close()
        del fobj

print(users)

print(groups)
