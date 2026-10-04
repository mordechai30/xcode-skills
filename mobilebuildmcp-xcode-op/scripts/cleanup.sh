#!/bin/bash
# Remove this skill's project artifacts; preserve top-level logs.
# Run only on explicit request, outside sandbox restrictions.
set -euo pipefail
if [[ $# -ne 1 ]]; then
  echo "Usage: cleanup.sh PROJECT_PACKAGE_OR_CONTAINING_FOLDER" >&2
  exit 2
fi
skill="mobilebuildmcp-xcode-op"
case "$1" in
  *.xcodeproj|*.xcworkspace) parent=$(dirname "$1") ;;
  *) parent="$1" ;;
esac
parent=$(cd "$parent" && pwd -P)
data="$parent/$skill"
if [[ -d "$data" ]]; then
  find "$data" -mindepth 1 -maxdepth 1 ! -name 'log-*.txt' -exec rm -rf -- {} +
fi
