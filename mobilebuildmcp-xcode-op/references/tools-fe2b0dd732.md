Source: [https://www.mobilebuildmcp.com/docs/tools](<https://www.mobilebuildmcp.com/docs/tools>)

<a id="tools-reference"></a>

# Tools Reference

All 82 tools MobileBuildMCP advertises, grouped by workflow. Data is fetched live from the latest tag of getsentry/MobileBuildMCP and cached for one hour.

Loading tools…



<a id="example-build_run_sim"></a>

## Example: `build_run_sim`[#](#example-build_run_sim)

The one-shot tool your agent will reach for most. Builds the scheme, installs the resulting `.app` on a booted simulator, and launches it, with logs captured to a file.

`launchArgs` is also supported on the other build-and-run tools (`build_run_device` and `build_run_macos`) and launch-only tools (`launch_app_sim`, `launch_app_device`, `launch_mac_app`) with the same contract: launch args go only to runtime launch steps, while `extraArgs` stays build/build-settings only.

scheme\*

string

The scheme to build. Use `list_schemes` to discover valid values. Optional when set in session defaults.

projectPath\*

string

Absolute or relative path to `.xcodeproj`. Mutually exclusive with `workspacePath`. Optional when set in session defaults.

workspacePath

string

Absolute or relative path to `.xcworkspace`. Mutually exclusive with `projectPath`. Optional when set in session defaults.

simulatorName

string

Human name, e.g. `"iPhone 17 Pro"`. Default: first booted simulator

simulatorId

string

Simulator UUID. Takes precedence over `simulatorName` if both are set.

configuration

string

Build configuration. Default: `Debug`

extraArgs

string[]

Additional `xcodebuild` and build-settings arguments. Use this for build-system flags, not app launch arguments.

launchArgs

string[]

Arguments passed to the launched app process. Use this for runtime flags that appear in `ProcessInfo.processInfo.arguments`.

<a id="naming-conventions"></a>

## Naming conventions[#](#naming-conventions)

- **MCP name**: what the server advertises to MCP clients (for example `build_run_sim`).
- **CLI name**: the short verb used under a workflow in the CLI (for example `build-and-run` under `simulator`). Click a tool card to see both.

Always up to date

This page is generated live from the latest release tag of [getsentry/MobileBuildMCP](https://github.com/getsentry/MobileBuildMCP). Every tool name, description, and workflow assignment matches the shipped release; a new version of MobileBuildMCP shows up here within an hour of publishing.

[← Previous

MCP Server Mode](https://www.mobilebuildmcp.com/docs/mcp-mode)[Next →

Workflows](https://www.mobilebuildmcp.com/docs/workflows)
