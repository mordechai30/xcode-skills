---
name: direct-xcode-op
description:
  Build, run, and debug macOS Xcode apps and SwiftPM executables with native Xcode and LLDB.
  Use for breakpoints, inspection, Pause, Continue, Status, and owned-session termination.
---

# macOS operations with native Xcode and LLDB

- Run all scripts and CLI commands outside sandbox restrictions.
- If the workspace (the root) has no `.xcodeproj`, `.xcworkspace`, `.xcproj` or `Package.swift`, look in  
`<root>/xcode`, `<root>/build`, and `<root>/out` before reporting no project found.
- Do not read scripts unless the user explicitly asks. Use their documented command interfaces (report if  
anything is missing, ambiguous or not working properly).
- Use one skill at a time, on one project and configuration. Run from this skill root or use absolute
entrypoint paths. Resolve input paths from the caller's directory.
- Report material contradictions, missing prerequisites/artifacts, errors, and unverified outcomes.
- Retain only task-relevant decisions, evidence, session identifiers, and unresolved issues in working
summaries. Discard irrelevant outputs from later summaries; preserve requested deliverables.

## Before Build or Run

- Read [arguments and prerequisites](references/examples.md#arguments) for route-specific inputs.
- Read [side effects and artifacts](references/backend.md#side-effects-and-artifacts) before the first operation
on a project. Build can automatically Clean.
- Kill an existing owned session before another Build or Run. Do not retry failed or uncertain requests
automatically. Use My Mac for local Xcode Run.
- Default to Debug build/run if none is specified.
- Debug enables the debugger unless `--no-debugger` is supplied; Release does not enable it.

## Commands

Use `CONTAINER` for one container selector and `CONFIG` for Debug or Release.

| Action | Command | Effect |
|---|---|---|
| Build | `./scripts/manager.py build CONTAINER --configuration CONFIG` | Build without launching. |
| Run | `./scripts/manager.py run CONTAINER --configuration CONFIG [--no-debugger]` | Build once and launch the selected product. |
| Status | `./scripts/manager.py status` | Report owned app state. |
| Breakpoint | `./scripts/manager.py set-breakpoint --file PATH --line NUMBER` | Set a source breakpoint. |
| Pause | `./scripts/manager.py pause` | Pause a running debugger-enabled Debug session. |
| Inspect | `./scripts/manager.py debugger-command --command "LLDB COMMAND" [--detail]` | Return requested output/errors within the response budget. |
| Continue | `./scripts/manager.py continue [--keep-breakpoint]` | Resume the paused app. |
| Kill | `./scripts/manager.py kill` | Terminate the owned app and verified dedicated helpers; release the session. |
| Cleanup | `./scripts/cleanup.sh OWNER_PATH` | Remove stored non-log artifacts; do not terminate processes. |

Replace `CONTAINER` with exactly one of `--project PATH.xcodeproj`, `--workspace PATH.xcworkspace`,
or `--package DIR`. Read the arguments reference above for selectors and supported route overrides.
Apply launch arguments and working-directory overrides only to Run; never pass them to Build.
Use follow-up commands without repeating selection inputs.

Use paths and inspection expressions from the actual task; examples do not prescribe app behavior.
Inspect frame-dependent data only at a verified paused frame.
A resolved breakpoint on a running app watches until a stop, exit, interruption, or unavailable control.
Interrupting that watch leaves execution unchanged. Pause has a total 15-second submission limit.
Continue removes only the responsible owned breakpoint; add `--keep-breakpoint` to retain it and watch again.
Ask for instruction on unexpected stops. Read [recovery](references/backend.md#recovery) for incomplete work.

## Results and exit codes

Read the plain-text response and exit code together; do not expect JSON or infer app state from success.
For Status, expect `Status: running.`, `paused.`, `exited.`, `unknown.`, or `no app.` with the same prefix.

| Exit | Expected result | Next action |
|---|---|---|
| `0` | Operation completed, e.g. `Build succeeded.`; Status reports the observed state. | Use the reported outcome; verify a stop before frame inspection. |
| `1` | Operation failed, was incomplete, or needs input; read diagnostics and any choices. | Resolve the reported cause/choice; use Status for uncertain state. |
| `2` | Invalid inputs or an unexpected exception; read the response to distinguish them. | Correct invalid inputs; verify state after an incomplete request. |
| `130` | Request interrupted outside the watch handler. | Use Status before another operation. |

Treat `Breakpoint needs input.` with a pending-location message as an installed unresolved breakpoint,
even with exit `1`; do not reinstall it automatically or claim it was hit.
For an interrupted watch, use its reported state and exit code; the handler can return `0` or `1`.
Expect relevant warnings/errors and requested inspection data after the result. Expect a 200-byte UTF-8
response budget, or 500 for failures, uncertainty, or inspection `--detail`, including the final newline.
Treat `…` as omitted data; narrow an inspection rather than claiming its complete output was inspected.

## Explicit artifact removal

Complete Kill before cleanup when an app session exists. Cleanup performs no process/session checks.
Supply an existing owning `.xcodeproj`, package directory, or project-containing folder as `OWNER_PATH`.
Do not supply a workspace path. For a workspace, obtain the selected target's `PROJECT_FILE_PATH`:

```bash
xcodebuild -workspace "PATH.xcworkspace" -scheme "SCHEME" -configuration "CONFIG" -showBuildSettings -json
```

Replace the placeholders with the active selection; match the returned target to the selected target and
use its `buildSettings.PROJECT_FILE_PATH`. If ownership is missing or ambiguous, stop and ask.
Read [artifact locations](references/backend.md#side-effects-and-artifacts) for retained files and scope.

| Cleanup exit | Expected stdout | Meaning |
|---|---|---|
| `0` | `Cleanup succeeded.` | Removal completed; retained logs remain. |
| `0` | `Cleanup: no artifacts found.` | No artifact directory existed. |
| Nonzero | `Cleanup failed.` with a reason for rejected inputs; filesystem diagnostics may appear on stderr. | Validation uses exit `2`; filesystem failures return their error code. Resolve the cause and inspect remaining artifacts before claiming completion. |
