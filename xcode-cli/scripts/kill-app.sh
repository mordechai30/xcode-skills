#!/bin/bash
# Stop one host app by PID. Use --zombie-parent only after inspecting its parent.
# Uses macOS ps; TERM and KILL each have a bounded wait.
set -u

fail() { printf '%s\n' "$*" >&2; exit 1; }

# Read identity and state into shared fields for the next check.
# A missing process returns failure without sending a signal.
inspect() {
    local row
    row=$(/bin/ps -p "$1" -o ppid=,uid=,stat=,lstart= 2>/dev/null) || return 1
    read -r proc_parent proc_uid proc_state proc_start <<< "$row"
    [[ -n "$proc_start" ]]
}

# Reject service PID 1, this shell, ancestors, and another user's process.
# Check ownership at every signal, not only at argument validation.
validate() {
    [[ "$1" -gt 1 && "$protected" != *" $1 "* ]] || fail 'Refused protected PID'
    [[ "$proc_uid" == "$caller_uid" ]] || fail 'Refused other-user PID'
}

# Stop the selected identity with TERM, then KILL if it stays alive.
# Recheck start time before signals to reduce PID reuse risk.
stop_process() {
    local pid=$1 original sig attempt
    inspect "$pid" || return 0
    validate "$pid"
    original=$proc_start
    for sig in TERM KILL; do
        inspect "$pid" || return 0
        [[ "$proc_start" == "$original" && "$proc_state" != *Z* ]] || return 0
        validate "$pid"
        if ! kill -s "$sig" "$pid" 2>/dev/null; then
            inspect "$pid" || return 0
            [[ "$proc_start" == "$original" && "$proc_state" != *Z* ]] || return 0
            fail "Could not send $sig to PID $pid"
        fi
        for ((attempt=0; attempt<20; attempt++)); do
            /bin/sleep 0.1
            inspect "$pid" || return 0
            [[ "$proc_start" == "$original" && "$proc_state" != *Z* ]] || return 0
        done
    done
    fail 'Process remains after KILL'
}

if [[ $# == 1 && ( "$1" == --help || "$1" == -h ) ]]; then
    printf '%s\n' 'Usage: bash kill-app.sh APP_PID [--zombie-parent PARENT_PID]'
    exit 0
fi
[[ $# == 1 || ( $# == 3 && "$2" == --zombie-parent ) ]] || fail 'Usage: bash kill-app.sh APP_PID [--zombie-parent PARENT_PID]'
[[ "$1" =~ ^[1-9][0-9]{0,8}$ ]] || fail 'Invalid app PID'
app_pid=$1
parent_pid=${3:-}
[[ -z "$parent_pid" || "$parent_pid" =~ ^[1-9][0-9]{0,8}$ ]] || fail 'Invalid parent PID'
caller_uid=$(/usr/bin/id -u)
protected=" 1 $$ "
ancestor=$PPID
while [[ "$ancestor" -gt 1 && "$protected" != *" $ancestor "* ]]; do
    protected+=" $ancestor "
    inspect "$ancestor" || break
    ancestor=$proc_parent
done
[[ "$app_pid" -gt 1 && "$protected" != *" $app_pid "* ]] || fail 'Refused protected PID'
if ! inspect "$app_pid"; then
    printf '%s\n' 'App PID no longer exists'
    exit 0
fi
validate "$app_pid"
app_start=$proc_start
stop_process "$app_pid"
if inspect "$app_pid" && [[ "$proc_start" == "$app_start" && "$proc_state" == *Z* ]]; then
    [[ -n "$parent_pid" ]] || fail "Zombie parent is $proc_parent; inspect it and pass --zombie-parent"
    [[ "$parent_pid" == "$proc_parent" ]] || fail 'Zombie parent PID does not match'
    stop_process "$parent_pid"
    printf '%s\n' 'Stopped zombie parent; reaping is handled by the OS'
else
    printf '%s\n' 'App stopped'
fi
