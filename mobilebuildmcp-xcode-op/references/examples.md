# Arguments and prerequisites

## Arguments

Require macOS, Python 3.10+, and a selected Xcode installation with its first-launch setup complete.
Check `python3 --version`, `xcode-select -p`, and `xcrun --find xcodebuild`; use the intended developer
installation. Require `xcrun --find swift` for packages and `xcrun --find lldb` for native Debug.
Require a writable installed skill root for private state and a writable project artifact directory.
Report missing prerequisites instead of installing/upgrading unrelated tooling or substituting a backend.

Run all commands outside sandbox restrictions. Resolve inputs from the caller's working directory.
Run from the skill root or use the absolute path to `scripts/manager.py`.

Supply selectors and flags only on operations/routes that support them:

| Input | Use |
|---|---|
| `--project PATH.xcodeproj` | Select an Xcode project. |
| `--workspace PATH.xcworkspace` | Select an Xcode workspace. |
| `--package DIR` | Select a directory containing `Package.swift`. |
| `--configuration Debug\|Release` | Require an explicit configuration for Build/Run. |
| `--scheme NAME`, `--target NAME` | Select Xcode scheme/target; omit only when unique. |
| `--product NAME` | Select a package executable; omit only when unique. |
| `--destination VALUE` | Use a returned supported destination; use My Mac for local Xcode Run. |
| `--no-debugger` | Run Debug without its debugger. |
| `--arguments ARG...` | Put last on supported Run routes; replace saved arguments, or clear them with a bare flag. |
| `--file PATH --line NUMBER` | Set a breakpoint at an existing source file and positive line. |
| `continue --keep-breakpoint` | Retain the responsible owned breakpoint and watch again. |
| `debugger-command --command TEXT [--detail]` | Request LLDB output; raise its response budget to 500 bytes with `--detail`. |

Supply exactly one container selector. Resolve ambiguous choices from discovery.
Do not use package scheme/target or Xcode product selectors. Native SwiftPM uses the current host.
Without explicit arguments, use enabled saved Xcode arguments, or none for a package.
Use `COMMAND --help` for a short summary. Unsupported/irrelevant inputs fail before Clean or Build.
Narrow inspection requests when output is omitted.

## Route options

Require `mobilebuildmcp` on PATH and its `mcp` command, with macos, xcode-ide, and swift-package workflows.
Require Apple's available MCP bridge for debugger-enabled Debug Run.

| Route | Supported overrides |
|---|---|
| Debugger-enabled Debug Run | Reject `--arguments`, `--derived-data`, and `--architecture`. |
| Debugger-free Run, including Release | Accept `--arguments`. |
| Xcode Build and debugger-free Xcode Run | Also accept `--derived-data DIR` and `--architecture arm64\|x86_64`. |
| SwiftPM | Reject derived-data and architecture overrides. |

Reject working-directory overrides on every route. Default Xcode derived data to the skill artifact
folder/DerivedData and architecture to the discovered destination.

## Inspection example

Run the selected app, set a breakpoint at a relevant existing source line, and verify the actual stop.
Adapt the expression to a variable in its paused frame:

```bash
./scripts/manager.py debugger-command --command "frame variable tick"
./scripts/manager.py debugger-command --command "thread backtrace -c 3" --detail
```

A resolved location is not evidence that the app hit it. Use Status to verify uncertain state.
Do not repeat a partially completed debugger command automatically.
