# Limits and recovery

## Backend limits

SwiftPM products are selected from Package.swift and its reported binary directory.

MCP requests are limited to 60 seconds. Native Build retains its longer execution limit. Pause has a total 15-second limit from submission. Breakpoint watching continues until a stop, exit, interruption, or unavailable app control.

## Clean

Clean precedes the first invoked Build and a Build more than one hour after the previous invocation. Exactly one hour does not trigger age Clean. Failed prerequisite Clean blocks Build. An invoked failed Build advances history and performs Clean without retry. Incomplete Clean remains due on the next attempt. Build age uses the log filename, not later log changes.

## Recovery

- Incomplete Build/Run: do not repeat it automatically. Use Status for an owned app, then Kill before another Run.
- Pause expiry: use Status; the interrupt may already have affected the app. Do not resume automatically.
- Pending breakpoint: it is installed, but resolution is not a hit. Use Status; inspect only at a verified paused frame.
- Interrupted watch: execution is unchanged. Use Status to observe the app.
- Incomplete inspection: narrow the request. A partial response never causes the command to run twice.
- App control unavailable: use Kill. Do not attach or adopt another app or debugger.
- Incomplete Kill: app/helper cleanup remains unverified. Do not start another Run until resolved. A warning can report an IDE breakpoint that could not be removed.

## Logs and artifacts

Artifacts remain in `OWNER_PROJECT_FOLDER/direct-xcode-op`; packages use `PACKAGE_DIRECTORY/direct-xcode-op`. Operation logs are `log-direct-xcode-op-CONFIGURATION-TIMESTAMP.txt`.

Logs contain useful failures, warnings/errors with necessary source context, operation status, and exact public responses. They contain no selection dumps, backend setup stages, raw transcripts, or omitted inspection data. Ordinary app output is consumed and discarded.

Required ownership and recovery state is private and automatic. Build products and dependencies remain available. Shared Xcode/backend storage and unrelated processes are preserved. Only verified request-owned response/build artifacts are removed after consumption.

Cleanup is explicit artifact removal. It preserves top-level operation logs and does not terminate processes.
