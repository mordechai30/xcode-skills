Source: [https://www.mobilebuildmcp.com/docs/changelog](<https://www.mobilebuildmcp.com/docs/changelog>)

<a id="changelog"></a>

# Changelog

Release notes pulled live from the getsentry/MobileBuildMCP GitHub releases feed and cached for one hour.

<a id="v2.7.1"></a>

### Release v2.7.1

September 23, 2026

latest[View on GitHub ↗](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.7.1)

<a id="release-v271"></a>

#### Release v2.7.1

<a id="changed"></a>

##### Changed

- Renamed the project from XcodeBuildMCP to MobileBuildMCP. The npm package, CLI binaries (`mobilebuildmcp`, `mobilebuildmcp-doctor`), Homebrew formula, `MOBILEBUILDMCP_*` environment variables, `mobilebuildmcp://` resource URIs, `mobilebuildmcp.output.*` structured output schema IDs, the `.mobilebuildmcp/config.yaml` project config directory, and the `~/Library/Developer/MobileBuildMCP` state directory all use the new name. The `xcodebuildmcp.com` domain is retired: structured output schema `$id` URLs now use `https://raw.githubusercontent.com/getsentry/MobileBuildMCP/main/schemas/structured-output/`, documentation links point at the docs sources in the `getsentry/xcodebuildmcp.com` repository, and the MCP registry name is `io.github.getsentry/mobilebuildmcp`.
- Dictionary-shaped MCP inputs now use client-compatible wire representations ([#491](https://github.com/getsentry/XcodeBuildMCP/issues/491)). The `env` and `testRunnerEnv` inputs on build, launch, test, and session-default tools are arrays of `{ "key": "...", "value": "..." }` entries, while `xcode_ide_call_tool.arguments` is a JSON object string. MobileBuildMCP converts these values to their existing internal objects only after MCP input validation.

<a id="option-a--homebrew-no-nodejs-required"></a>

##### Option A — Homebrew (no Node.js required)

Install:

```
brew tap getsentry/xcodebuildmcp
brew install mobilebuildmcp
```

MCP config:

```
"MobileBuildMCP": {
  "command": "mobilebuildmcp",
  "args": ["mcp"]
}
```

<a id="option-b--npm--npx-nodejs-18"></a>

##### Option B — npm / npx (Node.js 18+)

Install:

```
npm install -g mobilebuildmcp@latest
```

MCP config:

```
"MobileBuildMCP": {
  "command": "npx",
  "args": ["-y", "mobilebuildmcp@latest", "mcp"]
}
```

📦 **NPM Package**: <https://www.npmjs.com/package/mobilebuildmcp/v/2.7.1>

<a id="v2.7.0"></a>

### Release v2.7.0

July 23, 2026

[View on GitHub ↗](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.7.0)

<a id="release-v270"></a>

#### Release v2.7.0

<a id="new-xcode-27-device-hub-simulator-support"></a>

##### New! Xcode 27 Device Hub simulator support

UI automation tools now work fully with Xcode 27 simulators through Device Hub, including simulator window launching and keyboard controls. XcodeBuildMCP targets the selected simulator directly and uses locale-independent menu actions, while maintaining backward compatibility with Simulator.app on earlier Xcode versions.

<a id="breaking"></a>

##### Breaking

<a id="build-and-test-structured-results-now-use-schema-version-3"></a>

##### Build and test structured results now use schema version 3

Build and test tools now return `schemaVersion: "3"` so prepared-test paths can be included in structured results. This affects MCP and CLI JSON consumers that validate `xcodebuildmcp.output.build-result` or `xcodebuildmcp.output.test-result` against version 2; consumers that only display or pass through tool results are unaffected.

If no action is taken, validators pinned to version 2 will reject new build and test results. Update them to accept the version 3 schemas, while retaining version 2 support when older XcodeBuildMCP releases remain in use.

Before:

```
https://xcodebuildmcp.com/schemas/structured-output/xcodebuildmcp.output.build-result/2.schema.json
https://xcodebuildmcp.com/schemas/structured-output/xcodebuildmcp.output.test-result/2.schema.json
```

After:

```
https://xcodebuildmcp.com/schemas/structured-output/xcodebuildmcp.output.build-result/3.schema.json
https://xcodebuildmcp.com/schemas/structured-output/xcodebuildmcp.output.test-result/3.schema.json
```

<a id="unspecified-build-configurations-now-follow-the-scheme"></a>

##### Unspecified build configurations now follow the scheme

Build, test, clean, and app-path commands now honor the scheme action's configuration when `configuration` is omitted instead of always using Debug. This fixes incorrect build settings for schemes that use another configuration, but scripts or agents that relied on the implicit Debug selection must now request it explicitly.

Before:

```
xcodebuildmcp simulator build --scheme MyApp --project-path ./MyApp.xcodeproj
```

After:

```
xcodebuildmcp simulator build \
  --scheme MyApp \
  --project-path ./MyApp.xcodeproj \
  --configuration Debug
```

For MCP calls, set `configuration: "Debug"` ([#443](https://github.com/getsentry/XcodeBuildMCP/issues/443), [#460](https://github.com/getsentry/XcodeBuildMCP/pull/460) by [@hujunfeng](https://github.com/hujunfeng)).

<a id="added"></a>

##### Added

- Added `xcodebuildmcp purge` to inspect and clean workspace storage managed by XcodeBuildMCP. It defaults to the current workspace, supports reports and dry runs, and requires explicit opt-in before removing DerivedData.
- Added reusable `extraArgs` session defaults for build and test commands, so common `xcodebuild` flags and build settings can be configured once in project config or the active session. Per-call values override matching defaults, and `extraArgs: []` clears them for one call ([#463](https://github.com/getsentry/XcodeBuildMCP/pull/463) by [@jknlsn](https://github.com/jknlsn)). See [config.example.yaml](https://www.mobilebuildmcp.com/docs/config.example.yaml).
- Added reusable test preparation to simulator, device, and macOS workflows. Build tools can produce a portable `.xctestproducts` package, and test tools can run it—or an advanced `.xctestrun` file—without rebuilding while still producing a fresh `.xcresult` ([#450](https://github.com/getsentry/XcodeBuildMCP/issues/450)). See [CLI examples](https://www.mobilebuildmcp.com/docs/README.md#cli).

<a id="fixed"></a>

##### Fixed

- Fixed MCP clients waiting 10–17 seconds for tools to become available, which could make short health checks report a failed connection ([#461](https://github.com/getsentry/XcodeBuildMCP/issues/461), [#468](https://github.com/getsentry/XcodeBuildMCP/pull/468) by [@Pitchfork-and-Torch](https://github.com/Pitchfork-and-Torch)).
- Fixed simulator commands selecting the wrong platform when a configured simulator is unavailable, especially for projects that support both iOS and visionOS. Setup now ignores unavailable simulators and records the selected platform.
- Fixed simulator and project discovery failures caused by malformed simulator data, projects with shared path prefixes, and compiler diagnostic filenames containing glob characters ([#424](https://github.com/getsentry/XcodeBuildMCP/issues/424)).
- Fixed `suppressWarnings` so warnings are omitted from final build, build-and-run, and test responses as well as live progress ([#447](https://github.com/getsentry/XcodeBuildMCP/issues/447), [#470](https://github.com/getsentry/XcodeBuildMCP/pull/470) by [@JoshKappler](https://github.com/JoshKappler)).
- Fixed multiple edge cases in iOS scaffolding, LLDB sessions, run-destination detection, concurrent operations, and physical-device name lookup that could produce incorrect project settings, mixed debugger output, missing destinations, or blocked responses ([#459](https://github.com/getsentry/XcodeBuildMCP/issues/459)).
- Fixed `stop_mac_app` app-name targeting so it no longer terminates unrelated processes whose later command-line arguments contain the app name, and rejects unsafe process IDs before execution ([#306](https://github.com/getsentry/XcodeBuildMCP/issues/306)).
- Fixed incremental builds with absolute DerivedData paths, long configuration arguments, changed build settings, or updated project files so generated build data is reused only when it is still valid ([#466](https://github.com/getsentry/XcodeBuildMCP/issues/466)).
- Fixed security risks by preventing environment-derived values from being interpreted as shell commands, verifying downloaded incremental-build tooling before execution, and restricting CI and release workflows to read-only repository access.

Various other internal improvements to stability, performance, and code quality.

<a id="option-a--homebrew-no-nodejs-required-1"></a>

##### Option A — Homebrew (no Node.js required)

Install:

```
brew tap getsentry/xcodebuildmcp
brew install xcodebuildmcp
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "xcodebuildmcp",
  "args": ["mcp"]
}
```

<a id="option-b--npm--npx-nodejs-18-1"></a>

##### Option B — npm / npx (Node.js 18+)

Install:

```
npm install -g xcodebuildmcp@latest
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "npx",
  "args": ["-y", "xcodebuildmcp@latest", "mcp"]
}
```

📦 **NPM Package**: <https://www.npmjs.com/package/xcodebuildmcp/v/2.7.0>

<a id="v2.6.2"></a>

### Release v2.6.2

June 2, 2026

[View on GitHub ↗](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.6.2)

<a id="release-v262"></a>

#### Release v2.6.2

<a id="fixed-1"></a>

##### Fixed

- Fixed `xcodebuildmcp upgrade` so update checks use the latest GitHub release as the canonical target instead of stale package-manager metadata, ensuring multi-version upgrades show release notes for the actual target version.

<a id="option-a--homebrew-no-nodejs-required-2"></a>

##### Option A — Homebrew (no Node.js required)

Install:

```
brew tap getsentry/xcodebuildmcp
brew install xcodebuildmcp
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "xcodebuildmcp",
  "args": ["mcp"]
}
```

<a id="option-b--npm--npx-nodejs-18-2"></a>

##### Option B — npm / npx (Node.js 18+)

Install:

```
npm install -g xcodebuildmcp@latest
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "npx",
  "args": ["-y", "xcodebuildmcp@latest", "mcp"]
}
```

📦 **NPM Package**: <https://www.npmjs.com/package/xcodebuildmcp/v/2.6.2>

<a id="v2.6.1"></a>

### Release v2.6.1

June 2, 2026

[View on GitHub ↗](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.6.1)

<a id="release-v261"></a>

#### Release v2.6.1

<a id="fixed-2"></a>

##### Fixed

- Fixed tab bar item discovery so agents can switch `UITabBar` items ([#439](https://github.com/getsentry/XcodeBuildMCP/issues/439), [#441](https://github.com/getsentry/XcodeBuildMCP/pull/441)).

<a id="option-a--homebrew-no-nodejs-required-3"></a>

##### Option A — Homebrew (no Node.js required)

Install:

```
brew tap getsentry/xcodebuildmcp
brew install xcodebuildmcp
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "xcodebuildmcp",
  "args": ["mcp"]
}
```

<a id="option-b--npm--npx-nodejs-18-3"></a>

##### Option B — npm / npx (Node.js 18+)

Install:

```
npm install -g xcodebuildmcp@latest
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "npx",
  "args": ["-y", "xcodebuildmcp@latest", "mcp"]
}
```

📦 **NPM Package**: <https://www.npmjs.com/package/xcodebuildmcp/v/2.6.1>

<a id="v2.6.0"></a>

### Release v2.6.0

June 1, 2026

[View on GitHub ↗](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.6.0)

<a id="release-v260"></a>

#### Release v2.6.0

<a id="new-runtime-ui-automation"></a>

##### New! Runtime UI automation

UI automation now hands your agent reusable context instead of just confirming an action ran. After a tap, swipe, type, wait, or batch, the result includes a compact snapshot of the foreground UI with stable element references and a screen hash, so the agent can pick the next control directly rather than taking another screenshot or re-running a full snapshot. Candidate controls are ranked from real accessibility data, and suggested next steps point at concrete element references instead of guessed coordinates.

In a deterministic Weather-app task, this cut wall-clock time by roughly 70%, token usage by roughly 68%, and total tool calls by roughly 76%.

New tools and options:

- `wait_for_ui` polls the UI until a predicate is satisfied — existence, enabled state, focus, visible text, or settled layout.
- `batch` performs a sequence of element-reference actions in one call, so agents can run several same-screen taps without a snapshot round-trip between each step.
- `drag` performs element-reference drag gestures for expanding sheets and scrolling real list regions without coordinate guessing.
- `snapshot_ui` now returns stable element references and a screen hash. Pass `sinceScreenHash` (MCP) / `--since-screen-hash` (CLI) to skip a full snapshot when the screen has not changed.
- `type_text` accepts `replaceExisting` to replace a field's current value instead of appending to it.

See [Tools Reference](https://xcodebuildmcp.com/docs/tools).

<a id="added-1"></a>

##### Added

- Added follow-up `nextSteps` to machine-readable results so agents can act on suggested next actions without scraping prose. MCP `structuredContent` carries MCP tool-call hints and CLI `--output json` carries shell command lines. Result schemas that include `nextSteps` move to schema version 2; version 1 schema files remain available for existing validators. See [Output Formats](https://xcodebuildmcp.com/docs/output-formats).
- Added an opt-in `XCODEBUILDMCP_HEADLESS_LAUNCH` mode for automated runs that should not steal macOS focus: macOS apps launch in the background, the Simulator window is not brought to the foreground (the simulator runtime still boots), and keyboard-shortcut actions fail fast with a clear foreground-focus requirement. See [Environment Variables](https://xcodebuildmcp.com/docs/env-vars).

<a id="fixed-3"></a>

##### Fixed

- Fixed structured output so MCP clients that validate tool results can load every structured-output tool again. Published schemas are now self-contained, resolving validation failures such as `PointerToNowhere` in JSON Schema 2020-12 validators that do not re-base references across embedded schemas ([#419](https://github.com/getsentry/XcodeBuildMCP/issues/419), [#423](https://github.com/getsentry/XcodeBuildMCP/pull/423) by [@Subharup-31](https://github.com/Subharup-31)).
- Clarified `debug_attach_sim` PID attach arguments so the schema documents that `pid` must be used without `bundleId` or `waitFor`, and invalid `pid` + `waitFor: true` calls now fail validation before LLDB is invoked ([#417](https://github.com/getsentry/XcodeBuildMCP/issues/417)).
- Fixed simulator-name session defaults in the CLI so a name-only default resolves to a simulator ID for tools that take an ID, resolves before simulator lifecycle operations, and does not add conflicting simulator arguments to tools that already accept a name.
- Fixed CLI JSON output so simulator-name resolution failures return the structured error envelope instead of plain stderr, and a launch failure during resolution is no longer reported as a macOS launch failure.
- Fixed `type_text` so characters AXe cannot type, such as accented or other international characters, fail with a clear recoverable error before the field is focused instead of a generic typing failure.
- Fixed CLI numeric array flags so comma-separated values such as `--key-codes 23,18,14` are parsed as numbers instead of failing validation.

Various other internal improvements to stability, performance, and code quality.

<a id="option-a--homebrew-no-nodejs-required-4"></a>

##### Option A — Homebrew (no Node.js required)

Install:

```
brew tap getsentry/xcodebuildmcp
brew install xcodebuildmcp
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "xcodebuildmcp",
  "args": ["mcp"]
}
```

<a id="option-b--npm--npx-nodejs-18-4"></a>

##### Option B — npm / npx (Node.js 18+)

Install:

```
npm install -g xcodebuildmcp@latest
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "npx",
  "args": ["-y", "xcodebuildmcp@latest", "mcp"]
}
```

📦 **NPM Package**: <https://www.npmjs.com/package/xcodebuildmcp/v/2.6.0>

<a id="v2.5.2"></a>

### Release v2.5.2

May 12, 2026

[View on GitHub ↗](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.5.2)

<a id="release-v252"></a>

#### Release v2.5.2

<a id="changed-1"></a>

##### Changed

- Updated the bundled AXe binary used by UI automation tools to 1.7.0.

<a id="fixed-4"></a>

##### Fixed

- Fixed a log-capture vulnerability where a crafted `bundleId` or custom subsystem filter could broaden simulator log streams to capture output from other apps or Apple system subsystems. Bundle IDs and subsystem filters are now validated against a strict allowlist before reaching the predicate ([#407](https://github.com/getsentry/XcodeBuildMCP/pull/407) by [@sebastiondev](https://github.com/sebastiondev)).
- Fixed `debug_attach_sim` so an explicit `pid` overrides an inherited `bundleId` session default before mutual-exclusion validation ([#410](https://github.com/getsentry/XcodeBuildMCP/issues/410)).

<a id="option-a--homebrew-no-nodejs-required-5"></a>

##### Option A — Homebrew (no Node.js required)

Install:

```
brew tap getsentry/xcodebuildmcp
brew install xcodebuildmcp
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "xcodebuildmcp",
  "args": ["mcp"]
}
```

<a id="option-b--npm--npx-nodejs-18-5"></a>

##### Option B — npm / npx (Node.js 18+)

Install:

```
npm install -g xcodebuildmcp@latest
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "npx",
  "args": ["-y", "xcodebuildmcp@latest", "mcp"]
}
```

📦 **NPM Package**: <https://www.npmjs.com/package/xcodebuildmcp/v/2.5.2>

<a id="v2.5.1"></a>

### Release v2.5.1

May 8, 2026

[View on GitHub ↗](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.5.1)

<a id="release-v251"></a>

#### Release v2.5.1

<a id="fixed-5"></a>

##### Fixed

- Fixed portable macOS/Homebrew installs missing structured output schemas, which prevented MCP clients from loading tools.

<a id="option-a--homebrew-no-nodejs-required-6"></a>

##### Option A — Homebrew (no Node.js required)

Install:

```
brew tap getsentry/xcodebuildmcp
brew install xcodebuildmcp
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "xcodebuildmcp",
  "args": ["mcp"]
}
```

<a id="option-b--npm--npx-nodejs-18-6"></a>

##### Option B — npm / npx (Node.js 18+)

Install:

```
npm install -g xcodebuildmcp@latest
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "npx",
  "args": ["-y", "xcodebuildmcp@latest", "mcp"]
}
```

📦 **NPM Package**: <https://www.npmjs.com/package/xcodebuildmcp/v/2.5.1>

<a id="v2.5.0"></a>

### Release v2.5.0

May 7, 2026

[View on GitHub ↗](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.5.0)

<a id="release-v250"></a>

#### Release v2.5.0

<a id="breaking-1"></a>

##### Breaking

<a id="standalone-log-capture-tools-removed"></a>

##### Standalone log-capture tools removed

The old `logging` workflow and its standalone log-capture tools (`start_sim_log_cap`, `stop_sim_log_cap`, `start_device_log_cap`, `stop_device_log_cap`, and `launch_app_logs_sim`) have been removed. This affects users, scripts, and agents that call those tool names directly.

Use the launch or build-and-run tools instead. They return runtime log paths as part of the normal result, so agents no longer need a separate start/stop log-capture sequence.

Before:

```
xcodebuildmcp logging start-sim-log-cap --simulator-id <UDID> --bundle-id com.example.MyApp
xcodebuildmcp simulator launch-app --simulator-id <UDID> --bundle-id com.example.MyApp
xcodebuildmcp logging stop-sim-log-cap --pid <PID>
```

After:

```
xcodebuildmcp simulator build-and-run --scheme MyApp --project-path ./MyApp.xcodeproj

# Or, for an app that is already installed on a simulator:
xcodebuildmcp simulator launch-app --simulator-id <UDID> --bundle-id com.example.MyApp
```

For MCP clients, use `build_run_sim` or `launch_app_sim` and read the returned runtime log path.

<a id="runtime-launch-arguments-now-use-launchargs"></a>

##### Runtime launch arguments now use `launchArgs`

Build-and-run and launch-only tools now separate build settings from app launch arguments. This affects users, scripts, and agents that previously passed runtime arguments through `extraArgs` or the launch-only `args` input.

If you do nothing, app runtime arguments may not reach the launched process, and launch-only calls that still use `args` will fail validation. Move app arguments to `launchArgs`; keep `extraArgs` only for `xcodebuild` flags and build setting overrides.

Before:

```
xcodebuildmcp simulator build-and-run --json '{
  "scheme": "MyApp",
  "projectPath": "./MyApp.xcodeproj",
  "extraArgs": ["--uitesting"]
}'
```

After:

```
xcodebuildmcp simulator build-and-run --json '{
  "scheme": "MyApp",
  "projectPath": "./MyApp.xcodeproj",
  "launchArgs": ["--uitesting"]
}'
```

Launch-only tools use the same input:

```
xcodebuildmcp simulator launch-app --json '{
  "simulatorId": "<UDID>",
  "bundleId": "com.example.MyApp",
  "launchArgs": ["--uitesting"]
}'
```

For MCP clients, use `launchArgs` on `build_run_sim`, `build_run_device`, `build_run_macos`, `launch_app_sim`, `launch_app_device`, and `launch_mac_app`. See [CLI](https://xcodebuildmcp.com/docs/cli#build-and-run-in-one-step).

<a id="new-structured-outputs"></a>

##### New! Structured outputs

XcodeBuildMCP now returns structured, machine-readable results across supported MCP clients and the CLI. Agents and scripts no longer have to scrape prose to find build status, log paths, bundle IDs, process IDs, test failures, or app paths. The human-readable text remains available, but every supported result now has a consistent envelope with the same fields:

```
{
  "schema": "xcodebuildmcp.output.build-run-result",
  "schemaVersion": "1",
  "didError": false,
  "error": null,
  "data": { }
}
```

For agents, this reduces token usage and makes tool results easier to act on reliably. Instead of rereading a full text transcript to find the build log, runtime log, or launched process, the agent can jump straight to fields such as `data.artifacts.buildLogPath`, `data.artifacts.runtimeLogPath`, `data.artifacts.osLogPath`, `data.artifacts.appPath`, `data.artifacts.bundleId`, and `data.artifacts.processId`.

<a id="mcp-clients"></a>

##### MCP clients

MCP clients that support structured tool results receive `structuredContent` alongside the existing text response. The text remains useful for humans and older clients; supported clients can use the structured fields directly.

Example Build & Run result shape:

```
{
  "schema": "xcodebuildmcp.output.build-run-result",
  "schemaVersion": "1",
  "didError": false,
  "error": null,
  "data": {
    "summary": { "status": "SUCCEEDED", "durationMs": 1234, "target": "simulator" },
    "artifacts": {
      "appPath": "~/Library/Developer/XcodeBuildMCP/DerivedData/.../CalculatorApp.app",
      "bundleId": "io.sentry.calculatorapp",
      "processId": 99999,
      "buildLogPath": "~/Library/Developer/XcodeBuildMCP/logs/build_run_sim_...log",
      "runtimeLogPath": "~/Library/Developer/XcodeBuildMCP/logs/io.sentry.calculatorapp_...log",
      "osLogPath": "~/Library/Developer/XcodeBuildMCP/logs/io.sentry.calculatorapp_oslog_...log"
    }
  }
}
```

<a id="cli-json-output"></a>

##### CLI JSON output

The CLI now supports `--output text|json|jsonl|raw` for tool commands. `text` remains the default. Use `--output json` when a script, CI job, or agent needs one final result document:

```
xcodebuildmcp simulator build-and-run --output json
```

```
{
  "schema": "xcodebuildmcp.output.build-run-result",
  "schemaVersion": "1",
  "didError": false,
  "error": null,
  "data": {
    "request": { "scheme": "CalculatorApp", "platform": "iOS Simulator" },
    "summary": { "status": "SUCCEEDED", "durationMs": 1234, "target": "simulator" },
    "artifacts": { "buildLogPath": "~/Library/Developer/XcodeBuildMCP/logs/build_run_sim_...log" },
    "diagnostics": { "warnings": [], "errors": [] }
  }
}
```

Use `--output jsonl` for live progress as newline-delimited JSON, one event per line:

```
{"event":"build-result.invocation","operation":"BUILD","request":{"scheme":"CalculatorApp","platform":"iOS Simulator"}}
{"event":"build-result.build-stage","operation":"BUILD","stage":"COMPILING","message":"Compiling CalculatorApp"}
{"event":"build-result.build-summary","operation":"BUILD","status":"SUCCEEDED","durationMs":3421}
```

Failures use the same envelope as successes, so callers can rely on `didError`, `error`, `data.summary`, `data.diagnostics`, and test-specific fields like `testCases` and `testFailures` instead of handling every command differently.

<a id="published-schemas"></a>

##### Published schemas

The structured result contracts are published as JSON Schema and can be used to validate output or generate types:

```
https://xcodebuildmcp.com/schemas/structured-output/<schema-name>/<version>.schema.json
```

For example: [`xcodebuildmcp.output.build-run-result` v1](https://xcodebuildmcp.com/schemas/structured-output/xcodebuildmcp.output.build-run-result/1.schema.json). See [Output Formats](https://xcodebuildmcp.com/docs/output-formats) for the full reference.

<a id="added-2"></a>

##### Added

- Added `xcodebuildmcp upgrade` to check for available updates and upgrade in place, with `--check` for report-only use and `--yes`/`-y` for non-interactive upgrades.
- Added a platform-aware `xcodebuildmcp setup` wizard: choose macOS, iOS, tvOS, watchOS, or visionOS up front; get platform-appropriate workflow recommendations; skip simulator/device prompts for macOS-only projects; and reuse previous choices when re-running setup. Single-platform setups also include the platform in generated config and `--format mcp-json` output. See [Setup](https://xcodebuildmcp.com/docs/setup) ([#365](https://github.com/getsentry/XcodeBuildMCP/pull/365), based on work by [@ichoosetoaccept](https://github.com/ichoosetoaccept)).
- Added `XCODEBUILDMCP_CWD` so MCP clients that cannot choose the server's start directory can still point project config discovery and relative-path resolution at the right workspace. See [Environment Variables](https://xcodebuildmcp.com/docs/env-vars#general-settings).
- Added per-test timing output, so agents and scripts can identify slow tests without opening the full test report. JSON and structured results include a `testCases` list, and text output can show per-test durations with `showTestTiming` or `XCODEBUILDMCP_SHOW_TEST_TIMING=1` ([#339](https://github.com/getsentry/XcodeBuildMCP/pull/339) by [@codeman9](https://github.com/codeman9)).
- Added default result bundles for simulator, device, macOS, and Swift Package test runs, so agents can inspect detailed test artifacts without manually choosing a result bundle path.
- Added opt-in idle shutdown for unused MCP server processes via `XCODEBUILDMCP_MCP_IDLE_TIMEOUT_MS`, reducing leftover background processes for clients that keep server sessions open ([#398](https://github.com/getsentry/XcodeBuildMCP/pull/398)). See [Environment Variables](https://xcodebuildmcp.com/docs/env-vars#mcp-idle-shutdown).
- Added `toggle_software_keyboard` and `toggle_connect_hardware_keyboard` tools for showing/hiding the iOS Simulator software keyboard and connecting/disconnecting the Mac hardware keyboard. See [Tools Reference](https://xcodebuildmcp.com/docs/tools) ([#346](https://github.com/getsentry/XcodeBuildMCP/issues/346), [#347](https://github.com/getsentry/XcodeBuildMCP/pull/347) by [@yjmeqt](https://github.com/yjmeqt)).
- Added tvOS, watchOS, and visionOS support to `build_device`, so physical-device builds are no longer limited to iOS. See [Device Code Signing](https://xcodebuildmcp.com/docs/device-signing) ([#352](https://github.com/getsentry/XcodeBuildMCP/pull/352) by [@bitxeno](https://github.com/bitxeno)).

<a id="changed-2"></a>

##### Changed

- CLI build and test commands now show live progress while they are running instead of waiting until the command finishes. See [Output Formats](https://xcodebuildmcp.com/docs/output-formats).
- CLI text output now shows file paths in a more readable `Files:` list by default. Use `--file-path-render-style tree`, `filePathRenderStyle`, or `XCODEBUILDMCP_FILE_PATH_RENDER_STYLE` if you prefer the compact tree layout used by MCP text responses ([#402](https://github.com/getsentry/XcodeBuildMCP/pull/402)). See [Output Formats](https://xcodebuildmcp.com/docs/output-formats#output-text).
- Xcode IDE tool results are now shorter in final output, with full details still accessible when needed. CLI JSON and JSONL output now work for Xcode IDE tool calls too ([#396](https://github.com/getsentry/XcodeBuildMCP/pull/396)).
- Runtime log capture is more reliable across restarts, cleans itself up when apps stop or the server shuts down, and avoids stopping active log streams from another workspace ([#382](https://github.com/getsentry/XcodeBuildMCP/issues/382)).
- XcodeBuildMCP now cleans up old logs and temporary build artifacts more reliably without disrupting concurrent active sessions ([#391](https://github.com/getsentry/XcodeBuildMCP/pull/391)).
- Builds and tests now use an isolated DerivedData location per workspace or project when you have not set `derivedDataPath`, reducing cross-project build conflicts while keeping explicit `derivedDataPath` settings unchanged ([#340](https://github.com/getsentry/XcodeBuildMCP/issues/340), [#341](https://github.com/getsentry/XcodeBuildMCP/pull/341) by [@codeman9](https://github.com/codeman9)).
- Long-form documentation has moved to [xcodebuildmcp.com/docs](https://xcodebuildmcp.com/docs), with the README focused on installation, setup, and quick links to the hosted guides.

<a id="fixed-6"></a>

##### Fixed

- Fixed shell-injection vulnerabilities when user-provided values were passed to Apple developer tools, log-capture queries, bundle ID extraction, and macOS launch flows ([#289](https://github.com/getsentry/XcodeBuildMCP/pull/289) by [@sebastiondev](https://github.com/sebastiondev), [#390](https://github.com/getsentry/XcodeBuildMCP/pull/390) by [@voidborne-d](https://github.com/voidborne-d)).
- Fixed a path traversal vulnerability that could allow reading files outside the expected scope.
- Fixed portable macOS installs missing a required runtime dependency, which could make packaged installs fail when commands needed file matching.
- Fixed configured paths that begin with `~` or `~/` so project, workspace, DerivedData, AXe, and template paths resolve under the user's home directory instead of creating literal `~` folders. Absolute configured paths are now normalized before use ([#283](https://github.com/getsentry/XcodeBuildMCP/issues/283), supersedes [#301](https://github.com/getsentry/XcodeBuildMCP/pull/301) by [@trmquang93](https://github.com/trmquang93)).
- Fixed device build next-step guidance so agents no longer suggest unsupported `--device-id` or `deviceId` arguments ([#287](https://github.com/getsentry/XcodeBuildMCP/issues/287), [#300](https://github.com/getsentry/XcodeBuildMCP/pull/300) by [@trmquang93](https://github.com/trmquang93), [#350](https://github.com/getsentry/XcodeBuildMCP/pull/350) by [@MukundaKatta](https://github.com/MukundaKatta)).
- Fixed Xcode IDE manual disconnect immediately reconnecting after the user explicitly disconnected it ([#343](https://github.com/getsentry/XcodeBuildMCP/issues/343), [#344](https://github.com/getsentry/XcodeBuildMCP/pull/344) by [@shaun0927](https://github.com/shaun0927)).
- Fixed simulator defaults refresh so stale simulator IDs are reconciled when both a simulator name and ID are configured, without rewriting shared project config files unnecessarily ([#357](https://github.com/getsentry/XcodeBuildMCP/issues/357)).
- Fixed session profile output so the `persisted` field accurately reflects whether a profile switch was saved.
- Fixed long-running commands that could hang even after completing.
- Fixed build and test failures after command startup returning incomplete output; they now finish with a clear error result and log paths.
- Fixed final text and JSON results changing unexpectedly when commands also stream live progress ([#360](https://github.com/getsentry/XcodeBuildMCP/issues/360)).
- Fixed test result output so agents can find xcresult bundle paths after simulator, device, macOS, and Swift Package test runs ([#397](https://github.com/getsentry/XcodeBuildMCP/pull/397)).
- Fixed test summaries and progress output so CLI tests no longer show false compiler errors, mixed Swift Testing/XCTest suites are counted accurately, parameterized Swift Testing cases are not overcounted, and simulator test progress stays visible while tests run ([#383](https://github.com/getsentry/XcodeBuildMCP/issues/383), [#392](https://github.com/getsentry/XcodeBuildMCP/issues/392)).
- Fixed device tool calls that use session defaults so they no longer fail when platform is omitted.

Various other internal improvements to stability, performance, and code quality.

<a id="option-a--homebrew-no-nodejs-required-7"></a>

##### Option A — Homebrew (no Node.js required)

Install:

```
brew tap getsentry/xcodebuildmcp
brew install xcodebuildmcp
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "xcodebuildmcp",
  "args": ["mcp"]
}
```

<a id="option-b--npm--npx-nodejs-18-7"></a>

##### Option B — npm / npx (Node.js 18+)

Install:

```
npm install -g xcodebuildmcp@latest
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "npx",
  "args": ["-y", "xcodebuildmcp@latest", "mcp"]
}
```

📦 **NPM Package**: <https://www.npmjs.com/package/xcodebuildmcp/v/2.5.0>

<a id="v2.5.0-beta.1"></a>

### Release v2.5.0-beta.1

April 30, 2026

pre-release[View on GitHub ↗](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.5.0-beta.1)

<a id="release-v250-beta1"></a>

#### Release v2.5.0-beta.1

<a id="breaking-2"></a>

##### Breaking

<a id="legacy-standalone-log-capture-tools-removed"></a>

##### Legacy standalone log-capture tools removed

The old `logging` workflow and its standalone log-capture tools (`start_sim_log_cap`, `stop_sim_log_cap`, `start_device_log_cap`, `stop_device_log_cap`, and `launch_app_logs_sim`) have been removed. This affects users, scripts, and agents that call those tool names directly.

Use the launch or build-and-run tools instead. They return runtime log paths as part of the normal result, so agents no longer need a separate start/stop log-capture sequence.

Before:

```
xcodebuildmcp logging start-sim-log-cap --simulator-id <UDID> --bundle-id com.example.MyApp
xcodebuildmcp simulator launch-app --simulator-id <UDID> --bundle-id com.example.MyApp
xcodebuildmcp logging stop-sim-log-cap --pid <PID>
```

After:

```
xcodebuildmcp simulator build-and-run --scheme MyApp --project-path ./MyApp.xcodeproj

# Or, for an app that is already installed on a simulator:
xcodebuildmcp simulator launch-app --simulator-id <UDID> --bundle-id com.example.MyApp
```

For MCP clients, use `build_run_sim`, `launch_app_sim`, or `build_run_device` and read the returned runtime log path.

<a id="new-structured-outputs-1"></a>

##### New! Structured outputs

XcodeBuildMCP now returns structured, machine-readable results across supported MCP clients and the CLI. Agents and scripts no longer have to scrape prose to find build status, log paths, bundle IDs, process IDs, test failures, or app paths. The human-readable text remains available, but every supported result now has a consistent envelope with the same frontmatter fields:

```
{
  "schema": "xcodebuildmcp.output.build-run-result",
  "schemaVersion": "1",
  "didError": false,
  "error": null,
  "data": { }
}
```

For agents, this reduces token usage and makes tool results easier to act on reliably. Instead of rereading a full text transcript to find the build log, runtime log, or launched process, the agent can jump straight to fields such as `data.artifacts.buildLogPath`, `data.artifacts.runtimeLogPath`, `data.artifacts.osLogPath`, `data.artifacts.appPath`, `data.artifacts.bundleId`, and `data.artifacts.processId`.

<a id="mcp-clients-1"></a>

##### MCP clients

MCP clients that support structured tool results receive `structuredContent` alongside the existing text response. The text remains useful for humans and older clients; supported clients can use the structured fields directly.

Example Build & Run result shape:

```
{
  "schema": "xcodebuildmcp.output.build-run-result",
  "schemaVersion": "1",
  "didError": false,
  "error": null,
  "data": {
    "summary": { "status": "SUCCEEDED", "durationMs": 1234, "target": "simulator" },
    "artifacts": {
      "appPath": "~/Library/Developer/XcodeBuildMCP/DerivedData/.../CalculatorApp.app",
      "bundleId": "io.sentry.calculatorapp",
      "processId": 99999,
      "buildLogPath": "~/Library/Developer/XcodeBuildMCP/logs/build_run_sim_...log",
      "runtimeLogPath": "~/Library/Developer/XcodeBuildMCP/logs/io.sentry.calculatorapp_...log",
      "osLogPath": "~/Library/Developer/XcodeBuildMCP/logs/io.sentry.calculatorapp_oslog_...log"
    }
  }
}
```

<a id="cli-json-output-1"></a>

##### CLI JSON output

The CLI now supports `--output text|json|jsonl|raw` for tool commands. `text` remains the default. Use `--output json` when a script, CI job, or agent needs one final result document:

```
xcodebuildmcp simulator build-and-run --output json
```

```
{
  "schema": "xcodebuildmcp.output.build-run-result",
  "schemaVersion": "1",
  "didError": false,
  "error": null,
  "data": {
    "request": { "scheme": "CalculatorApp", "platform": "iOS Simulator" },
    "summary": { "status": "SUCCEEDED", "durationMs": 1234, "target": "simulator" },
    "artifacts": { "buildLogPath": "~/Library/Developer/XcodeBuildMCP/logs/build_run_sim_...log" },
    "diagnostics": { "warnings": [], "errors": [] }
  }
}
```

Use `--output jsonl` for live progress as newline-delimited JSON, one event per line:

```
{"event":"build-result.invocation","operation":"BUILD","request":{"scheme":"CalculatorApp","platform":"iOS Simulator"}}
{"event":"build-result.build-stage","operation":"BUILD","stage":"COMPILING","message":"Compiling CalculatorApp"}
{"event":"build-result.build-summary","operation":"BUILD","status":"SUCCEEDED","durationMs":3421}
```

Failures use the same envelope as successes, so callers can rely on `didError`, `error`, `data.summary`, `data.diagnostics`, and test-specific fields like `testCases` and `testFailures` instead of handling every command differently.

<a id="published-schemas-1"></a>

##### Published schemas

The structured result contracts are published as JSON Schema and can be used to validate output or generate types:

```
https://xcodebuildmcp.com/schemas/structured-output/<schema-name>/<version>.schema.json
```

For example: [`xcodebuildmcp.output.build-run-result` v1](https://xcodebuildmcp.com/schemas/structured-output/xcodebuildmcp.output.build-run-result/1.schema.json). See [Output Formats](https://xcodebuildmcp.com/docs/output-formats) for the full reference.

<a id="added-3"></a>

##### Added

- Added `xcodebuildmcp upgrade` to check for available updates and upgrade in place, with `--check` for report-only use and `--yes`/`-y` for non-interactive upgrades.
- Added a platform-aware `xcodebuildmcp setup` wizard: choose macOS, iOS, tvOS, watchOS, or visionOS up front; get platform-appropriate workflow recommendations; skip simulator/device prompts for macOS-only projects; and reuse previous choices when re-running setup. Single-platform setups also include the platform in generated config and `--format mcp-json` output. See [Setup](https://xcodebuildmcp.com/docs/setup) ([#365](https://github.com/getsentry/XcodeBuildMCP/pull/365), based on work by [@ichoosetoaccept](https://github.com/ichoosetoaccept)).
- Added `XCODEBUILDMCP_CWD` so MCP clients that cannot choose the server's start directory can still point project config discovery and relative-path resolution at the right workspace.
- Added per-test timing output for test runs. JSON and structured results now include a `testCases` list, and text output can show per-test durations with the `showTestTiming` config option or `XCODEBUILDMCP_SHOW_TEST_TIMING=1` ([#339](https://github.com/getsentry/XcodeBuildMCP/pull/339) by [@codeman9](https://github.com/codeman9)).
- Added `toggle_software_keyboard` and `toggle_connect_hardware_keyboard` tools for showing/hiding the iOS Simulator software keyboard and connecting/disconnecting the Mac hardware keyboard. See [Tools Reference](https://xcodebuildmcp.com/docs/tools) ([#346](https://github.com/getsentry/XcodeBuildMCP/issues/346), [#347](https://github.com/getsentry/XcodeBuildMCP/pull/347) by [@yjmeqt](https://github.com/yjmeqt)).
- Added tvOS, watchOS, and visionOS support to `build_device`, so physical-device builds are no longer limited to iOS. See [Device Code Signing](https://xcodebuildmcp.com/docs/device-signing) ([#352](https://github.com/getsentry/XcodeBuildMCP/pull/352) by [@bitxeno](https://github.com/bitxeno)).

<a id="changed-3"></a>

##### Changed

- CLI build and test commands now show live progress while they are running instead of waiting until the command finishes. See [Output Formats](https://xcodebuildmcp.com/docs/output-formats).
- Runtime log capture is more reliable across server restarts and cleans itself up when apps stop or the server shuts down, reducing orphaned background log streams.
- Builds and tests now use an isolated DerivedData location per workspace or project when you have not set `derivedDataPath`, reducing cross-project build conflicts while keeping explicit `derivedDataPath` settings unchanged ([#340](https://github.com/getsentry/XcodeBuildMCP/issues/340), [#341](https://github.com/getsentry/XcodeBuildMCP/pull/341) by [@codeman9](https://github.com/codeman9)).
- Long-form documentation has moved to [xcodebuildmcp.com/docs](https://xcodebuildmcp.com/docs), with the README focused on installation, setup, and quick links to the hosted guides.

<a id="fixed-7"></a>

##### Fixed

- Fixed a shell injection vulnerability when user-provided values were passed to Apple developer tools and log-capture queries ([#289](https://github.com/getsentry/XcodeBuildMCP/pull/289) by [@sebastiondev](https://github.com/sebastiondev)).
- Fixed a path traversal vulnerability in structured-output schema loading so schema requests cannot read outside the bundled schema files.
- Fixed configured paths that begin with `~` or `~/` so project, workspace, DerivedData, AXe, and template paths resolve under the user's home directory instead of creating literal `~` folders. Absolute configured paths are now normalized before use ([#283](https://github.com/getsentry/XcodeBuildMCP/issues/283), supersedes [#301](https://github.com/getsentry/XcodeBuildMCP/pull/301) by [@trmquang93](https://github.com/trmquang93)).
- Fixed device build next-step guidance so agents no longer suggest unsupported `--device-id` or `deviceId` arguments ([#287](https://github.com/getsentry/XcodeBuildMCP/issues/287), [#300](https://github.com/getsentry/XcodeBuildMCP/pull/300) by [@trmquang93](https://github.com/trmquang93), [#350](https://github.com/getsentry/XcodeBuildMCP/pull/350) by [@MukundaKatta](https://github.com/MukundaKatta)).
- Fixed Xcode IDE manual disconnect immediately reconnecting after the user explicitly disconnected it ([#343](https://github.com/getsentry/XcodeBuildMCP/issues/343), [#344](https://github.com/getsentry/XcodeBuildMCP/pull/344) by [@shaun0927](https://github.com/shaun0927)).
- Fixed simulator defaults refresh so stale simulator IDs are reconciled when both a simulator name and ID are configured, without rewriting shared project config files unnecessarily ([#357](https://github.com/getsentry/XcodeBuildMCP/issues/357)).
- Fixed session profile JSON output so callers can rely on `persisted: true` after persisting a profile switch.
- Fixed some long-running commands hanging after the underlying Apple tool finished, especially when helper processes kept output streams open.
- Fixed build and test failures after command startup returning incomplete output; they now finish with a clear error result and log paths.

Various other internal improvements to stability, performance, and code quality.

<a id="option-a--homebrew-no-nodejs-required-8"></a>

##### Option A — Homebrew (no Node.js required)

Install:

```
brew tap getsentry/xcodebuildmcp
brew install xcodebuildmcp
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "xcodebuildmcp",
  "args": ["mcp"]
}
```

<a id="option-b--npm--npx-nodejs-18-8"></a>

##### Option B — npm / npx (Node.js 18+)

Install:

```
npm install -g xcodebuildmcp@latest
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "npx",
  "args": ["-y", "xcodebuildmcp@latest", "mcp"]
}
```

📦 **NPM Package**: <https://www.npmjs.com/package/xcodebuildmcp/v/2.5.0-beta.1>

<a id="v2.3.2"></a>

### Release v2.3.2

March 31, 2026

[View on GitHub ↗](https://github.com/getsentry/MobileBuildMCP/releases/tag/v2.3.2)

<a id="release-v232"></a>

#### Release v2.3.2

<a id="fixed-8"></a>

##### Fixed

- Improved reliability of internal telemetry during shutdown ([#302](https://github.com/getsentry/XcodeBuildMCP/pull/302)).

<a id="option-a--homebrew-no-nodejs-required-9"></a>

##### Option A — Homebrew (no Node.js required)

Install:

```
brew tap getsentry/xcodebuildmcp
brew install xcodebuildmcp
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "xcodebuildmcp",
  "args": ["mcp"]
}
```

<a id="option-b--npm--npx-nodejs-18-9"></a>

##### Option B — npm / npx (Node.js 18+)

Install:

```
npm install -g xcodebuildmcp@latest
```

MCP config:

```
"XcodeBuildMCP": {
  "command": "npx",
  "args": ["-y", "xcodebuildmcp@latest", "mcp"]
}
```

📦 **NPM Package**: <https://www.npmjs.com/package/xcodebuildmcp/v/2.3.2>

[See every release on GitHub →](https://github.com/getsentry/MobileBuildMCP/releases)

[← Previous

Storage Management](https://www.mobilebuildmcp.com/docs/storage-management)[Next →

Contributing](https://www.mobilebuildmcp.com/docs/contributing)
