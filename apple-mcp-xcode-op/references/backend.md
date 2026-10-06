# Limits and recovery

## Backend limits

SwiftPM Release uses native SwiftPM.

MCP requests are limited to 60 seconds. Native Build retains its longer execution limit. Pause has a total 15-second limit from submission. Breakpoint watching continues until a stop, exit, interruption, or unavailable app control.

## Recovery

- Incomplete Build/Run: do not repeat it automatically. Use Status for an owned app, then Kill before another Run.
- Pause expiry: use Status; the interrupt may already have affected the app. Do not resume automatically.
- Pending breakpoint: it is installed, but resolution is not a hit. Use Status; inspect only at a verified paused frame.
- Interrupted watch: execution is unchanged. Use Status to observe the app.
- Incomplete inspection: narrow the request. A partial response never causes the command to run twice.
- App control unavailable: use Kill. Do not attach or adopt another app or debugger.
- Incomplete Kill: app/helper cleanup remains unverified. Do not start another Run until resolved. A warning can report an IDE breakpoint that could not be removed.

## Artifacts

Required ownership and recovery state is private and automatic. Build products and dependencies remain available. Shared Xcode/backend storage and unrelated processes are preserved. Only verified request-owned response/build artifacts are removed after consumption.

Cleanup is explicit artifact removal. It does not terminate processes.
