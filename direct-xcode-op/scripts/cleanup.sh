#!/bin/bash
# Explicit artifact cleanup. Preserve operation logs; do not check or stop apps.
set -euo pipefail
failure() { printf 'Cleanup failed.\n'; }
trap failure ERR
if [[ $# -ne 1 ]]; then
  printf 'Cleanup failed. Provide one project, package, or containing folder.\n'
  exit 2
fi
skill="direct-xcode-op"
case "$1" in
  *.xcodeproj|*.xcworkspace) parent=$(dirname "$1") ;;
  *) parent="$1" ;;
esac
parent=$(cd "$parent" 2>/dev/null && pwd -P)
data="$parent/$skill"
if [[ -d "$data" ]]; then
  find "$data" -mindepth 1 -maxdepth 1 ! -name 'log-*.txt' -exec rm -rf -- {} +
fi
printf 'Cleanup succeeded.\n'
