# Side effects and recovery

## Side effects and artifacts

Expect artifacts in `OWNER_PROJECT_FOLDER/direct-xcode-op`, where OWNER_PROJECT_FOLDER is the directory
containing the selected app target's owning .xcodeproj. A workspace may live elsewhere: use the selected
target's PROJECT_FILE_PATH from Xcode build settings to identify its owner. Packages use
`PACKAGE_DIRECTORY/direct-xcode-op`.
Expect operation logs named `log-direct-xcode-op-CONFIGURATION-TIMESTAMP.txt` in that directory.

Require the installed skill root to be writable: private `.active-session.json` and `.operation.lock`
live there. The locator links to project session state; the OS lock serializes operations. Kill releases
the owned session and locator; the lock file can remain. Do not remove private state to bypass recovery.

Expect Clean before the first invoked Build and when the previous invocation is more than one hour old.
Exactly one hour does not trigger age Clean. Failed prerequisite Clean blocks Build. An invoked failed
Build advances history and performs Clean without retry; incomplete Clean remains due next time.
Build age uses the invocation log filename, not later writes. Clean can remove backend build products,
including SwiftPM's package build output or the selected Xcode build roots.
Use command responses for results. Logs retain useful diagnostics and necessary source context, not raw
transcripts or omitted inspection output. Ordinary app output is consumed and discarded.
Keep requested deliverables and necessary recovery records; do not treat artifact cleanup as agent-context
cleanup. Cleanup is explicit and never automatic: it preserves top-level regular `log-*.txt` files,
removes other content in the selected skill artifact folder, and does not terminate/check processes.
It reports when no artifact folder exists. Supply the owning project/package or its containing folder;
workspace paths are rejected because they do not identify the selected target's artifact owner.
Custom derived-data/build locations and persistent scheme copies are outside this cleanup operation.

## Backend limits

Allow up to 7,200 seconds for native Build/Clean commands and 60 seconds for discovery queries.
Native debugger-channel requests normally allow 15 seconds.
Pause has a total 15-second limit from submission, including queueing. Breakpoint watching continues until
a stop, exit, interruption, or unavailable app control.

## Recovery

- Incomplete Build/Run: do not retry automatically. Use Status for an owned app, then Kill before a new Run.
- Pause expiry: use Status; the interrupt may already have affected the app. Do not resume automatically.
- Pending breakpoint: distinguish installation from resolution and a hit. Inspect at a verified paused frame.
- Interrupted watch: use Status; interruption does not change app execution.
- Incomplete inspection: narrow the request. Do not repeat a potentially mutating command automatically.
- App control unavailable: use Kill; do not attach to or adopt another app or debugger.
- Incomplete Kill: do not start another Run until app/helper cleanup is verified. Report any warning about
  an IDE breakpoint that could not be removed.
