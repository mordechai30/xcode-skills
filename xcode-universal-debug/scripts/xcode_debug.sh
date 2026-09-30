#!/usr/bin/env bash
set -euo pipefail

# Usage:
#   SCHEME=GL_renderer your_script.sh /path/to/project-root [--debug|--release|--logs|--telemetry|--verify|--clean|--kill] [--lldb|--release]

PROJECT_ROOT_INPUT="${1:?usage: $0 PROJECT_ROOT [--debug|--release|--logs|--telemetry|--verify|--clean|--kill] [--lldb|--release]}"
MODE="${2:---debug}"
EXTRA="${3:-}"
LLDB_MODE=""

if (( $# > 3 )); then
  echo "usage: $0 PROJECT_ROOT [--debug|--release|--logs|--telemetry|--verify|--clean|--kill] [--lldb|--release]" >&2
  exit 2
fi

case "$MODE" in
  --debug|debug) BUILD_TYPE="Debug" ;;
  --release|release) BUILD_TYPE="Release" ;;
  --log|log|--logs|logs|--telemetry|telemetry|--verify|verify) BUILD_TYPE="Debug" ;;
  --clean|clean|--kill|kill) BUILD_TYPE="Debug" ;;
  *)
    echo "usage: $0 PROJECT_ROOT [--debug|--release|--logs|--telemetry|--verify|--clean|--kill] [--lldb|--release]" >&2
    exit 2
    ;;
esac

if [[ "$MODE" == "--clean" || "$MODE" == "clean" ]]; then
  case "$EXTRA" in
    ""|--debug) ;;
    --release) BUILD_TYPE="Release" ;;
    *) echo "For --clean, use --debug or --release." >&2; exit 2 ;;
  esac
elif [[ -n "$EXTRA" ]]; then
  if [[ "$EXTRA" != "--lldb" || ( "$MODE" != "--debug" && "$MODE" != "debug" && "$MODE" != "--release" && "$MODE" != "release" ) ]]; then
    echo "--lldb is valid only with --debug or --release." >&2
    exit 2
  fi
  LLDB_MODE="$EXTRA"
fi

PROJECT_ROOT="$(cd -- "$PROJECT_ROOT_INPUT" && pwd -P)"
XCODE_DIR="$PROJECT_ROOT/xcode"
DERIVED_DATA="${DERIVED_DATA:-$PROJECT_ROOT/.build/xcode}"

[[ -d "$XCODE_DIR" ]] || {
  echo "Xcode directory not found: $XCODE_DIR" >&2
  exit 1
}

