# Xcode Tools Documentation

Reference documentation for Xcode’s MCP server. It lets AI coding assistants browse and edit projects, build apps, run tests, and render previews.

> Covers **Xcode 27**. See the [changelog](CHANGELOG.md) for changes since Xcode 26.5 and the additions in [Xcode 27.2 beta](CHANGELOG.md#xcode-272-beta).

<p align="center">
  <img src=".github/screenshot.png" width="60%"/>
</p>

## Quick start

**1. Open your project or workspace in Xcode 27.** For setup without an Xcode window, see [Headless mode](headless.md#headless-mode).

**2. Register the server** with your coding tool. `xcrun mcpbridge` is the bridge into Xcode:

```bash
# Claude Code
claude mcp add --transport stdio xcode -- xcrun mcpbridge

# Codex
codex mcp add xcode -- xcrun mcpbridge
```

**3. Verify** with `claude mcp list` / `codex mcp list`, then ask the assistant to call [`XcodeListWindows`](tools.md#xcodelistwindows) — it returns the open windows and the `tabIdentifier` of each.

> **Choosing a workspace:** most tools take an optional `tabIdentifier` — which Xcode workspace tab to act on. Omit it when only one tab is open. In [headless mode](headless.md#headless-mode) it is named `workspaceIdentifier` and takes a workspace identifier or an absolute path instead.

## Tool categories

| Category | What you can do |
|---|---|
| [Workspaces and Projects](tools.md#workspaces-and-projects) | Open workspaces and create projects or targets |
| [Files](tools.md#files) | Find, read, and edit project files |
| [Configuration](tools.md#configuration) | Manage targets, schemes, destinations, and build settings |
| [Build and Run](tools.md#build-and-run) | Build and launch apps, inspect diagnostics and logs |
| [Previews and Debugging](tools.md#previews-and-debugging) | Render previews, run snippets, and use LLDB |
| [Testing](tools.md#testing) | Select test plans and run tests |
| [Devices and Simulators](tools.md#devices-and-simulators) | Install apps and interact with their UI |
| [Localization](tools.md#localization) | Read and translate String Catalogs |
| [Crashes and Performance](tools.md#crashes-and-performance) | Investigate crash and performance reports |
| [Documentation](tools.md#documentation) | Search Apple Developer Documentation |

## Further documentation

| Guide | Contents |
|---|---|
| [Tool reference](tools.md) | Full tool index, parameters, and examples |
| [Headless mode](headless.md) | Setup without an Xcode window, permissions, and server internals |
| [Agent tooling](agent-tooling.md) | Bridge configuration, agent launcher, skill export, and the separate LLDB server |
| [Schemas](schemas.md) | Raw MCP tool definitions by Xcode version and mode |
| [Changelog](CHANGELOG.md) | Changes in Xcode 27 and 27.2 beta |

## Apple Documentation

- [Setting up coding intelligence](https://developer.apple.com/documentation/xcode/setting-up-coding-intelligence)
- [Writing code with intelligence in Xcode](https://developer.apple.com/documentation/xcode/writing-code-with-intelligence-in-xcode)
- [Giving agentic coding tools access to Xcode](https://developer.apple.com/documentation/xcode/giving-agentic-coding-tools-access-to-xcode)

## Author

Artem Novichkov, https://artemnovichkov.com
