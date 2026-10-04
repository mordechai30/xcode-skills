---
name: mobilebuildmcp-xcode-op
description: Build, run, and control macOS Xcode apps and SwiftPM executables through MobileBuildMCP macOS and Apple bridge, with source breakpoints, inspection, Pause, Continue, and complete session termination.
---

# MobileBuildMCP macOS and Apple bridge operations

All scripts (Python, Bash) and CLI commands must run outside sandbox restrictions.

Use `scripts/manager.py` for the requested operation. The manager imports separate operation modules. Each package has its own lifecycle code. This skill supports macOS projects, workspaces, and SwiftPM executable products. UI interaction and other Apple platforms are deferred.

Each skill operates on one project and one configuration at a time. It creates the debugger session or backend connection used by its subsequent operations. Follow-up operations use only that connection and app session. Do not adopt or attach to an externally created debugger session.

## Requests

```text
python3 scripts/manager.py build --project /path/App.xcodeproj --configuration Debug
python3 scripts/manager.py run --workspace /path/App.xcworkspace --configuration Release
python3 scripts/manager.py build --package /path/Package --configuration Debug --product App
python3 scripts/manager.py run --package /path/Package --configuration Release --arguments --stay-alive
python3 scripts/manager.py set-breakpoint --file /path/App.cpp --line 120
python3 scripts/manager.py debugger-command --command "frame variable width"
python3 scripts/manager.py debugger-command --command "thread backtrace"
python3 scripts/manager.py pause
python3 scripts/manager.py continue --keep-breakpoint
python3 scripts/manager.py kill
```

Build and Run require one container and Debug or Release configuration. Use `--project`, `--workspace`, or `--package` (directory or Package.swift). Use `--scheme`, `--target` (alias `--product`), and `--destination` to resolve choices. Optional `--derived-data` controls Xcode Build locations. For native and debugger-free Mobile package launches, place `--arguments` last and supply executable arguments after it. Use `--no-debugger` only to disable Debug attachment. Follow-up operations need no session ID or repeated project selection.

SwiftPM route: Use package Build/Clean/Run tools. Debugger-enabled Debug Run uses the retained Apple bridge; it has no launch-argument input, so reject supplied arguments. Debugger-free Debug and Release use package Run with arguments. Use live configuration fields or supported session defaults. Do not create a configuration scheme without a suitable saved source. Product paths come from SwiftPM's bin-path query or the actual Apple linker log, never an assumed .build/debug layout.

## Operation rules

- Build uses the selected configuration and never launches. Each invoked Build has an exact-format log. Clean is required before the first Build, more than one hour after the last invoked Build, or after an incomplete required Clean. Exactly one hour does not trigger Clean. Failed prerequisite Clean prevents Build and leaves the timer unchanged. Failed Build performs Clean and waits; do not retry automatically.
- Run may Build every time, using the simplest supported route. Native builds then launches; Apple RunProject and Mobile package Run embed Build. Apply preparation and failure rules once to each Build attempt. Debug uses LLDB by default. Release has no debugger. Record Build and launch results separately.
- One active context blocks Build and another Run. Offer Kill and wait. Switching requires app termination and required dedicated debugger/helper cleanup.
- Set Breakpoint requires an existing source file and positive line. Report requested and resolved locations. A relocated line is valid and must be disclosed. Keep pending breakpoints and ask. Resolution is not a hit. Watch a resolved breakpoint until hit, another stop, exit, interruption, or lost connection. On a hit report the actual source, thread, frame, and stop cause, then wait for user input. Do not automatically Continue.
- Pause interrupts a running debugger-enabled Debug session and verifies the stop.
- Continue requires paused Debug execution. Remove only the responsible session breakpoint unless retention is requested. Preserve other breakpoints. Delete none for manual or runtime pauses. Ask if the responsible breakpoint is ambiguous. A retained breakpoint watches again.
- Inspection forwards the requested command through the retained connection and records its current output. Present available values and stacks regardless of earlier changes. Report unavailable or optimized-out values. Use manager Continue and Kill when the user requests those operations. Do not implement a command classifier or comprehensive LLDB interpreter.
- Kill removes the skill's recorded session breakpoints while its debugger connection is usable. Process termination remains app-first: use the owning backend, verify disappearance, and use verified TERM/KILL fallback if required. For a zombie, try appropriate parent cleanup. Close dedicated non-IDE debugger parents/helpers even after app exit. Ask before terminating a shared IDE/service or unrelated parent. Protect PID 1, system services, caller ancestors, and reused identities. After verified process cleanup, release the context even if breakpoint removal was not verified; warn that an IDE breakpoint may remain. Report app, zombie, helper, breakpoint, and incomplete process cleanup separately.

## Results and artifacts

Read the JSON result. `success` requires evidence; `needs_user_input`, `failure`, and `uncertain` require an accurate explanation and user direction. Keep raw backend results. Do not claim success from a wrapper exit or empty error list alone. Reconcile uncertain launches before another Run. Unexpected runtime stops wait for user input; do not change sanitizer settings.

Retain the connection throughout the active session. A lost connection stops debugger operations. Preserve process records and logs; offer verified Kill or wait. Do not attach another debugger or relaunch.

For `/path/App.xcodeproj`, artifacts belong in `/path/mobilebuildmcp-xcode-op/`. A workspace uses the selected app target's owning project. A Swift package uses `/path/Package/mobilebuildmcp-xcode-op/`. Top-level logs use `log-mobilebuildmcp-xcode-op-Debug-YY-MM-DD-HH-MM-SS.txt` or Release, local time, with timezone inside. Session activity appends to its Build/launch log. Build age uses the filename, never modification time.

Use suitable saved schemes. When configuration requires a copy, retain `source-mobilebuildmcp-xcode-op-configuration` in the source scheme directory, number unsuitable collisions, and preserve the original and unrelated settings. Ask if saved sources are absent or ambiguous.

`bash scripts/cleanup.sh /path/App.xcodeproj` removes non-log content from this skill's project folder. It performs no session checks. Never invoke cleanup automatically. It does not remove schemes or build products outside that folder.

Installed help and live schemas determine supported backend arguments. Each adapter request is limited to 60 seconds; native compilation has a separate deadline. Reference versions are examples, not fixed contracts. Do not modify application source or commit without a request. Use the small C++ and Objective-C++ apps and a SwiftPM executable for acceptance. Fixture paths and values are never production defaults. Xcode executable launches preserve enabled arguments from the selected saved scheme.


Read the following section when when checking backend interfaces or implementation examples.

# MobileBuildMCP implementation references

- [Apple bridge](references/xcode-ide.md#L32): remote tool discovery and bridge targeting.
- [Structured results](references/output-formats.md#L68): domain errors and artifacts.
- [Persistent MCP mode](references/mcp-mode.md): retain the server throughout the active app session.
- [Workflow boundaries](references/workflows.md#L20): macOS tools and simulator tools are separate.

Use these as examples. Installed help and live schemas define supported inputs. The approved operation rules remain authoritative.
