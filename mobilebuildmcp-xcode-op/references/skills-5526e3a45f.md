Source: [https://www.mobilebuildmcp.com/docs/skills](<https://www.mobilebuildmcp.com/docs/skills>)

<a id="agent-skills"></a>

# Agent Skills

Prime your agent with MobileBuildMCP's conventions so it stops guessing flag names.

MobileBuildMCP ships with two optional [agent skills](https://agentskills.io/home):

- **MCP Skill**: how to call MCP tools. Optional when you're already using the MCP server, because Claude Code already receives equivalent guidance via server instructions.
- **CLI Skill**: how to navigate the CLI. Recommended when your agent drives the terminal.

<a id="install"></a>

## Install[#](#install)

shell

```
mobilebuildmcp init
```

This auto-detects installed AI clients (Claude Code, Cursor, Codex) and installs the CLI skill into the right directory for each.

<a id="options"></a>

## Options[#](#options)

| Flag | Description |
| --- | --- |
| `--skill cli` | Install the CLI skill (default). |
| `--skill mcp` | Install the MCP skill. |
| `--client claude` | Install to Claude only. Other targets: `cursor`, `codex`. |
| `--dest /path/to/dir` | Install to a custom directory. |
| `--force` | Overwrite an existing skill. |
| `--remove-conflict` | Auto-remove a conflicting variant (MCP vs CLI). |
| `--uninstall` | Remove an installed skill. |
| `--print` | Print skill content to stdout instead of installing. |

Claude Code + MCP skill

When installing `--skill mcp` in auto-detect mode, Claude Code targets are skipped: Claude already receives MCP guidance through server instructions. Pass `--client claude` explicitly to force install.

<a id="unsupported-clients"></a>

## Unsupported clients[#](#unsupported-clients)

For clients without a skills directory, print the skill and pipe it where you need it:

shell

```
mobilebuildmcp init --print --skill mcp > my-mcp-skill.md
```

Then paste it into your client's instructions area, or feed it as system prompt context.

<a id="why-skills"></a>

## Why skills[#](#why-skills)

The skills prime the agent with:

- Tool names and their CLI equivalents
- Session-defaults workflow (`session_set_defaults` first, then minimal calls)
- Build-and-run as the preferred one-shot instead of separate build/install/launch
- Structured next-step hints after each tool call

Agents without the skill still work; they just spend more tokens rediscovering conventions.

<a id="related"></a>

## Related[#](#related)

- [agentskills.io](https://agentskills.io/home)
- The upstream skill sources live in [skills/](https://github.com/getsentry/MobileBuildMCP/tree/main/skills).

[← Previous

Device Code Signing](https://www.mobilebuildmcp.com/docs/device-signing)[Next →

Demos](https://www.mobilebuildmcp.com/docs/demos)
