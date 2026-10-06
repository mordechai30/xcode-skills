---
name: apple-mcp-xcode-op
description: Build, run, and debug macOS Xcode apps and SwiftPM executables with Apple Xcode MCP. Use for source breakpoints, inspection, Pause, Continue, Status, and owned-session termination.
---

# Apple Xcode MCP operations

**All scripts and CLI commands must run outside sandbox restrictions.**
Use one skill at a time, on one project, with one configuration. Run from this skill root or use the entrypoint's absolute path. Input paths resolve from your current directory.

| Action | Command | Effect |
|---|---|---|
| Build only | `./scripts/manager.py build CONTAINER --configuration CONFIG` | Build the selected configuration without launching. |
| Build and Run | `./scripts/manager.py run CONTAINER --configuration CONFIG [--no-debugger]` | Build and launch the selected product; Debug enables the debugger by default. |
| App state | `./scripts/manager.py status` | Report the owned app state. |
| Source breakpoint | `./scripts/manager.py set-breakpoint --file PATH --line NUMBER` | Set a source breakpoint; watch the running app when the breakpoint resolves. |
| Pause | `./scripts/manager.py pause` | Pause a running app in a debugger-enabled Debug session. |
| Continue | `./scripts/manager.py continue [--keep-breakpoint]` | Resume a paused app; remove the responsible owned breakpoint unless `--keep-breakpoint` is supplied. |
| Inspect | `./scripts/manager.py debugger-command --command "LLDB COMMAND" [--detail]` | Execute the requested LLDB command and return its output and errors. |
| Kill app and dedicated helpers | `./scripts/manager.py kill` | Terminate the owned app and verified dedicated helpers, including a dedicated headless parent; release the session. |
| Remove artifacts | `./scripts/cleanup.sh PROJECT_OR_PACKAGE_PATH` | Delete session files and build products in this skill's artifact folder; does not terminate processes. |

`CONTAINER` is exactly one of `--project PATH.xcodeproj`, `--workspace PATH.xcworkspace`, or `--package DIRECTORY` containing `Package.swift`. `CONFIG` is `Debug` or `Release`; it is required. Select Xcode with `--scheme NAME` and `--target NAME`; select a package with `--product NAME`. Unique choices are automatic. Follow-up commands need no selection inputs. Use `COMMAND --help` for a short summary.

Xcode and SwiftPM Debug reject launch/build overrides. Use saved scheme arguments. SwiftPM Release accepts `--arguments` and `--working-directory`.
Put `--arguments` last. Omitted arguments use enabled saved Xcode arguments or none for a package. An explicit list replaces them; a bare flag clears them. Unsupported options fail before Clean or Build.

Use "My Mac" as the destination for Build and Run. Debug enables the debugger unless `--no-debugger` is supplied; Release does not. Build never launches. Every Run builds once. Kill before another Build or Run. Failed or uncertain requests do not retry automatically.

A pending breakpoint returns immediately. A resolved breakpoint on a running app watches for a hit, other stop, exit, or interruption. Interrupting the watch does not change execution. Inspection requires a suitable paused frame. Pause has a 15-second submission limit. Continue removes the responsible owned breakpoint; `--keep-breakpoint` retains it and watches again. Unexpected stops require user instruction.

Responses contain a short result, relevant warnings/errors, and requested inspection data. Normal output is at most **200 UTF-8 bytes**; exceptional errors or `--detail` allow **500**, including newline and stderr. Omitted data is discarded. Use command responses for operation results.

`manager.py kill` terminates processes. `cleanup.sh PATH` deletes stored skill files. If an app session exists, complete `manager.py kill` before running `cleanup.sh PATH`.

Agents must not read scripts unless the user explicitly asks. Command help is brief; read [Arguments and examples](references/examples.md#arguments) for full options, route limits, and workflows. Read [Limits and recovery](references/backend.md#backend-limits) when an operation is incomplete.
