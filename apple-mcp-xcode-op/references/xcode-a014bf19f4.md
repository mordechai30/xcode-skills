Source: [https://cursor.com/docs/integrations/xcode](<https://cursor.com/docs/integrations/xcode>)

<a id="xcode"></a>

# Xcode

Xcode 26.3+ exposes a built-in [MCP](https://cursor.com/docs/mcp.md) server that gives Cursor direct access to your Xcode projects. Cursor's agent can read and edit files, trigger builds, run tests, capture SwiftUI previews, and search Apple's documentation; all without leaving your editor.

This works through `xcrun mcpbridge`, a binary Apple ships with Xcode that translates MCP protocol messages into Xcode's internal XPC layer. You configure it once, and Cursor treats Xcode's 20 built-in tools like any other MCP server.

<a id="prerequisites"></a>

## Prerequisites

- macOS with Xcode 26.3 or later installed
- A paid [Cursor plan](https://cursor.com/docs/models-and-pricing.md)
- An Xcode project open in Xcode (Xcode must be running)

<a id="enable-mcp-in-xcode"></a>

### Enable MCP in Xcode

Before Cursor can connect, turn on Xcode's MCP bridge:

<a id="open-xcode-settings"></a>

### Open Xcode settings

Go to **Xcode > Settings > Intelligence**.

<a id="enable-mcp"></a>

### Enable MCP

Under **Model Context Protocol**, toggle **Xcode Tools** on.

<a id="set-up-cursor"></a>

## Set up Cursor

Pick whichever method suits your workflow.

<a id="option-1-mcp-settings-ui"></a>

### Option 1: MCP settings UI

<a id="open-mcp-settings"></a>

### Open MCP settings

Go to **Customize** > **MCPs**.

<a id="add-the-server"></a>

### Add the server

Click **Add New MCP Server**. Set the transport to **stdio**, name it `xcode-tools`, and enter `xcrun mcpbridge` as the command.

<a id="option-2-mcpjson"></a>

### Option 2: `mcp.json`

Add an entry to your [MCP config file](https://cursor.com/docs/mcp.md#configuration-locations):

```json title="~/.cursor/mcp.json"
{
  "mcpServers": {
    "xcode-tools": {
      "command": "xcrun",
      "args": ["mcpbridge"]
    }
  }
}
```

<a id="option-3-cursor-cli"></a>

### Option 3: Cursor CLI

If you use the [Cursor CLI](https://cursor.com/docs/cli/overview.md), register the server from your terminal:

```bash
agent mcp add xcode-tools -- xcrun mcpbridge
```

The CLI shares the same MCP config as the editor, so the server appears in both.

<a id="available-tools"></a>

## Available tools

Xcode exposes 20 MCP tools across five categories:

<a id="file-operations"></a>

### File operations

- **XcodeRead** - Read file contents (up to 600 lines per call, with offset/limit for larger files)
- **XcodeWrite** - Create or overwrite files
- **XcodeUpdate** - Apply targeted edits to existing files
- **XcodeGrep** - Search file contents with regex
- **XcodeGlob** - Find files by pattern
- **XcodeLS** - List directory contents
- **XcodeMakeDir** - Create directories
- **XcodeRM** - Remove files or directories
- **XcodeMV** - Move or rename files

<a id="build-and-test"></a>

### Build and test

- **BuildProject** - Build the active scheme
- **GetBuildLog** - Retrieve build logs, filterable by severity, regex, or file glob
- **RunAllTests** - Run the full test suite
- **RunSomeTests** - Run specific test classes or methods
- **GetTestList** - List available tests

<a id="diagnostics"></a>

### Diagnostics

- **XcodeListNavigatorIssues** - Show warnings and errors from the Issue Navigator
- **XcodeRefreshCodeIssuesInFile** - Re-check a file for code issues

<a id="intelligence"></a>

### Intelligence

- **RenderPreview** - Capture a screenshot of a SwiftUI preview
- **DocumentationSearch** - Semantic search across Apple's documentation and WWDC transcripts
- **ExecuteSnippet** - Run a Swift code snippet

<a id="workspace"></a>

### Workspace

- **XcodeListWindows** - List open Xcode windows and tabs

<a id="example-workflow"></a>

## Example workflow

A typical Cursor + Xcode workflow looks like this:

1. Open your project in both Cursor and Xcode
2. Ask Cursor's agent to add a feature or fix a bug
3. The agent uses **XcodeRead** and **XcodeGrep** to understand your code
4. It edits files with **XcodeWrite** or **XcodeUpdate**
5. It runs **BuildProject** to check for errors, reads results with **GetBuildLog**
6. It runs tests with **RunSomeTests** to verify the change
7. It captures a SwiftUI preview with **RenderPreview** to confirm the UI

You stay in Cursor the whole time. Xcode handles compilation, testing, and previews in the background.

<a id="cursor-cli-with-xcode"></a>

## Cursor CLI with Xcode

The [Cursor CLI](https://cursor.com/docs/cli/overview.md) also works with Xcode's MCP tools. This is useful for headless workflows, CI pipelines, or terminal-first developers.

```bash
# Run agent with Xcode tools available
agent "Add unit tests for the NetworkManager class"
```

The agent picks up the `xcode-tools` MCP server from your config and uses the same tools available in the editor.

<a id="troubleshooting"></a>

## Troubleshooting

<a id="cursor-cant-find-the-xcode-tools-server"></a>

### Cursor can't find the xcode-tools server

Make sure Xcode is running with a project open. The `xcrun mcpbridge` process needs an active Xcode session to communicate with.

<a id="tools-show-errors-about-missing-tabidentifier"></a>

### Tools show errors about missing tabIdentifier

Some Xcode MCP tools need a workspace context. Confirm you have a project or workspace open in Xcode, not an empty window.

<a id="build-or-test-tools-time-out"></a>

### Build or test tools time out

Large projects take longer to build. Check Xcode's build progress directly. The MCP bridge waits for Xcode's response, so timeouts usually mean the underlying operation is still running.

<a id="mcp-toggle-missing-in-xcode-settings"></a>

### MCP toggle missing in Xcode settings

You need Xcode 26.3 or later. Check your version under **Xcode > About Xcode** and update through the Mac App Store or [Apple Developer downloads](https://developer.apple.com/download/).

<a id="xcrun-error-unable-to-find-utility-mcpbridge"></a>

### xcrun: error: unable to find utility "mcpbridge"

Your system is pointed at Command Line Tools instead of the full Xcode installation. Fix this by running:

```bash
sudo xcode-select -s /Applications/Xcode.app/Contents/Developer
sudo xcodebuild -runFirstLaunch
```

Then confirm the bridge is available:

```bash
xcrun --find mcpbridge
```

This should return a file path, not an error. Once it does, open Xcode with your project, go to **Settings > Intelligence > Model Context Protocol**, and enable **Allow external agents**. Then toggle the Xcode MCP server back on in Cursor settings. You should see a permission dialog in Xcode confirming the connection.

<a id="related"></a>

## Related

<a id="mcp-overview"></a>

### MCP overview

Complete MCP guide with setup, configuration, and authentication

<a id="ios--macos-swift"></a>

### iOS & macOS (Swift)

Swift development workflow with Cursor, Sweetpad, and Xcode Build Server

<a id="cursor-cli"></a>

### Cursor CLI

Use Cursor's agent from the terminal

<a id="cli-mcp-commands"></a>

### CLI MCP commands

Manage MCP servers from the command line

---



<a id="sitemap"></a>

## Sitemap

[Overview of all docs pages](tionsxcode/1ef7ac26b1eedd0ba5cabac9.md)
