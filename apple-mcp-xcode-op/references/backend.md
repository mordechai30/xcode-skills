# Backend details

## Backend route

Use returned workspace identifiers and live tool schemas. Use the discovered scheme and verify its live configuration; select My Mac before Build/Run. `BuildProject` never launches; `RunProject` embeds Build and explicitly selects debugger attachment. Keep Build and launch outcomes separate.

Use `InvokeDebuggerCommand` on the retained connection. Preserve partial output and query fresh state without blindly repeating a command. Native Clean must use Apple's actual build roots and selected configuration. An unavailable matching context blocks Clean.

Package Debug opens the package directory and generated executable scheme. Package Release uses native SwiftPM because generated schemes lack supported configuration selection. Apple package Run has no launch-argument input; supplied arguments are rejected. Product paths come from actual linker evidence, not an assumed `.build/debug` directory.

## Logs and build history

For `/path/App.xcodeproj`, artifacts use `/path/apple-mcp-xcode-op/`. A workspace uses the selected app target's owning project; a package uses `/path/Package/apple-mcp-xcode-op/`.

Top-level logs use `log-apple-mcp-xcode-op-Debug-YY-MM-DD-HH-MM-SS.txt` or Release. Local timezone is recorded inside. Same-second collisions wait; no overwrite or suffix. Appending session output does not reset Build age. Only invoked Builds count; failed prerequisite Clean leaves history unchanged. Exactly one hour does not trigger age-based Clean.

## Session recovery and termination

Follow-up commands use the retained owned session. Verify current state and process identities. Lost channels must not create replacement debuggers or adopt external sessions. Offer verified Kill or wait.

Kill removes recorded session breakpoints while the connection is usable. Process termination is app-first, followed by applicable dedicated debugger/helper and zombie-parent cleanup. Ask before terminating shared IDE/services or unrelated parents. Protect caller ancestors, system processes, and reused PIDs.

After verified process cleanup, release the context even if a lost connection prevents breakpoint-removal verification; warn that an IDE breakpoint may remain. Unverified process cleanup keeps the context blocked.

## Scheme selection

Reuse suitable saved schemes. If configuration requires a copy, preserve the original and unrelated settings. Retain `source-apple-mcp-xcode-op-configuration`, numbering unsuitable name collisions. Ask when suitable saved sources are absent or ambiguous.

## Diagnostics

Backend success requires operation and product/process evidence. Wrapper success or an empty error list alone is insufficient. After uncertain launch, inspect current state before another Run. Truncated public inspection includes an omission flag and log reference. Full diagnostic evidence is recorded once.
