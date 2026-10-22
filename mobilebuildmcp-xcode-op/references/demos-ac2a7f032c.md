Source: [https://www.mobilebuildmcp.com/docs/demos](<https://www.mobilebuildmcp.com/docs/demos>)

<a id="demos"></a>

# Demos

Short clips of MobileBuildMCP in action, handling build errors, automating UI, and running full build-and-launch cycles from inside an MCP client.

<a id="autonomously-fixing-build-errors-in-cursor"></a>

## Autonomously fixing build errors in Cursor[#](#autonomously-fixing-build-errors-in-cursor)

An agent runs a build, reads the structured diagnostics, makes edits, rebuilds, and repeats until the project compiles, without human intervention.

![Cursor agent iterating on build errors until the project compiles](<mdocsdemos/68ce5fe81b6b2e77028f85f0.gif>)


<a id="ui-automation-and-screen-capture"></a>

## UI automation and screen capture[#](#ui-automation-and-screen-capture)

Tap, swipe, type, and capture screenshots from inside an agent session. `snapshot_ui` returns semantic element refs, labels, identifiers, roles, and frames so the agent can target UI elements without guessing pixel positions.

![UI automation driving a simulator with taps, swipes, and screenshot capture](<mdocsdemos/9d2133d36cd116f2726f9cfb.gif>)


<a id="building-and-running-ios-apps-in-claude-desktop"></a>

## Building and running iOS apps in Claude Desktop[#](#building-and-running-ios-apps-in-claude-desktop)

A single `build_run_sim` call compiles the scheme, boots the simulator, installs the app, launches it, and starts streaming logs, all in one structured tool invocation.

[](https://github.com/user-attachments/assets/e3c08d75-8be6-4857-b4d0-9350b26ef086)


<a id="related"></a>

## Related[#](#related)

- [Introduction](https://www.mobilebuildmcp.com/docs), what MobileBuildMCP is for
- [Setup](https://www.mobilebuildmcp.com/docs/setup), get your own agent running in 5 minutes
- [Tools Reference](https://www.mobilebuildmcp.com/docs/tools), every tool the agent has access to

[← Previous

Agent Skills](https://www.mobilebuildmcp.com/docs/skills)[Next →

Migration from v1](https://www.mobilebuildmcp.com/docs/migration-v2)
