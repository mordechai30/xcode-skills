---
name: xcodebuildmcp-cli
description: Build, run, and debug Apple platform projects with MobileBuildMCP CLI and MCP tools, and Xcode IDE tools when needed.
---

# MobileBuildMCP and Xcode

- All scripts (Python, Bash) and CLI commands must be run outside sandbox restrictions.

## Choose the route

- For macOS and physical iOS builds and runs, start with the `mobilebuildmcp` CLI (`macos` or `device`). It works without an open Xcode IDE and exposes commands regardless of MCP `enabledWorkflows`. Use [CLI](references/cli.md) for command behavior and [workflows](references/workflows.md) for workflow scope.
- Use MobileBuildMCP MCP tools when the required workflow is exposed and a specific benefit matters, such as an existing stateful server session or mutable session defaults. Do not choose MCP solely because an agent has several steps. CLI project defaults and named profiles also avoid repeated arguments; only MCP session changes persist across its calls. See [configuration](references/configuration.md) and [MCP mode](references/mcp-mode.md).
- For debugging an app in an open Xcode workspace, use direct Xcode MCP tools for the IDE run session, console, and LLDB. MobileBuildMCP's `debugging` workflow targets simulator apps; do not assume it can attach to macOS or physical iOS apps. Use the [Xcode IDE Bridge](references/xcode-ide.md) only when direct Xcode tools are unavailable or its proxy is needed.
- Use raw `xcodebuild`, `xcrun`, or `simctl` only when the chosen interface cannot perform the required action.

## Discover the needed command or tool

- Inspect tools available in the current Codex session. MobileBuildMCP's MCP server exposes only the simulator workflow by default. If using MCP regularly for macOS or physical iOS, enable only the needed `macos` and `device` tools or a custom workflow; a new Codex session may be needed to see changes. See [workflows](references/workflows.md), [configuration](references/configuration.md), and [MCP mode](references/mcp-mode.md). Workflow selection controls MCP advertisement, not CLI commands.
- For CLI, check `mobilebuildmcp --version`, then discover only what is needed with `mobilebuildmcp --help`, `mobilebuildmcp <workflow> --help`, and `mobilebuildmcp <workflow> <tool> --help`. Use `mobilebuildmcp tools` for the full catalog. The vendor's optional agent skills are described in [agent skills](references/skills.md); check installed `init --help` before using its client flags.
- Before a build or run, inspect `.mobilebuildmcp/config.yaml` and relevant command help. CLI fills configured `sessionDefaults`; `--profile` selects a named profile for one call, and explicit flags override defaults. For MCP, inspect server-held defaults. See [configuration](references/configuration.md).

## Execute and verify

- Choose the smallest action that meets the request. For run intent, prefer `build-and-run`; build separately only when a build-only result is needed.
- Use CLI text for routine reading, JSON for final structured data, and JSONL for live machine-readable progress. Check `schema` and `didError` in structured results. See [output formats](references/output-formats.md) and [schemas](references/schemas.md).
- Stateful CLI commands use an automatically started per-workspace daemon. If startup fails, inspect status and logs, start it outside the sandbox, and retry once. See [CLI daemon guidance](references/cli.md).
- For MCP registration or migration, see [clients](references/clients.md), [setup](references/setup.md), and [v2 migration](references/migration-v2.md). The server launch command ends with `mcp`.

Report the route used, the result, and any relevant artifact or diagnostic path. State what could not be verified.
