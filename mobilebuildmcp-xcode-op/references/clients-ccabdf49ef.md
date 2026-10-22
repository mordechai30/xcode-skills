Source: [https://www.mobilebuildmcp.com/docs/clients](<https://www.mobilebuildmcp.com/docs/clients>)

<a id="mcp-clients"></a>

# MCP Clients

Drop-in config for every major MCP-speaking editor. Pick yours and paste.

[C

Claude Code

Anthropic CLI](#claude-code)[Cu

Cursor

cursor.sh](#cursor)[Cx

Codex CLI

OpenAI](#codex-cli)[CD

Claude Desktop

Anthropic app](#claude-desktop)[VS

VS Code

Agent mode](#vs-code)[Ki

Kiro

kiro.dev](#kiro)[W

Windsurf

Codeium](#windsurf)[OC

OpenCode

opencode.ai](#opencode)[Tr

Trae

trae.ai](#trae)[Xc

Xcode (Codex)

In-IDE agent](#xcode-codex-agent)[Xc

Xcode (Claude)

In-IDE agent](#xcode-claude-code-agent)[A

AdaL CLI

adal.dev](#adal-cli)

All examples below use the npx command. If you installed via Homebrew, replace `command` with `"mobilebuildmcp"` and `args` with `["mcp"]` to skip the npx download check on startup.

<a id="claude-code"></a>

## Claude Code[#](#claude-code)

bash

```
claude mcp add MobileBuildMCP -- npx -y mobilebuildmcp@latest mcp
```

Or with env-based session defaults:

bash

```
claude mcp add MobileBuildMCP -e MOBILEBUILDMCP_SENTRY_DISABLED=false -- npx -y mobilebuildmcp@latest mcp
```

<a id="cursor"></a>

## Cursor[#](#cursor)

Project-scoped (recommended): create `.cursor/mcp.json` in your workspace root:

json

```
{
  "mcpServers": {
    "MobileBuildMCP": {
      "command": "npx",
      "args": ["-y", "mobilebuildmcp@latest", "mcp"]
    }
  }
}
```

For global Cursor config at `~/.cursor/mcp.json`, set `MOBILEBUILDMCP_CWD` so startup runs from the active workspace:

json

```
{
  "mcpServers": {
    "MobileBuildMCP": {
      "command": "npx",
      "args": ["-y", "mobilebuildmcp@latest", "mcp"],
      "env": {
        "MOBILEBUILDMCP_CWD": "${workspaceFolder}"
      }
    }
  }
}
```

<a id="codex-cli"></a>

## Codex CLI[#](#codex-cli)

Run inside your terminal:

bash

```
codex mcp add MobileBuildMCP -- npx -y mobilebuildmcp@latest mcp
```

Or edit `~/.codex/config.toml`:

toml

```
[mcp_servers.MobileBuildMCP]
command = "npx"
args = ["-y", "mobilebuildmcp@latest", "mcp"]
```

If you hit `timed out awaiting tools/call after 60s`, `timed out awaiting tools/call after 120s`, or similar, set the timeout in the same server block:

toml

```
[mcp_servers.MobileBuildMCP]
command = "npx"
args = ["-y", "mobilebuildmcp@latest", "mcp"]
tool_timeout_sec = 600
```

Codex ignores a top-level `tool_timeout_sec` for MCP tool calls.

<a id="claude-desktop"></a>

## Claude Desktop[#](#claude-desktop)

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

json

```
{
  "mcpServers": {
    "MobileBuildMCP": {
      "command": "npx",
      "args": ["-y", "mobilebuildmcp@latest", "mcp"]
    }
  }
}
```

<a id="vs-code"></a>

## VS Code[#](#vs-code)

Add to your VS Code settings JSON:

json

```
{
  "mcp": {
    "servers": {
      "MobileBuildMCP": {
        "command": "npx",
        "args": ["-y", "mobilebuildmcp@latest", "mcp"]
      }
    }
  }
}
```

<a id="kiro"></a>

## Kiro[#](#kiro)

Workspace-scoped at `.kiro/settings/mcp.json`, or user-scoped at `~/.kiro/settings/mcp.json`:

json

```
{
  "mcpServers": {
    "MobileBuildMCP": {
      "command": "npx",
      "args": ["-y", "mobilebuildmcp@latest", "mcp"]
    }
  }
}
```

<a id="windsurf"></a>

## Windsurf[#](#windsurf)

Add to `~/.codeium/windsurf/mcp_config.json`:

json

```
{
  "mcpServers": {
    "MobileBuildMCP": {
      "command": "npx",
      "args": ["-y", "mobilebuildmcp@latest", "mcp"]
    }
  }
}
```

<a id="opencode"></a>

## OpenCode[#](#opencode)

Add to your `opencode.json`:

json

```
{
  "$schema": "https://opencode.ai/config.json",
  "mcp": {
    "MobileBuildMCP": {
      "type": "local",
      "command": ["npx", "-y", "mobilebuildmcp@latest", "mcp"]
    }
  }
}
```

OpenCode loads config from multiple locations with a clear precedence order. A project-level `opencode.json` in your repo overrides the global one at `~/.config/opencode/opencode.json`, which in turn overrides remote organizational defaults. Settings from all layers are merged, not replaced. See [openCode docs → Config Precedence](https://opencode.ai/docs/config/#precedence-order) for the full order.

<a id="trae"></a>

## Trae[#](#trae)

Add to `~/Library/Application Support/Trae/User/mcp.json`:

json

```
{
  "mcpServers": {
    "MobileBuildMCP": {
      "command": "npx",
      "args": ["-y", "mobilebuildmcp@latest", "mcp"]
    }
  }
}
```

<a id="xcode-codex-agent"></a>

## Xcode (Codex Agent)[#](#xcode-codex-agent)

Requires **Xcode 26.3 or later** with the Codex agent installed under *Xcode Settings → Intelligence → Open AI*. At the time of writing, Xcode's Codex agent only supports a project-scoped `.codex/config.toml` at your project workspace root:

toml

```
[mcp_servers.MobileBuildMCP]
args = [
  "-lc",
  "PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin; export NVM_DIR=\"$HOME/.nvm\"; [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\"; nvm use --silent >/dev/null 2>&1 || true; npx -y mobilebuildmcp@latest mcp"
]
command = "/bin/zsh"
enabled = true
tool_timeout_sec = 10000
```

Limited PATH

Codex Agent inside Xcode starts with a minimal `PATH`. If the server won't start, it's usually because `npx` can't be found. The zsh wrapper above handles Homebrew and nvm; adjust to match your toolchain.

<a id="xcode-claude-code-agent"></a>

## Xcode (Claude Code Agent)[#](#xcode-claude-code-agent)

Requires **Xcode 26.3 or later** with the Claude Code agent installed under *Xcode Settings → Intelligence → Anthropic*. Edit the config at:

path

```
~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json
```

Add or replace the `mcpServers` block:

json

```
{
  "mcpServers": {
    "MobileBuildMCP": {
      "command": "/bin/zsh",
      "args": [
        "-lc",
        "PATH=/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin:/usr/sbin:/sbin; export NVM_DIR=\"$HOME/.nvm\"; [ -s \"$NVM_DIR/nvm.sh\" ] && . \"$NVM_DIR/nvm.sh\"; nvm use --silent >/dev/null 2>&1 || true; npx -y mobilebuildmcp@latest mcp"
      ]
    }
  }
}
```

<a id="adal-cli"></a>

## AdaL CLI[#](#adal-cli)

At the AdaL prompt:

console

```
/mcp add MobileBuildMCP --command npx --args "-y,mobilebuildmcp@latest,mcp"
```

<a id="verifying-the-connection"></a>

## Verifying the connection[#](#verifying-the-connection)

Once configured, ask your agent to list tools. With the default `simulator` workflow enabled you should see the simulator toolset. Expand `enabledWorkflows` in your [configuration](https://www.mobilebuildmcp.com/docs/configuration) to surface more, or browse every tool in the [Tools Reference](https://www.mobilebuildmcp.com/docs/tools).

[← Previous

Setup](https://www.mobilebuildmcp.com/docs/setup)[Next →

CLI](https://www.mobilebuildmcp.com/docs/cli)
