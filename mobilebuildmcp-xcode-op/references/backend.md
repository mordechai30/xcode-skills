# Backend details

## Backend route

Discover supported inputs with installed help and live MCP schemas. Keep the owned Mobile MCP server and its Apple bridge during the session. Set supported in-memory defaults once; do not persist defaults into application files.

Use macOS Build/Clean/product/Launch/Stop, or SwiftPM package operations. Debug Run uses the Apple bridge; Release and debugger-disabled routes use the appropriate launch tool. Package Debug through Apple has no launch-argument input.

Check actual domain errors, operation outcome fields, and returned artifacts. Bridge artifacts must match the requested remote tool and arguments. Do not hard-code reference schema versions. Independently verify returned PIDs against the selected executable: a name lookup can return another process. Never terminate by broad app-name matching.

## Logs and build history

For `/path/App.xcodeproj`, artifacts use `/path/mobilebuildmcp-xcode-op/`. A workspace uses the selected app target's owning project; a package uses `/path/Package/mobilebuildmcp-xcode-op/`.

Top-level logs use `log-mobilebuildmcp-xcode-op-Debug-YY-MM-DD-HH-MM-SS.txt` or Release. Local timezone is recorded inside. Same-second collisions wait; no overwrite or suffix. Appending session output does not reset Build age. Only invoked Builds count; failed prerequisite Clean leaves history unchanged. Exactly one hour does not trigger age-based Clean.

## Session recovery and termination

Follow-up commands use the retained owned session. Verify current state and process identities. Lost channels must not create replacement debuggers or adopt external sessions. Offer verified Kill or wait.

Kill removes recorded session breakpoints while the connection is usable. Process termination is app-first, followed by applicable dedicated debugger/helper and zombie-parent cleanup. Ask before terminating shared IDE/services or unrelated parents. Protect caller ancestors, system processes, and reused PIDs.

After verified process cleanup, release the context even if a lost connection prevents breakpoint-removal verification; warn that an IDE breakpoint may remain. Unverified process cleanup keeps the context blocked.

## Scheme selection

Reuse suitable saved schemes. If configuration requires a copy, preserve the original and unrelated settings. Retain `source-mobilebuildmcp-xcode-op-configuration`, numbering unsuitable name collisions. Ask when suitable saved sources are absent or ambiguous.

## Diagnostics

Backend success requires operation and product/process evidence. Wrapper success or an empty error list alone is insufficient. After uncertain launch, inspect current state before another Run. Truncated public inspection includes an omission flag and log reference. Full diagnostic evidence is recorded once.