shopt -s nullglob
PROJECTS=("$XCODE_DIR"/*.xcodeproj)

if (( ${#PROJECTS[@]} != 1 )); then
  echo "Expected exactly one .xcodeproj in: $XCODE_DIR" >&2
  exit 1
fi

XCODE_CONTAINER=(-project "${PROJECTS[0]}")
PROJECT_NAME="$(basename "${PROJECTS[0]}" .xcodeproj)"

# Ask Xcode for the available schemes unless SCHEME was supplied.
if [[ -z "${SCHEME:-}" ]]; then
  SCHEMES=()

  while IFS= read -r scheme; do
    [[ -n "$scheme" ]] && SCHEMES+=("$scheme")
  done < <(
    xcrun xcodebuild "${XCODE_CONTAINER[@]}" -list 2>/dev/null |
      awk '
        /^[[:space:]]*Schemes:$/ { reading = 1; next }
        reading && /^[[:space:]]*$/ { next }
        reading {
          match($0, /^[ \t]*/)
          if (RLENGTH >= 8) {
            sub(/^[ \t]+/, "")
            print
          } else {
            exit
          }
        }
      '
  )

  if (( ${#SCHEMES[@]} > 1 )); then
    PROJECT_SCHEMES=()
    for scheme in "${SCHEMES[@]}"; do
      [[ "$scheme" == "$PROJECT_NAME" ]] && PROJECT_SCHEMES+=("$scheme")
    done
    (( ${#PROJECT_SCHEMES[@]} == 1 )) && SCHEMES=("${PROJECT_SCHEMES[0]}")
  fi

  if (( ${#SCHEMES[@]} != 1 )); then
    echo "Could not select one scheme; found ${#SCHEMES[@]}." >&2
    echo "Specify one, e.g.: SCHEME=GL_renderer $0 \"$PROJECT_ROOT\"" >&2
    exit 1
  fi

  SCHEME="${SCHEMES[0]}"
fi

if [[ "$MODE" == "--clean" || "$MODE" == "clean" ]]; then
  echo "Cleaning $BUILD_TYPE scheme '$SCHEME'..."
  xcrun xcodebuild \
    "${XCODE_CONTAINER[@]}" \
    -scheme "$SCHEME" \
    -configuration "$BUILD_TYPE" \
    -derivedDataPath "$DERIVED_DATA" \
    clean
  exit 0
fi

if [[ "$MODE" == "--kill" || "$MODE" == "kill" ]]; then
  echo "Resolving runnable product for scheme '$SCHEME'..."
else
  echo "Building $BUILD_TYPE scheme '$SCHEME'..."
fi

if [[ "$MODE" != "--kill" && "$MODE" != "kill" ]]; then
  xcrun xcodebuild \
    "${XCODE_CONTAINER[@]}" \
    -scheme "$SCHEME" \
    -configuration "$BUILD_TYPE" \
    -derivedDataPath "$DERIVED_DATA" \
    build
fi

# Ask Xcode for resolved paths rather than assuming a products directory.
BUILD_CANDIDATES="$(
  xcrun xcodebuild \
    "${XCODE_CONTAINER[@]}" \
    -scheme "$SCHEME" \
    -configuration "$BUILD_TYPE" \
    -derivedDataPath "$DERIVED_DATA" \
    -showBuildSettings |
  awk '
    function reset() {
      target_dir = ""
      wrapper_name = ""
      product_name = ""
      product_type = ""
      executable_path = ""
      bundle_id = ""
    }
    function emit_if_runnable() {
      if (target_dir != "" && executable_path != "" && wrapper_name ~ /\.app$/) {
        print target_dir "\t" wrapper_name "\t" executable_path "\t" bundle_id
      } else if (target_dir != "" && executable_path != "" && product_type == "com.apple.product-type.tool") {
        print target_dir "\t" product_name "\t" executable_path "\t" bundle_id
      }
    }
    /^Build settings for action / { emit_if_runnable(); reset(); next }
    /^[[:space:]]*TARGET_BUILD_DIR = / {
      sub(/^[[:space:]]*TARGET_BUILD_DIR = /, ""); target_dir = $0; next
    }
    /^[[:space:]]*WRAPPER_NAME = / {
      sub(/^[[:space:]]*WRAPPER_NAME = /, ""); wrapper_name = $0; next
    }
    /^[[:space:]]*PRODUCT_NAME = / {
      sub(/^[[:space:]]*PRODUCT_NAME = /, ""); product_name = $0; next
    }
    /^[[:space:]]*PRODUCT_TYPE = / {
      sub(/^[[:space:]]*PRODUCT_TYPE = /, ""); product_type = $0; next
    }
    /^[[:space:]]*EXECUTABLE_PATH = / {
      sub(/^[[:space:]]*EXECUTABLE_PATH = /, ""); executable_path = $0; next
    }
    /^[[:space:]]*PRODUCT_BUNDLE_IDENTIFIER = / {
      sub(/^[[:space:]]*PRODUCT_BUNDLE_IDENTIFIER = /, ""); bundle_id = $0; next
    }
    END { emit_if_runnable() }
  '
)"

REQUESTED_APP="${APP_NAME:-}"
REQUESTED_APP="${REQUESTED_APP%.app}"
MATCH_COUNT=0

while IFS=$'\t' read -r TARGET_BUILD_DIR WRAPPER_NAME EXECUTABLE_PATH BUNDLE_ID; do
  [[ -z "$TARGET_BUILD_DIR" ]] && continue

  DETECTED_APP_NAME="${WRAPPER_NAME%.app}"
  [[ -n "$REQUESTED_APP" && "$DETECTED_APP_NAME" != "$REQUESTED_APP" ]] && continue

  MATCH_COUNT=$((MATCH_COUNT + 1))
  APP_NAME="$DETECTED_APP_NAME"
  APP_BINARY="$TARGET_BUILD_DIR/$EXECUTABLE_PATH"
done <<< "$BUILD_CANDIDATES"

if (( MATCH_COUNT != 1 )); then
  echo "Expected one runnable product; found $MATCH_COUNT." >&2
  echo "If needed: APP_NAME=ProductName SCHEME=$SCHEME $0 \"$PROJECT_ROOT\"" >&2
  exit 1
fi

if [[ "$MODE" != "--kill" && "$MODE" != "kill" ]]; then
  [[ -x "$APP_BINARY" ]] || {
  echo "Built executable not found: $APP_BINARY" >&2
  exit 1
  }
fi

SUBSYSTEM="${SUBSYSTEM:-$BUNDLE_ID}"

# Find this product by its exact path. With no path, find the same product in this project's Xcode output.
find_app_pids() {
  local exact_path="${1:-}"
  ps -axo pid=,stat=,comm= | awk \
    -v exact="$exact_path" \
    -v root="$PROJECT_ROOT/xcode/" \
    -v name="$(basename "$APP_BINARY")" '
      $2 ~ /Z/ { next }
      {
        pid = $1
        command = $0
        sub(/^[[:space:]]*[0-9]+[[:space:]]+[^[:space:]]+[[:space:]]+/, "", command)
        if (exact != "") {
          if (command == exact) print pid
        } else if (index(command, root) == 1) {
          product = command
          sub(/^.*\//, "", product)
          if (product == name) print pid
        }
      }
    '
}

# Signal a direct debugger parent only after the app resists TERM and KILL.
stop_debugger_parents() {
  local exact_path="$1" app_pid parent_pid parent_command
  shift
  for app_pid in "$@"; do
    parent_pid="$(ps -p "$app_pid" -o ppid= 2>/dev/null | awk '{ print $1 }')"
    [[ "$parent_pid" =~ ^[0-9]+$ ]] || continue
    (( parent_pid > 1 )) || continue

    parent_command="$(ps -p "$parent_pid" -o comm= 2>/dev/null || true)"
    case "${parent_command##*/}" in
      debugserver|lldb) ;;
      *) continue ;;
    esac

    kill -TERM "$parent_pid" || true
    for _ in {1..20}; do
      [[ -z "$(find_app_pids "$exact_path")" ]] && return 0
      kill -0 "$parent_pid" >/dev/null 2>&1 || break
      sleep 0.1
    done

    if [[ -n "$(find_app_pids "$exact_path")" ]] && kill -0 "$parent_pid" >/dev/null 2>&1; then
      [[ "$(ps -p "$parent_pid" -o comm= 2>/dev/null || true)" == "$parent_command" ]] &&
        kill -KILL "$parent_pid" || true
    fi
  done
}

# Signal the app with TERM, then KILL. Try a verified debugger parent only if both fail.
terminate_app_pids() {
  local exact_path="$1" app_pids
  app_pids="$(find_app_pids "$exact_path")"
  [[ -n "$app_pids" ]] || return 0

  kill -TERM $app_pids || true
  for _ in {1..20}; do
    app_pids="$(find_app_pids "$exact_path")"
    [[ -z "$app_pids" ]] && return 0
    sleep 0.1
  done

  kill -KILL $app_pids || true
  for _ in {1..20}; do
    app_pids="$(find_app_pids "$exact_path")"
    [[ -z "$app_pids" ]] && return 0
    sleep 0.1
  done

  stop_debugger_parents "$exact_path" $app_pids
  for _ in {1..20}; do
    app_pids="$(find_app_pids "$exact_path")"
    [[ -z "$app_pids" ]] && return 0
    sleep 0.1
  done
  return 1
}

# Try the selected executable first, then other builds of this product in this project.
stop_app_processes() {
  local exact_pids related_pids pid
  exact_pids="$(find_app_pids "$APP_BINARY")"
  if [[ -n "$exact_pids" ]] && terminate_app_pids "$APP_BINARY"; then
    echo "Stopped '$APP_NAME' at $APP_BINARY."
    return 0
  fi

  related_pids="$(find_app_pids)"
  if [[ -z "$related_pids" ]]; then
    echo "No running '$APP_NAME' process found in $PROJECT_ROOT/xcode."
    return 0
  fi

  echo "Stopping related '$APP_NAME' processes in $PROJECT_ROOT/xcode..."
  if terminate_app_pids ""; then
    echo "Stopped related '$APP_NAME' processes."
    return 0
  fi
  echo "Could not stop all related '$APP_NAME' processes. Remaining processes:" >&2
  related_pids="$(find_app_pids)"
  for pid in $related_pids; do
    ps -p "$pid" -o pid=,ppid=,stat=,user=,comm= >&2 || true
  done
  return 1
}

start_app() {
  "$APP_BINARY" &
  APP_PID=$!
  echo "$APP_NAME is running (pid $APP_PID)"
}

if [[ "$MODE" == "--kill" || "$MODE" == "kill" ]]; then
  stop_app_processes
  exit $?
fi

stop_app_processes

case "$MODE" in
  --debug|debug|--release|release)
    if [[ "$LLDB_MODE" == "--lldb" ]]; then
      exec xcrun lldb \
        -o "process launch --stop-at-entry" \
        -o 'script print("App PID: {}".format(lldb.debugger.GetSelectedTarget().GetProcess().GetProcessID()))' \
        -o continue \
        -- "$APP_BINARY"
    fi
    start_app
    wait "$APP_PID"
    ;;
  --log|log|--logs|logs)
    start_app
    /usr/bin/log stream --info --style compact \
      --predicate "process == \"$(basename "$APP_BINARY")\""
    ;;
  --telemetry|telemetry)
    [[ -n "$SUBSYSTEM" ]] || {
      echo "No bundle ID found; set SUBSYSTEM=com.example.YourApp" >&2
      exit 1
    }
    start_app
    /usr/bin/log stream --info --style compact \
      --predicate "subsystem == \"$SUBSYSTEM\""
    ;;
  --verify|verify)
    start_app
    sleep 1
    kill -0 "$APP_PID"
    ;;
  *)
    echo "usage: $0 PROJECT_ROOT [--debug|--release|--logs|--telemetry|--verify|--kill] [--lldb]" >&2
    exit 2
    ;;
esac
