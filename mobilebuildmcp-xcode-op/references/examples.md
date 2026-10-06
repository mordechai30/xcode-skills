# Arguments and examples

## Arguments

Run outside sandbox restrictions. `--configuration Debug|Release` and one container are required for Build/Run. All paths resolve from the caller's directory.

| Option | Use |
|---|---|
| `--project PATH.xcodeproj` | Xcode project |
| `--workspace PATH.xcworkspace` | Xcode workspace |
| `--package DIR` | Folder containing Package.swift |
| `--scheme NAME`, `--target NAME` | Xcode selection; omit when unique |
| `--product NAME` | Package executable; omit when unique |
| `--destination VALUE` | Returned destination; My Mac for local Run |
| `--arguments ARG…` | Run without a debugger; put last; replaces saved arguments |
| `--working-directory DIR` | Not supported |
| `--derived-data DIR` | Xcode Build and debugger-free Run; default skill artifact folder/DerivedData |
| `--architecture arm64\|x86_64` | Xcode Build and debugger-free Run; default discovered destination |
| `--no-debugger` | Debug Run without a debugger |
| `--file PATH --line NUMBER` | Breakpoint; existing file and positive line |
| `--keep-breakpoint` | Continue and watch the next hit |
| `--command TEXT --detail` | Requested inspection with optional 500-byte limit |

Debugger-enabled Debug Run rejects `--arguments`, `--derived-data`, and `--architecture`. Debugger-free Run and Release Run accept `--arguments`; Xcode Build and debugger-free Run also accept `--derived-data` and `--architecture`. Working-directory overrides are unsupported. SwiftPM does not accept `--derived-data` or `--architecture`.
Do not use package `--scheme` or `--target`, or Xcode `--product`. Unsupported and irrelevant inputs fail before compilation.

## Build and Run

```bash
./scripts/manager.py build --project /path/App.xcodeproj --configuration Debug
./scripts/manager.py run --project /path/App.xcodeproj --configuration Debug
./scripts/manager.py status
./scripts/manager.py kill
```

Examples: `Build succeeded.`; `Run succeeded.`; `Status: running.`; `Kill succeeded.` Warnings and errors follow the result. An ambiguous selection names the choices; supply the appropriate option.

## Debug

```bash
./scripts/manager.py run --package /Users/motyzas/src/skill-test-projects/HelloSwiftPackage --configuration Debug --product HelloSwift
./scripts/manager.py set-breakpoint --file /Users/motyzas/src/skill-test-projects/HelloSwiftPackage/Sources/HelloSwift/main.swift --line 9
./scripts/manager.py debugger-command --command "frame variable tick"
./scripts/manager.py continue
./scripts/manager.py pause
./scripts/manager.py continue
./scripts/manager.py kill
```

Inspect only after a verified stop. The fixture updates tick on line 9. A pending breakpoint is installed but has not resolved; use Status and wait for a stop before inspection. A hit reports the short source location. Continue removes only the responsible owned breakpoint. Use `continue --keep-breakpoint` to stop there again.

For a bounded stack:

```bash
./scripts/manager.py debugger-command --command "thread backtrace -c 3" --detail
```

Inspection reports the requested output and any command error. `…` marks omitted text; inspect fewer members or frames. Omitted data is not archived.

## Release and arguments

```bash
./scripts/manager.py run --package /path/Package --configuration Release --product Product
./scripts/manager.py status
./scripts/manager.py kill
```

On supported routes, add `--arguments --mode test` to replace saved arguments. Bare trailing `--arguments` clears them. Quote values containing spaces. The supplied HelloSwiftPackage fixture accepts `--exit` for immediate exit. Run or subsequent Status reports the observed exit.

## Cleanup

```bash
./scripts/cleanup.sh /path/App.xcodeproj
./scripts/cleanup.sh /path/Package
```

Use Kill for app termination. Cleanup removes only non-log content in this skill's artifact folder. It never runs automatically and performs no session checks.
