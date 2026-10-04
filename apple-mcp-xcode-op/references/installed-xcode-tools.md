# Installed Xcode tools

Command details for the installed CLI and Apple MCP bridge.

## Prerequisites

- All scripts (Python, Bash) and CLI commands must be run outside sandbox restrictions.
- Xcode 26.3 or later is installed and open with the target project
- `xcode-cli` is installed: `npm install -g xcode-cli`
- Bridge running: `xcode-cli-ctl install` (background) or `xcode-cli-ctl run` (foreground)

## Commands

Use the installed `xcode-cli` and Apple's installed MCP bridge. Check
`xcode-cli --version`, `xcodebuild -version`, and `xcode-cli tools --json`.
Do not install another MCP package for these operations.

The installed CLI 1.1.2 convenience commands use old `tabIdentifier` tools.
With Xcode 27, use `xcode-cli call <toolName> --args '<JSON>' --json` instead.
`--tab` and current-directory selection do not supply `workspaceIdentifier` to
these direct calls. Include the workspace ID in each call.

```bash
xcode-cli call XcodeOpenWorkspace --args '{"path":"/absolute/path/MyApp.xcodeproj"}' --json
xcode-cli call XcodeListWorkspaces --args '{}' --json
```

Use the returned `workspaceIdentifier` in place of `WORKSPACE_ID` below.
The installed bridge rejects an absolute path as `workspaceIdentifier`.
Opening a workspace requests Xcode approval if access is not yet granted.

| Operation | Tool | JSON arguments (replace example values) |
|-----------|------|-----------------------------------------|
| Build | `BuildProject` | `{"workspaceIdentifier":"WORKSPACE_ID"}` |
| Build errors | `GetBuildLog` | `{"workspaceIdentifier":"WORKSPACE_ID","severity":"error"}` |
| Build and run | `RunProject` | `{"workspaceIdentifier":"WORKSPACE_ID","attachDebugger":true}` |
| Stop app | `StopProject` | `{"workspaceIdentifier":"WORKSPACE_ID"}` |
| File diagnostics | `XcodeRefreshCodeIssuesInFile` | `{"workspaceIdentifier":"WORKSPACE_ID","filePath":"MyApp/Sources/MyFile.swift"}` |
| List tests | `GetTestList` | `{"workspaceIdentifier":"WORKSPACE_ID"}` |
| Run all tests | `RunAllTests` | `{"workspaceIdentifier":"WORKSPACE_ID"}` |
| Run selected tests | `RunSomeTests` | `{"workspaceIdentifier":"WORKSPACE_ID","tests":[{"targetName":"MyAppTests","testIdentifier":"MyTests/method()"}]}` |
| Preview | `RenderPreview` | `{"workspaceIdentifier":"WORKSPACE_ID","sourceFilePath":"MyApp/Sources/MyView.swift","timeout":120}` |
| Swift snippet | `RunCodeSnippet` | `{"workspaceIdentifier":"WORKSPACE_ID","sourceFilePath":"MyApp/Sources/File.swift","codeSnippet":"print(1)","purpose":"Inspect value"}` |
| Apple docs | `DocumentationSearch` | `{"query":"SwiftUI NavigationStack","frameworks":["SwiftUI"]}` |
| Read | `XcodeRead` | `{"workspaceIdentifier":"WORKSPACE_ID","filePath":"MyApp/Sources/File.swift"}` |
| List | `XcodeLS` | `{"workspaceIdentifier":"WORKSPACE_ID","path":"/","recursive":true}` |
| Search | `XcodeGrep` | `{"workspaceIdentifier":"WORKSPACE_ID","pattern":"TODO|FIXME"}` |
| Find | `XcodeGlob` | `{"workspaceIdentifier":"WORKSPACE_ID","pattern":"**/*.swift"}` |
| Write | `XcodeWrite` | `{"workspaceIdentifier":"WORKSPACE_ID","filePath":"MyApp/Sources/File.swift","content":"content"}` |
| Update | `XcodeUpdate` | `{"workspaceIdentifier":"WORKSPACE_ID","filePath":"MyApp/Sources/File.swift","oldString":"old","newString":"new","replaceAll":false}` |
| Move | `XcodeMV` | `{"workspaceIdentifier":"WORKSPACE_ID","sourcePath":"Old.swift","destinationPath":"New.swift"}` |
| Make directory | `XcodeMakeDir` | `{"workspaceIdentifier":"WORKSPACE_ID","directoryPath":"MyApp/Sources/Feature"}` |
| Remove from project | `XcodeRM` | `{"workspaceIdentifier":"WORKSPACE_ID","path":"MyApp/Sources/Unused.swift","deleteFiles":false}` |

