# Tools Reference

Source: https://www.mobilebuildmcp.com/docs/tools

All 82 tools MobileBuildMCP advertises, grouped by workflow. Data is fetched live from the latest tag of getsentry/MobileBuildMCP and cached for one hour.

## `batch`

- CLI: `batch`
- Labels: read-only ui-automation

UI automation batch for multiple same-screen elementRef taps, especially visible settings switches that can be toggled without intermediate assertions. The input key is steps, never commands, and each step is an object such as {"action":"tap","elementRef":"e1"}; do not pass raw command strings. Use refs from the latest snapshot_ui or wait_for_ui output, for example {"steps":[{"action":"tap","elementRef":"e1"},{"action":"tap","elementRef":"e2"}]}. Omit preDelay/postDelay for switch elementRefs; switches execute as touch down/up steps and reject delays.

## `boot_sim`

- CLI: `boot`
- Labels: simulator-management

Boot iOS simulator for manual/non-build flows. Not required before simulator build-and-run (build_run_sim).

## `build_device`

- CLI: `build`
- Labels: device

Build for device.

## `build_macos`

- CLI: `build`
- Labels: macos

Build macOS app.

## `build_run_device`

- CLI: `build-and-run`
- Labels: device

Build, install, and launch on physical device. Preferred single-step run tool when defaults are set.

## `build_run_macos`

- CLI: `build-and-run`
- Labels: macos

Build and run macOS app.

## `build_run_sim`

- CLI: `build-and-run`
- Labels: simulator

Build, install, and launch on iOS Simulator, booting it when needed. Runtime logs are captured automatically and the log file path is included in the response. Preferred single-step run tool when defaults are set.

## `build_sim`

- CLI: `build`
- Labels: simulator

Build for iOS sim (compile-only, no launch).

## `button`

- CLI: `button`
- Labels: read-only ui-automation

Press simulator hardware button.

## `clean`

- CLI: `clean`
- Labels: destructive device

Clean build products.

## `debug_attach_sim`

- CLI: `attach`
- Labels: debugging

Attach LLDB to sim app.

## `debug_breakpoint_add`

- CLI: `add-breakpoint`
- Labels: debugging

Add breakpoint.

## `debug_breakpoint_remove`

- CLI: `remove-breakpoint`
- Labels: debugging

Remove breakpoint.

## `debug_continue`

- CLI: `continue`
- Labels: debugging

Continue debug session.

## `debug_detach`

- CLI: `detach`
- Labels: debugging

Detach debugger.

## `debug_lldb_command`

- CLI: `lldb-command`
- Labels: destructive debugging

Run LLDB command.

## `debug_stack`

- CLI: `stack`
- Labels: read-only debugging

Get backtrace.

## `debug_variables`

- CLI: `variables`
- Labels: read-only debugging

Get frame variables.

## `discover_projs`

- CLI: `discover-projects`
- Labels: read-only device

Scans a directory (defaults to workspace root) to find Xcode project (.xcodeproj) and workspace (.xcworkspace) files. Use when project/workspace path is unknown.

## `doctor`

- CLI: `doctor`
- Labels: read-only doctor

MCP environment info.

## `drag`

- CLI: `drag`
- Labels: read-only ui-automation

Drag from a visible runtime elementRef in a direction, then return a refreshed runtime UI snapshot. Use this for exposed sheet grabbers or real scroll/list content refs when nextSteps suggests dragging; do not use raw screen coordinates.

## `erase_sims`

- CLI: `erase`
- Labels: destructive simulator-management

Erase simulator.

## `gesture`

- CLI: `gesture`
- Labels: read-only ui-automation

Simulator gesture preset.

## `get_app_bundle_id`

- CLI: `get-app-bundle-id`
- Labels: read-only device

Extract bundle id from .app.

## `get_coverage_report`

- CLI: `get-coverage-report`
- Labels: read-only coverage

Show per-target code coverage from an xcresult bundle.

## `get_device_app_path`

- CLI: `get-app-path`
- Labels: read-only device

Get device built app path.

## `get_file_coverage`

- CLI: `get-file-coverage`
- Labels: read-only coverage

Show function-level coverage and uncovered line ranges for a specific file.

## `get_mac_app_path`

- CLI: `get-app-path`
- Labels: read-only macos

Get macOS built app path.

## `get_mac_bundle_id`

- CLI: `get-macos-bundle-id`
- Labels: read-only macos

Extract bundle id from macOS .app.

## `get_sim_app_path`

- CLI: `get-app-path`
- Labels: read-only simulator

Get sim built app path.

## `install_app_device`

- CLI: `install`
- Labels: device

Install app on device.

## `install_app_sim`

- CLI: `install`
- Labels: simulator

Install app on sim.

## `key_press`

- CLI: `key-press`
- Labels: read-only ui-automation

Press one hardware key using an AXe HID key code. Prefer type_text for text entry. Common values include 40 Return/Enter, 42 Backspace, 43 Tab, and 44 Space.

## `key_sequence`

