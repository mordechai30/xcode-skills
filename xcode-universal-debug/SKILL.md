---
name: xcode-universal-debug
description: Build, run, clean, stop, debug, log or conduct telemetry for macOS Xcode apps.
---


# How to

All scripts (Python, Bash) and CLI commands must be run outside sandbox restrictions.

## Crucial assumptions:

**Project root has an `xcode` folder containing the Xcode project (`.xcodeproj`).**.   
- check whether the root of the repo has 'xcode/*.xcodeproj'
```bash
find root/xcode -maxdepth 1 -name '*.xcodeproj' -print -quit | grep -q .
```
- If the above command returns non-zero, surface its message.

## Running the script with arguments

run [`scripts/xcode_debug.sh`](./scripts/xcode_debug.sh) with the following parameters (see [`references/examples.md`](references/examples.md)):

1. first argument, (mandatory) path of the repo root with an `xcode/*.xcodeproj` project.

2. second argument, an operation (optional, default is `--debug`):

* `--debug`
* `--release`
* `--logs`
* `--telemetry`
* `--verify`
* `--clean` — clean Debug without building or running; add `--release` as the third argument to clean Release
* `--kill` — stop a previously running app without building it

3. third argument, when needed:

* `--lldb` with `--debug` or `--release`
* `--debug` or `--release` with `--clean`

For `--kill` and before a new launch, the script first stops processes with
the resolved executable path. If that fails or finds none, it stops matching
products within this project's `xcode/` tree. It sends TERM to the app,
then KILL if the app remains. Only if both fail does it signal a verified
direct debugger parent. It does not signal other parents. On failure it
reports signal errors and the surviving app process details.


## Extra variable

Set this variable for extra control:
* SCHEME: the Xcode scheme to build and run. If not set, the script will try to find a scheme automatically.


## How to choose second and third arguments for the script:

- User wants to build and run the app, use `--debug` or `--release`. (or nothing).
- User mentions lldb explicitly, then use `--lldb` too.
- User does not explicitly mention lldb but wants to inspect a file, function, variable, or set breakpoint, use Debug with `--lldb`.


## Debug the running app


### App already controlled by LLDB

If the app is already stopped at the LLDB prompt, set the breakpoint and
continue:

```lldb
breakpoint set -f /absolute/path/SceneManager.cpp -l 171
continue
```

If the app is running, use a separate terminal to pause the PID printed by the
launcher:

```bash
kill -STOP <pid>
```

Then set the breakpoint at the LLDB prompt and use `continue`.

### App not controlled by LLDB

Use the helper: [`scripts/lldb_breakpoint.sh`](./scripts/lldb_breakpoint.sh)  
Must receive three arguments:
* app name
* absolute path to the source file
* line number

```bash
~/.agents/skills/xcode-universal-debug/scripts/lldb_breakpoint.sh \
  MyApp /absolute/path/SceneManager.cpp 171
```