## Debug or Release

`BuildProject` and `RunProject` use the active scheme's Run configuration.
They have no configuration argument. Select Debug or Release with the helper.

1. Find the active scheme's `.xcscheme` file. Check its `LaunchAction` configuration.
2. Save an exact copy outside the project if the change is temporary.
3. Stop the app and close its workspace with `XcodeCloseWorkspace`.
4. Run the helper, then reopen the project with `XcodeOpenWorkspace`.
   Use the new workspace ID for subsequent calls.

```bash
python3 /Users/motyzas/.agents/skills/xcode-cli/scripts/set-configuration.py \
  --scheme-file /absolute/path/MyApp.xcodeproj/xcshareddata/xcschemes/MyApp.xcscheme \
  --configuration Release
```

Use `--configuration Debug` for Debug. The helper changes only the Run
configuration. Verify the selected configuration in the build log or executable
path. For a temporary change, close the workspace, restore the saved scheme,
and reopen it after stopping the app. Do not disable debugger attachment or
remove breakpoints unless the task requires it.

## Breakpoints

First launch with `RunProject` and `attachDebugger:true`. Then check the process
state and set a symbol or source breakpoint in the active LLDB session:

```bash
xcode-cli call InvokeDebuggerCommand --args '{"workspaceIdentifier":"WORKSPACE_ID","command":"process status"}' --json
xcode-cli call InvokeDebuggerCommand --args '{"workspaceIdentifier":"WORKSPACE_ID","command":"breakpoint set --shlib MyApp --name main"}' --json
xcode-cli call InvokeDebuggerCommand --args '{"workspaceIdentifier":"WORKSPACE_ID","command":"breakpoint set --file MyFile.cpp --line 42"}' --json
xcode-cli call InvokeDebuggerCommand --args '{"workspaceIdentifier":"WORKSPACE_ID","command":"breakpoint list"}' --json
```

Replace `MyApp` with the app executable name. Use an actual symbol or executable source line. Check the breakpoint has a
resolved location. A breakpoint on `main` added after launch does not stop past
execution. These are LLDB session breakpoints, not saved Xcode breakpoint files.

## Kill an app

Use `StopProject` first. If the macOS app remains, inspect its exact PID:

```bash
ps -p APP_PID -o pid=,ppid=,stat=,comm=
bash /Users/motyzas/.agents/skills/xcode-cli/scripts/kill-app.sh APP_PID
```

The script sends TERM, waits, then sends KILL if needed. A process with `Z` in
its state is already dead; its parent must reap it. To terminate that parent,
pass the inspected parent PID explicitly:

```bash
bash /Users/motyzas/.agents/skills/xcode-cli/scripts/kill-app.sh APP_PID --zombie-parent PARENT_PID
```

This can end the parent's other work. The script checks the parent relationship
again and refuses PID 1, itself, its ancestors, and processes of another user.
Use this script for host macOS processes only, not device or simulator PIDs.

## Notes

- Enable external-agent access in Xcode's MCP settings. Check `xcrun mcp-server status` if approval fails.
- File paths are relative to the Xcode project structure. Use `XcodeLS` to find them.
- If the bridge fails, check `xcode-cli-ctl status`, then use `xcode-cli-ctl restart`.
- Increase the CLI call timeout with `--timeout 180000` for a slow build. Tool timeouts use seconds.
- Inspect JSON for `isError`, build errors, and operation results. CLI exit code 0 does not prove MCP success.
- Use `targetName` and `identifier` from `GetTestList` as `targetName` and `testIdentifier` in `RunSomeTests`. Tests come from the active scheme's active test plan.
- `run-without-build` is an AppleScript shortcut. It requires Accessibility permission and acts on the front Xcode window. Prefer workspace-targeted `RunProject`.
- Swift snippets and SwiftUI previews need compatible source files; they do not verify C++ code.
- The reference `mcpservers-xcode-mcp.md` describes a separate third-party server. Its tool names are not Apple MCP tool names.
