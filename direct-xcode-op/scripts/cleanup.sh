#!/bin/bash
# Remove explicit skill artifacts after the caller completes owned-process termination.
# Preserve regular top-level logs and reject workspace paths with ambiguous artifact ownership.
set -euo pipefail

# Report an unexpected removal failure without claiming successful cleanup.
# The ERR trap covers filesystem errors from path resolution and deletion.
failure() { printf 'Cleanup failed.\n'; }
trap failure ERR
if [[ $# -ne 1 ]]; then
  printf 'Cleanup failed. Provide one owning project, package, or containing folder.\n'
  exit 2
fi
input="${1%/}"
if [[ "$input" == *.xcworkspace ]]; then
  printf 'Cleanup failed. Supply the selected target owning .xcodeproj or its containing folder.\n'
  exit 2
fi
if [[ ! -d "$input" ]]; then
  printf 'Cleanup failed. The supplied project/package/folder does not exist.\n'
  exit 2
fi
skill="direct-xcode-op"
case "$input" in
  *.xcodeproj) parent=$(dirname "$input") ;;
  *) parent="$input" ;;
esac
parent=$(cd "$parent" && pwd -P)
data="$parent/$skill"
if [[ -L "$data" ]]; then
  printf 'Cleanup failed. Artifact folder must not be a symbolic link.\n'
  exit 2
fi
if [[ ! -d "$data" ]]; then
  printf 'Cleanup: no artifacts found.\n'
  exit 0
fi
find "$data" -mindepth 1 -maxdepth 1 ! \( -type f -name 'log-*.txt' \) -exec rm -rf -- {} +
printf 'Cleanup succeeded.\n'
