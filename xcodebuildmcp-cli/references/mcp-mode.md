# MCP Server Mode

Source: https://www.mobilebuildmcp.com/docs/mcp-mode

What the server exposes, how it behaves, and where the edges are.

## Starting the server

MCP clients spawn the server over stdio. You don't run it yourself, your client does, based on the config you set in [MCP Clients](https://www.mobilebuildmcp.com/docs/clients).

`mobilebuildmcp mcp`

## What's advertised

The server advertises **tools** and **resources** to the client. Tool surface is controlled by `enabledWorkflows` in your config file or the `MOBILEBUILDMCP_ENABLED_WORKFLOWS` env var, defaulting to just `simulator` to keep agent context small.

## Feature support matrix

| Client | Tools | Resources | Tool-list-changed | Env vars in config |
| --- | --- | --- | --- | --- |
| Claude Code | ✓ | ✓ | ✓ | ✓ |
| Claude Desktop | ✓ | ✓ | — | ✓ |
| Cursor | ✓ | ✓ | — | ✓ |
| Codex CLI | ✓ | ✓ | — | ✓ |
| VS Code (Agent mode) | ✓ | ✓ | — | ✓ |
| Windsurf | ✓ | — | — | ✓ |
| Kiro | ✓ | ✓ | — | ✓ |
| Xcode (Codex / Claude) | ✓ | — | — | ✓ |

## Session defaults

Session defaults are enabled by default and are the single biggest token saver. Tell your agent which workspace (or project), scheme, and simulator to use, and the server stores those values. Every subsequent tool call reuses them automatically, so you do not need to repeat them and your agent does not have to re-state them on every call.

Defaults can also be:

*   Seeded at startup via `.mobilebuildmcp/config.yaml` (`sessionDefaults:`)
*   Set from env vars (`MOBILEBUILDMCP_WORKSPACE_PATH`, `MOBILEBUILDMCP_SCHEME`, etc.)
*   Persisted to disk by passing `persist: true` on `session_set_defaults`

Once a default is set, tools can be called without that parameter and the server fills it in. To require every parameter on every call, set `disableSessionDefaults: true` in `.mobilebuildmcp/config.yaml` (or `MOBILEBUILDMCP_DISABLE_SESSION_DEFAULTS=true`).

See [Session Defaults](https://www.mobilebuildmcp.com/docs/session-defaults) for the full schema.

### Named profiles

For monorepos, keep a separate defaults profile for each sub-project (for example one for the iOS app, one for the watchOS companion). Tell your agent to switch profiles, and it loads the defaults you stored for that profile. Each profile is strictly isolated; they do not inherit from `global`.

## Workflow selection

The MCP server advertises only the tools in your enabled workflows. The default is just `simulator` to keep your agent's context window lean. See [Reference > Workflows](https://www.mobilebuildmcp.com/docs/workflows) for the catalog of available workflows and what each one contains.

Add more workflows in `.mobilebuildmcp/config.yaml`:

```
schemaVersion: 1
enabledWorkflows:
  - simulator
  - debugging
  - ui-automation
```

Or via env (useful for clients that don't read your project's config file):

```
{
  "env": {
    "MOBILEBUILDMCP_ENABLED_WORKFLOWS": "simulator,debugging,ui-automation"
  }
}
```

Context savings

Cutting from the full catalog to `simulator,debugging` drops advertised tool count from 82 to 20 + 8 (minus overlaps), saving roughly 70% of the tool catalog tokens your agent has to keep in context.

### Custom workflows

Define your own named workflow with an explicit tool list:

```
enabledWorkflows: ["my-workflow"]
customWorkflows:
  my-workflow:
    - build_run_sim
    - record_sim_video
    - screenshot
```

Notes:

*   Session-management tools are always auto-included.
*   The `doctor` workflow is auto-included when `debug: true`.
*   Custom workflow names are normalized to lowercase.
*   Unknown tool names are ignored and logged as warnings.

### Experimental workflow discovery

Opt into the `manage-workflows` tool so the agent can add or remove workflows at runtime:

`experimentalWorkflowDiscovery: true`

Requires tools/list_changed support

Some clients (including Cursor, Claude Code, and Codex at the time of writing) do not surface MCP `tools/list_changed` notifications, so runtime workflow changes won't reflect until the session is restarted.

## Xcode IDE bridge

Enable `xcode-ide` to expose Xcode 26+'s `xcrun mcpbridge` tools through MobileBuildMCP. Two meta-tools appear: `xcode_ide_list_tools` and `xcode_ide_call_tool`. The bridge runs as a persistent daemon-backed session. See [Xcode IDE Bridge](https://www.mobilebuildmcp.com/docs/xcode-ide) for details.

## Tool annotations

Every tool declares read-only, destructive, and open-world hints so MCP clients that respect annotations can skip unnecessary confirmation prompts for lower-risk calls and keep prompts for risky ones.

## Idle shutdown

MCP server mode does not shut down for idleness by default. To opt in, set `MOBILEBUILDMCP_MCP_IDLE_TIMEOUT_MS` to a positive number of milliseconds in your MCP client env config.

```
{
  "env": {
    "MOBILEBUILDMCP_MCP_IDLE_TIMEOUT_MS": "600000"
  }
}
```

When enabled, the server exits through the normal graceful shutdown path only after the idle timeout has elapsed, no MCP request is in flight, and no registered runtime operation is active. Use `0` or omit the variable to keep idle shutdown disabled.

Client reconnect behavior varies

Idle shutdown closes the MCP stdio connection from the server side. Claude Code and Codex CLI are expected to respawn MCP servers after disconnects, but other MCP clients may not handle this gracefully. Keep this disabled unless your client can recover from the server exiting, and choose a timeout long enough for normal pauses between agent requests.

See [Environment Variables](https://www.mobilebuildmcp.com/docs/env-vars#mcp-idle-shutdown) for the full reference.

See [MCP Protocol Support](https://www.mobilebuildmcp.com/docs/mcp-protocol-support) for the full list of MCP features MobileBuildMCP implements.
