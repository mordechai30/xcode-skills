# Backend details

## Backend route

Native arguments remain separate subprocess arguments, including paths with spaces. Discover supported configurations independently of build-setting query success. Use matching project/workspace, scheme, configuration, destination, and derived-data selections for Clean and Build.

Resolve exactly the selected application target. Product path is `TARGET_BUILD_DIR / FULL_PRODUCT_NAME`; executable is `TARGET_BUILD_DIR / EXECUTABLE_PATH`. SwiftPM uses its selected executable product and `swift build --show-bin-path`. Never choose the first executable found by a directory search.

Debug commands share the owned LLDB controller and short relative socket. A PID is identity evidence, not a debugger channel. Source breakpoints use LLDB location resolution; only a stop reason establishes a hit.

## Logs and build history

For `/path/App.xcodeproj`, artifacts use `/path/direct-xcode-op/`. A workspace uses the selected app target's owning project; a package uses `/path/Package/direct-xcode-op/`.

Top-level logs use `log-direct-xcode-op-Debug-YY-MM-DD-HH-MM-SS.txt` or Release. Local timezone is recorded inside. Same-second collisions wait; no overwrite or suffix. Appending session output does not reset Build age. Only invoked Builds count; failed prerequisite Clean leaves history unchanged. Exactly one hour does not trigger age-based Clean.

## Session recovery and termination

Follow-up commands use the retained owned session. Verify current state and process identities. Lost channels must not create replacement debuggers or adopt external sessions. Offer verified Kill or wait.

Kill removes recorded session breakpoints while the connection is usable. Process termination is app-first, followed by applicable dedicated debugger/helper and zombie-parent cleanup. Ask before terminating shared IDE/services or unrelated parents. Protect caller ancestors, system processes, and reused PIDs.

After verified process cleanup, release the context even if a lost connection prevents breakpoint-removal verification; warn that an IDE breakpoint may remain. Unverified process cleanup keeps the context blocked.

## Scheme selection

Reuse suitable saved schemes. If configuration requires a copy, preserve the original and unrelated settings. Retain `source-direct-xcode-op-configuration`, numbering unsuitable name collisions. Ask when suitable saved sources are absent or ambiguous.

## Diagnostics

Backend success requires operation and product/process evidence. Wrapper success or an empty error list alone is insufficient. After uncertain launch, inspect current state before another Run. Truncated public inspection includes an omission flag and log reference. Full diagnostic evidence is recorded once.
