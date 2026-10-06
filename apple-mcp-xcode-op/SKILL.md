---
name: apple-mcp-xcode-op
description: Build, run, and debug macOS Xcode apps and SwiftPM executables with Apple Xcode MCP. Use for source breakpoints, inspection, Pause, Continue, Status, and owned-session termination.
---

# Apple Xcode MCP operations

**All scripts and CLI commands must run outside sandbox restrictions.**
Use one skill at a time, on one project, with one configuration. Run from this skill root or use the entrypoint's absolute path. Input paths resolve from your current directory.

| Action | Command |
|---|---|
| Build only | `./scripts/manager.py build CONTAINER --configuration CONFIG` |
| Build and Run | `./scripts/manager.py run CONTAINER --configuration CONFIG [--no-debugger]` |
| App state | `./scripts/manager.py status` |
| Source breakpoint | `./scripts/manager.py set-breakpoint --file PATH --line NUMBER` |
| Pause | `./scripts/manager.py pause` |
| Continue | `./scripts/manager.py continue [--keep-breakpoint]` |
| Inspect | `./scripts/manager.py debugger-command --command "LLDB COMMAND" [--detail]` |
| Stop app | `./scripts/manager.py kill` |
| Remove artifacts | `./scripts/cleanup.sh PROJECT_OR_PACKAGE_PATH` |

`CONTAINER` is exactly one of `--project PATH.xcodeproj`, `--workspace PATH.xcworkspace`, or `--package DIRECTORY` containing `Package.swift`. `CONFIG` is `Debug` or `Release`; it is required. Select Xcode with `--scheme NAME` and `--target NAME`; select a package with `--product NAME`. Unique choices are automatic. Follow-up commands need no selection inputs. Use `COMMAND --help` for its inputs.

Xcode and SwiftPM Debug reject launch/build overrides. Use saved scheme arguments. SwiftPM Release accepts `--arguments` and `--working-directory`.
Put `--arguments` last. Omitted arguments use enabled saved Xcode arguments or none for a package. An explicit list replaces them; a bare flag clears them. Unsupported options fail before Build.

Run uses discovered **My Mac**. **Any Mac** and generic destinations are Build-only. Debug enables the debugger unless `--no-debugger` is supplied; Release does not. Build never launches. Every Run builds once. Build and Run use incremental builds. Kill before another Build or Run. Failed or uncertain requests do not retry automatically.

A pending breakpoint returns immediately. A resolved breakpoint on a running app watches for a hit, other stop, exit, or interruption. Interrupting the watch does not change execution. Inspection requires a suitable paused frame. Pause has a 15-second submission limit. Continue removes the responsible owned breakpoint; `--keep-breakpoint` retains it and watches again. Unexpected stops require user instruction.

Responses contain a short result, relevant warnings/errors, and requested inspection data. Normal output is at most **200 UTF-8 bytes**; exceptional errors or `--detail` allow **500**, including newline and stderr. Omitted data is discarded. Use command responses for operation results.

Kill stops the owned app and dedicated helpers. Cleanup is separate, explicit, and does not stop processes.

Read [Arguments and examples](references/examples.md#arguments) for options and workflows, or [Limits and recovery](references/backend.md#backend-limits) when an operation is incomplete.
