#!/usr/bin/env python3
"""Set the Run configuration in one Xcode scheme.
Preserve all other scheme text and reject ambiguous LaunchAction entries.
"""
import argparse
from pathlib import Path
import re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--scheme-file', type=Path, required=True)
parser.add_argument('--configuration', choices=('Debug', 'Release'), required=True)
args = parser.parse_args()
text = args.scheme_file.read_bytes().decode('utf-8')
pattern = r'(<LaunchAction\b[^>]*\bbuildConfiguration\s*=\s*")([^"]+)(")'
matches = list(re.finditer(pattern, text))
if len(matches) != 1:
    parser.error('Expected one LaunchAction with a buildConfiguration attribute.')
match = matches[0]
args.scheme_file.write_bytes((text[:match.start(2)] + args.configuration + text[match.end(2):]).encode('utf-8'))
print(f'Run configuration: {match.group(2)} -> {args.configuration}')
