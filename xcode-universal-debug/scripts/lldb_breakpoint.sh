#!/usr/bin/env bash
set -euo pipefail

if (( $# != 3 )); then
  echo "usage: $0 APP_NAME SOURCE_FILE LINE" >&2
  exit 2
fi

APP_NAME="$1"
SOURCE_FILE="$2"
LINE="$3"

[[ "$APP_NAME" != */* ]] || APP_NAME="$(basename "$APP_NAME")"
[[ "$LINE" =~ ^[1-9][0-9]*$ ]] || {
  echo "LINE must be a positive integer: $LINE" >&2
  exit 2
}

PIDS="$(
  ps -axo pid=,stat=,comm= |
    awk -v name="$APP_NAME" '
      $2 ~ /Z/ { next }
      { process = $3; sub(/^.*\//, "", process); if (process == name) print $1 }
    '
)"
PID_COUNT="$(printf '%s\n' "$PIDS" | awk 'NF { count++ } END { print count + 0 }')"

if (( PID_COUNT == 0 )); then
  echo "No running process named '$APP_NAME' found." >&2
  exit 1
fi

if (( PID_COUNT != 1 )); then
  printf "Expected one '$APP_NAME' process; found %d: %s\n" "$PID_COUNT" "$PIDS" >&2
  exit 1
fi

PID="$PIDS"
echo "$APP_NAME PID: $PID"

kill -STOP "$PID" || {
  echo "Could not pause PID $PID." >&2
  exit 1
}
echo "Paused PID $PID. Attaching LLDB..."

if ! exec xcrun lldb -p "$PID" \
  -o "breakpoint set --file '$SOURCE_FILE' --line $LINE" \
  -o continue; then
  kill -CONT "$PID" >/dev/null 2>&1 || true
  echo "Could not attach LLDB. Resumed PID $PID." >&2
  exit 1
fi
