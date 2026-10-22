Source: [https://www.mobilebuildmcp.com/docs/xcode-ide](<https://www.mobilebuildmcp.com/docs/xcode-ide>)

<a id="xcode-ide-bridge"></a>

# Xcode IDE Bridge

Proxy Xcode 26's built-in MCP service through MobileBuildMCP to reach IDE-only tools like Preview rendering, Issue Navigator queries, and documentation search.

MobileBuildMCP can optionally proxy Xcode's built-in MCP service via Xcode 26's `xcrun mcpbridge`. This exposes IDE-only tools that are not available via `xcodebuild`:

- Preview rendering
- Issue Navigator queries
- Documentation search
- Project Navigator operations
- And more, depending on your Xcode version

<a id="requirements"></a>

## Requirements[#](#requirements)

- Xcode 26.3 or later
- `mcpbridge` available at `xcrun mcpbridge` (shipped with Xcode)
- MobileBuildMCP with the `xcode-ide` workflow enabled

<a id="enable"></a>

## Enable[#](#enable)

Add `xcode-ide` to `enabledWorkflows` in `.mobilebuildmcp/config.yaml`:

yaml

```
schemaVersion: 1
enabledWorkflows: ["simulator", "debugging", "xcode-ide"]
```

If the workflow isn't enabled, MobileBuildMCP doesn't start the bridge.

<a id="tools-exposed"></a>

## Tools exposed[#](#tools-exposed)

When `xcode-ide` is enabled and `mcpbridge` is available, MobileBuildMCP exposes two gateway tools to MCP clients:

| Tool | Purpose |
| --- | --- |
| `xcode_ide_list_tools` | List the tools Xcode's MCP server advertises, with names, descriptions, and JSON schemas. |
| `xcode_ide_call_tool` | Call a remote Xcode tool by name with a JSON argument payload. |

These two tools are stable and always present when the workflow is enabled. The actual tool catalog they proxy depends on your Xcode version, expect the set to grow as Xcode ships new IDE-facing tools.

In CLI mode, proxied Xcode tools are exposed under dynamic `xcode_tools_*` names instead of the two gateway tools above.

<a id="trust-prompts"></a>

## Trust prompts[#](#trust-prompts)

Xcode may show trust/allow prompts when the bridge connects and/or when tools are invoked. Recommended flow:

1. Launch Xcode.
2. Start MobileBuildMCP with `xcode-ide` enabled.
3. If `xcode_ide_list_tools` fails, enable `debug: true` in your config and call `xcode_tools_bridge_status` to inspect the bridge state; retry after approving prompts.

<a id="debug-tools"></a>

## Debug tools[#](#debug-tools)

The following are hidden unless you set `debug: true`, because they're primarily for troubleshooting:

- `xcode_tools_bridge_status`, bridge availability, connection state, last error, proxied tool count.
- `xcode_tools_bridge_sync`, one-shot connect + re-sync (use this if Xcode's startup sync was blocked).
- `xcode_tools_bridge_disconnect`, disconnect and unregister the proxied tools.

<a id="targeting-a-specific-xcode"></a>

## Targeting a specific Xcode[#](#targeting-a-specific-xcode)

If you have multiple Xcodes installed and need to scope the bridge to a specific one, set these env vars. MobileBuildMCP forwards them to the bridge:

| Env var | Forwards as |
| --- | --- |
| `MOBILEBUILDMCP_XCODE_PID` | `MCP_XCODE_PID` |
| `MOBILEBUILDMCP_XCODE_SESSION_ID` | `MCP_XCODE_SESSION_ID` |

<a id="related"></a>

## Related[#](#related)

- [Configuration](https://www.mobilebuildmcp.com/docs/configuration)
- [Workflows](https://www.mobilebuildmcp.com/docs/workflows)

[← Previous

Environment Variables](https://www.mobilebuildmcp.com/docs/env-vars)[Next →

Device Code Signing](https://www.mobilebuildmcp.com/docs/device-signing)
