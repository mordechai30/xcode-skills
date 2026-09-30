# MCP Clients

Source: https://www.mobilebuildmcp.com/docs/clients

Drop-in config for every major MCP-speaking editor. Pick yours and paste.

- [C Claude Code Anthropic CLI](https://www.mobilebuildmcp.com/docs/clients#claude-code)
- [Cu Cursor cursor.sh](https://www.mobilebuildmcp.com/docs/clients#cursor)
- [Cx Codex CLI OpenAI](https://www.mobilebuildmcp.com/docs/clients#codex-cli)
- [CD Claude Desktop Anthropic app](https://www.mobilebuildmcp.com/docs/clients#claude-desktop)
- [VS VS Code Agent mode](https://www.mobilebuildmcp.com/docs/clients#vs-code)
- [Ki Kiro kiro.dev](https://www.mobilebuildmcp.com/docs/clients#kiro)
- [W Windsurf Codeium](https://www.mobilebuildmcp.com/docs/clients#windsurf)
- [OC OpenCode opencode.ai](https://www.mobilebuildmcp.com/docs/clients#opencode)
- [Tr Trae trae.ai](https://www.mobilebuildmcp.com/docs/clients#trae)
- [Xc Xcode (Codex) In-IDE agent](https://www.mobilebuildmcp.com/docs/clients#xcode-codex-agent)
- [Xc Xcode (Claude) In-IDE agent](https://www.mobilebuildmcp.com/docs/clients#xcode-claude-code-agent)
- [A AdaL CLI adal.dev](https://www.mobilebuildmcp.com/docs/clients#adal-cli)

All examples below use the npx command. If you installed via Homebrew, replace `command` with `"mobilebuildmcp"` and `args` with `["mcp"]` to skip the npx download check on startup.

## Claude Code

`claude mcp add MobileBuildMCP -- npx -y mobilebuildmcp@latest mcp`

Or with env-based session defaults:

`claude mcp add MobileBuildMCP -e MOBILEBUILDMCP_SENTRY_DISABLED=false -- npx -y mobilebuildmcp@latest mcp`

## Cursor

Project-scoped (recommended): create `.cursor/mcp.json` in your workspace root:

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

## Codex CLI

Run inside your terminal:

`codex mcp add MobileBuildMCP -- npx -y mobilebuildmcp@latest mcp`

Or edit `~/.codex/config.toml`:

```
[mcp_servers.MobileBuildMCP]
command = "npx"
args = ["-y", "mobilebuildmcp@latest", "mcp"]
```

If you hit `timed out awaiting tools/call after 60s`, `timed out awaiting tools/call after 120s`, or similar, set the timeout in the same server block:

```
[mcp_servers.MobileBuildMCP]
command = "npx"
args = ["-y", "mobilebuildmcp@latest", "mcp"]
tool_timeout_sec = 600
```

Codex ignores a top-level `tool_timeout_sec` for MCP tool calls.

## Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:

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

## VS Code

Add to your VS Code settings JSON:

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

## Kiro

Workspace-scoped at `.kiro/settings/mcp.json`, or user-scoped at `~/.kiro/settings/mcp.json`:

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

## Windsurf

Add to `~/.codeium/windsurf/mcp_config.json`:

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

## OpenCode

Add to your `opencode.json`:

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

## Trae

Add to `~/Library/Application Support/Trae/User/mcp.json`:

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

## Xcode (Codex Agent)

Requires **Xcode 26.3 or later** with the Codex agent installed under _Xcode Settings → Intelligence → Open AI_. At the time of writing, Xcode's Codex agent only supports a project-scoped `.codex/config.toml` at your project workspace root:

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

## Xcode (Claude Code Agent)

Requires **Xcode 26.3 or later** with the Claude Code agent installed under _Xcode Settings → Intelligence → Anthropic_. Edit the config at:

path Copy

`~/Library/Developer/Xcode/CodingAssistant/ClaudeAgentConfig/.claude.json`

Add or replace the `mcpServers` block:

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

## AdaL CLI

At the AdaL prompt:

console Copy

`/mcp add MobileBuildMCP --command npx --args "-y,mobilebuildmcp@latest,mcp"`

## Verifying the connection

Once configured, ask your agent to list tools. With the default `simulator` workflow enabled you should see the simulator toolset. Expand `enabledWorkflows` in your [configuration](https://www.mobilebuildmcp.com/docs/configuration) to surface more, or browse every tool in the [Tools Reference](https://www.mobilebuildmcp.com/docs/tools).