- CLI: `key-sequence`
- Labels: read-only ui-automation

Press hardware keys using AXe HID key codes. Prefer type_text for text entry. Common values include 40 Return/Enter, 42 Backspace, 43 Tab, and 44 Space.

## `launch_app_device`

- CLI: `launch`
- Labels: device

Launch app on device.

## `launch_app_sim`

- CLI: `launch-app`
- Labels: simulator

Launch app on simulator. Runtime logs are captured automatically and the log file path is included in the response.

## `launch_mac_app`

- CLI: `launch`
- Labels: macos

Launch macOS app.

## `list_devices`

- CLI: `list`
- Labels: read-only device

List connected devices.

## `list_schemes`

- CLI: `list-schemes`
- Labels: read-only device

List Xcode schemes.

## `list_sims`

- CLI: `list`
- Labels: read-only simulator-management

List iOS simulators.

## `long_press`

- CLI: `long-press`
- Labels: read-only ui-automation

Long press a UI element by elementRef from a current rs/1 runtime snapshot.

## `manage-workflows`

- CLI: `manage-workflows`
- Labels: other

Workflows are groups of tools exposed by MobileBuildMCP. By default, not all workflows (and therefore tools) are enabled; only simulator tools are enabled by default. Some workflows are mandatory and can't be disabled.

## `open_sim`

- CLI: `open`
- Labels: read-only simulator-management

Open the simulator frontend for visibility and manual workflows. Not required before simulator build-and-run (build_run_sim).

## `record_sim_video`

- CLI: `record-video`
- Labels: simulator

Record sim video.

## `reset_sim_location`

- CLI: `reset-location`
- Labels: read-only simulator-management

Reset sim location.

## `scaffold_ios_project`

- CLI: `scaffold-ios`
- Labels: project-scaffolding

Scaffold iOS project.

## `scaffold_macos_project`

- CLI: `scaffold-macos`
- Labels: project-scaffolding

Scaffold macOS project.

## `screenshot`

- CLI: `screenshot`
- Labels: read-only ui-automation

Capture screenshot.

## `session_clear_defaults`

- CLI: `clear-defaults`
- Labels: destructive session-management

Clear session defaults for the active profile or a specified profile.

## `session_set_defaults`

- CLI: `set-defaults`
- Labels: session-management

Set session defaults for the active profile, or for a specified profile and make it active.

## `session_show_defaults`

- CLI: `show-defaults`
- Labels: read-only session-management

Show current active defaults. Required before your first build/run/test call in a session — do not assume defaults are configured.

## `session_use_defaults_profile`

- CLI: `use-defaults-profile`
- Labels: session-management

Switch the active session defaults profile.

## `set_sim_appearance`

- CLI: `set-appearance`
- Labels: read-only simulator-management

Set sim appearance.

## `set_sim_location`

- CLI: `set-location`
- Labels: read-only simulator-management

Set sim location.

## `show_build_settings`

- CLI: `show-build-settings`
- Labels: read-only device

Show build settings.

## `sim_statusbar`

- CLI: `statusbar`
- Labels: read-only simulator-management

Set sim status bar network.

## `snapshot_ui`

- CLI: `snapshot-ui`
- Labels: read-only ui-automation

Capture a semantic rs/1 runtime UI snapshot with elementRef targets. Observe once, use tap for one target or batch for multiple same-screen targets, and refresh after navigation, scrolling, sheet changes, or obvious layout changes.

## `stop_app_device`

- CLI: `stop`
- Labels: device

Stop device app.

## `stop_app_sim`

- CLI: `stop`
- Labels: simulator

Stop sim app.

## `stop_mac_app`

- CLI: `stop`
- Labels: macos

Stop macOS app.

## `swift_package_build`

- CLI: `build`
- Labels: swift-package

swift package target build.

## `swift_package_clean`

- CLI: `clean`
- Labels: destructive swift-package

swift package clean.

## `swift_package_list`

- CLI: `list`
- Labels: read-only swift-package

List SwiftPM processes.

## `swift_package_run`

- CLI: `run`
- Labels: swift-package

swift package target run.

## `swift_package_stop`

- CLI: `stop`
- Labels: swift-package

Stop SwiftPM run.

## `swift_package_test`

- CLI: `test`
- Labels: swift-package

Run swift package target tests.

## `swipe`

- CLI: `swipe`
- Labels: read-only ui-automation

Swipe within a scrollable UI element using withinElementRef from a current rs/1 runtime snapshot. withinElementRef is required; do not use elementRef. Optional distance is a normalized stroke fraction greater than 0 and up to 1. Example input: {"withinElementRef":"e7","direction":"up","distance":0.7}.

## `sync_xcode_defaults`

- CLI: `sync-xcode-defaults`
- Labels: session-management

Sync session defaults (scheme, simulator) from Xcode's current IDE selection.

## `tap`

- CLI: `tap`
- Labels: read-only ui-automation

