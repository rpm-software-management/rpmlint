#!/usr/bin/python3
import argparse
import os
import sys

# make rpmlint modules available
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

import rpmlint.checks.FileDigestCheck as fdc  # noqa: E402

parser = argparse.ArgumentParser(
    description='This tool helps calculating whitelisting digests for the FileDigestCheck'
)
parser.add_argument('--filter', choices=list(fdc.DIGESTERS.keys()), required=True)
parser.add_argument('--show-result',
                    help='Instead of print the resulting digest, show the filtered file data',
                    action='store_true')
parser.add_argument('FILE')

args = parser.parse_args()

if args.filter == 'default' and args.show_result:
    print('Cannot output result data for default digester (which is binary)', file=sys.stderr)
    sys.exit(1)

Digester = fdc.DIGESTERS.get(args.filter, fdc.DefaultDigester)

digester = Digester(args.FILE, fdc.DEFAULT_DIGEST_ALG)

if args.show_result:
    for chunk in digester.parse_content():
        print(chunk.decode('utf8'), end='')
else:
    print(digester.get_digest())
