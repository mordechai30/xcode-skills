---
name: mobilebuildmcp-xcode-op
description: Build, run, and debug macOS Xcode apps and SwiftPM executables with MobileBuildMCP. Use for source breakpoints, inspection, Pause, Continue, and session termination.
---

# MobileBuildMCP operations

Run all Python, Bash, and CLI commands outside sandbox restrictions. Execute `scripts/manager.py`; reading its implementation is not required.

Use one skill, one project, one configuration, and one owned app session at a time. Follow-up commands reuse only this skill's connection. Do not adopt external apps or debugger sessions. An active context requires Kill before Build, another Run, or switching projects.

```bash
python3 scripts/manager.py build --project /path/App.xcodeproj --configuration Debug
python3 scripts/manager.py run --package /path/Package --configuration Release
python3 scripts/manager.py set-breakpoint --file /path/main.cpp --line 20
python3 scripts/manager.py debugger-command --command "frame variable tick"
python3 scripts/manager.py continue
python3 scripts/manager.py kill
```

Build/Run require `--project`, `--workspace`, or `--package` and Debug/Release. Use `--scheme`, `--target` (alias `--product`), and `--destination` only when selection requires them. Follow-up commands need no session ID.

Choose discovered **My Mac** for local execution. **Any Mac** is generic and cannot Run. SwiftPM host routes use `macOS`. Honor supported explicit choices; ask about unresolved ambiguity.

Use MobileBuildMCP macOS/SwiftPM tools and its persistent Apple bridge for debugger-enabled Debug. Do not use simulator debugging for macOS.

- Build never launches. Run builds once per request. Clean first, after more than one hour, or after incomplete required Clean. Failed Clean blocks Build; failed Build cleans and waits without retry.
- Debug attaches LLDB unless `--no-debugger`; Release has no debugger.
- Set Breakpoint requires file/line. A hit pauses and waits for user input. Pending or relocated locations must be reported. Watching is silent until it ends; interruption leaves the session intact.
- Pause interrupts running Debug. Continue requires paused Debug and removes only the responsible owned breakpoint; `--keep-breakpoint` retains it and watches again. Manual/runtime pauses delete none.
- Inspection returns current values/stack. Unexpected stops wait; never Continue automatically or change sanitizer settings.
- Kill terminates the app, then required dedicated debugger/helpers and appropriate zombie parents. Preserve shared IDE/services. Lost connections allow verified Kill recovery, never automatic attachment or relaunch.

Public JSON is at most 200 UTF-8 bytes normally, or 500 for errors/requested inspection. Full evidence stays in project-local logs. Disclosed omissions point to the log. Adapter requests have a 60-second maximum.

Do not modify app source or commit. UI interaction and other Apple platforms are deferred. Execute `scripts/cleanup.sh` only on explicit request; it removes non-log artifacts without session checks.

For backend limitations, logs, or recovery, read [backend details](references/backend.md#backend-route). For arguments and command examples, read [examples](references/examples.md#commands).