Tap one elementRef from the latest snapshot_ui or wait_for_ui output. The elementRef must list the tap action in the snapshot targets; do not use refs from text-only rows. For multiple same-screen taps or visible switch toggles with no intermediate assertion, use batch instead of repeated tap calls. Other same-screen refs may remain usable after success; refresh after navigation, scrolling, sheet changes, or obvious layout changes.

## `test_device`

- CLI: `test`
- Labels: device

Test on device.

## `test_macos`

- CLI: `test`
- Labels: macos

Test macOS target.

## `test_sim`

- CLI: `test`
- Labels: simulator

Test on iOS sim.

## `toggle_connect_hardware_keyboard`

- CLI: `toggle-connect-hardware-keyboard`
- Labels: simulator-management

Toggle whether the iOS Simulator simulates a hardware keyboard connection. Disconnecting makes the on-screen keyboard appear for tap-based input. Requires the simulator to be booted and Accessibility permission for the MCP host.

## `toggle_software_keyboard`

- CLI: `toggle-software-keyboard`
- Labels: simulator-management

Toggle the iOS Simulator software keyboard. Shows or hides the on-screen keyboard. Requires the simulator to be booted and Accessibility permission for the MCP host.

## `touch`

- CLI: `touch`
- Labels: read-only ui-automation

Send touch down/up events to a UI element by elementRef from a current rs/1 runtime snapshot.

## `type_text`

- CLI: `type-text`
- Labels: read-only ui-automation

Type text into a UI element by elementRef from a current rs/1 runtime snapshot, optionally replacing existing field contents. elementRef is required; do not call with only text. Example input: {"elementRef":"e8","text":"London","replaceExisting":true}.

## `wait_for_ui`

- CLI: `wait-for-ui`
- Labels: read-only ui-automation

Poll rs/1 runtime UI snapshots until a selector-based UI predicate, selector-free textContains/gone text predicate, or selector-free settled predicate is satisfied, then record the latest snapshot. Prefer this after navigation or layout changes. Select with elementRef, identifier, label, role, or value when a selector is needed.

## `xcode_ide_call_tool`

- CLI: `call-tool`
- Labels: destructive xcode-ide

Call a remote Xcode IDE MCP tool.

## `xcode_ide_list_tools`

- CLI: `list-tools`
- Labels: read-only xcode-ide

Lists Xcode-IDE-only MCP capabilities (Use for: SwiftUI previews image capture, code snippet execution, issue Navigator/build logs, and window/tab context).

## `xcode_tools_bridge_disconnect`

- CLI: `bridge-disconnect`
- Labels: xcode-ide

Disconnect bridge and unregister proxied `xcode_tools_*` tools.

## `xcode_tools_bridge_status`

- CLI: `bridge-status`
- Labels: read-only xcode-ide

Show xcrun mcpbridge availability and proxy tool sync status.

## `xcode_tools_bridge_sync`

- CLI: `bridge-sync`
- Labels: xcode-ide

One-shot connect + tools/list sync (manual retry; avoids background prompt spam).

## Example: `build_run_sim`

The one-shot tool your agent will reach for most. Builds the scheme, installs the resulting `.app` on a booted simulator, and launches it, with logs captured to a file.

`launchArgs` is also supported on the other build-and-run tools (`build_run_device` and `build_run_macos`) and launch-only tools (`launch_app_sim`, `launch_app_device`, `launch_mac_app`) with the same contract: launch args go only to runtime launch steps, while `extraArgs` stays build/build-settings only.

| Parameter | Type | Description |
| --- | --- | --- |
| `scheme*` | `string` | The scheme to build. Use `list_schemes` to discover valid values. Optional when set in session defaults. |
| `projectPath*` | `string` | Absolute or relative path to `.xcodeproj`. Mutually exclusive with `workspacePath`. Optional when set in session defaults. |
| `workspacePath` | `string` | Absolute or relative path to `.xcworkspace`. Mutually exclusive with `projectPath`. Optional when set in session defaults. |
| `simulatorName` | `string` | Human name, e.g. `"iPhone 17 Pro"`. Default: first booted simulator |
| `simulatorId` | `string` | Simulator UUID. Takes precedence over `simulatorName` if both are set. |
| `configuration` | `string` | Build configuration. Default: `Debug` |
| `extraArgs` | `string[]` | Additional `xcodebuild` and build-settings arguments. Use this for build-system flags, not app launch arguments. |
| `launchArgs` | `string[]` | Arguments passed to the launched app process. Use this for runtime flags that appear in `ProcessInfo.processInfo.arguments`. |

## Naming conventions

*   **MCP name**: what the server advertises to MCP clients (for example `build_run_sim`).
*   **CLI name**: the short verb used under a workflow in the CLI (for example `build-and-run` under `simulator`). Click a tool card to see both.

### Always up to date

This page is generated live from the latest release tag of [getsentry/MobileBuildMCP](https://github.com/getsentry/MobileBuildMCP). Every tool name, description, and workflow assignment matches the shipped release; a new version of MobileBuildMCP shows up here within an hour of publishing.
