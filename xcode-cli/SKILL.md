---
name: xcode-cli
description: 
  Xcode IDE interaction skill. Uses the xcode-cli CLI to build, diagnose,
  test, preview, and edit Xcode projects via MCP.
---

## Requirements

Use the installed `xcode-cli` and Apple MCP bridge.  
Run scripts and CLI commands outside sandbox restrictions.  
See [setup and version checks](references/installed-xcode-tools.md#prerequisites).

## Workflow

1. Read [command details](references/installed-xcode-tools.md#commands) before use.
2. Open the project and use the returned workspace ID in each direct call.
3. Build, run, or test with the listed Apple tools. Inspect JSON results for errors.

## Task references

- [Commands and JSON arguments](references/installed-xcode-tools.md#commands)
- [Debug or Release selection](references/installed-xcode-tools.md#debug-or-release)
- [Breakpoint workflow and examples](references/installed-xcode-tools.md#breakpoints)
- [Stop, kill, and zombie-parent workflow](references/installed-xcode-tools.md#kill-an-app); [kill script](scripts/kill-app.sh)
- [Diagnostics, limits, and recovery](references/installed-xcode-tools.md#notes)
- [Cursor setup](references/cursor-xcode.md)
- [Separate third-party MCP server](references/mcpservers-xcode-mcp.md); use only for that server.
