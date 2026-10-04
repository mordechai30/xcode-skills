# Workflows

Source: https://www.mobilebuildmcp.com/docs/workflows

The catalog of tool groups MobileBuildMCP exposes through MCP, and what each one contains.

## What workflows are

A workflow is a named group of related tools (`simulator`, `debugging`, `ui-automation`, etc.). Workflows exist to control which tools the MCP server advertises in `tools/list`. Every advertised tool consumes context tokens in your agent, so picking only the workflows you need keeps the tool catalog lean.

By default only the `simulator` workflow is enabled. To enable more (or define your own), see [MCP Server Mode → Workflow selection](https://www.mobilebuildmcp.com/docs/mcp-mode#workflow-selection) for the full configuration surface, including custom workflows and experimental runtime discovery.

The CLI is different

The CLI does not gate by enabled workflows. Every workflow's commands are always available as `mobilebuildmcp <workflow> <tool>`. The CLI does not pay an upfront context cost because agents and humans discover commands progressively via `--help`; `enabledWorkflows` only affects what the MCP server advertises.

## Available workflows

This list is generated live from the latest [getsentry/MobileBuildMCP](https://github.com/getsentry/MobileBuildMCP) release.

| Workflow | Recommended for | Tools | Description |
| --- | --- | --- | --- |
| coverage | iOS macOS tvOS watchOS visionOS | 2 | View code coverage data from xcresult bundles produced by test runs. |
| debugging | iOS tvOS watchOS visionOS | 8 | Attach LLDB debugger to simulator apps, set breakpoints, inspect variables and call stacks. |
| device | iOS tvOS watchOS visionOS | 15 | Complete development workflow for physical devices (iPhone, iPad, Apple Watch, Apple TV, Apple Vision Pro). |
| doctor | not platform-specific | 1 | Diagnostic tool providing comprehensive information about the MCP server environment, dependencies, and configuration. |
| macos | macOS | 13 | Complete macOS development workflow for both .xcodeproj and .xcworkspace files. Build, test, deploy, and manage macOS applications. |
| project-discovery | iOS macOS tvOS watchOS visionOS | 5 | Discover and examine Xcode projects, workspaces, and Swift packages. Analyze project structure, schemes, build settings, and bundle information. |
| project-scaffolding | iOS macOS | 2 | Scaffold new iOS and macOS projects from templates. |
| session-management default | not platform-specific | 5 | Manage session defaults for project/workspace paths, scheme, configuration, simulator/device settings. |
| simulator default | iOS tvOS watchOS visionOS | 20 | Complete iOS development workflow for both .xcodeproj and .xcworkspace files targeting simulators. |
| simulator-management | iOS tvOS watchOS visionOS | 10 | Tools for managing simulators from booting, opening simulators, listing simulators, stopping simulators, erasing simulator content and settings, and setting simulator environment options like location, network, statusbar and appearance. |
| swift-package | iOS macOS tvOS watchOS visionOS | 8 | Build, test, run and manage Swift Package Manager projects. |
| ui-automation | iOS | 14 | UI automation and accessibility testing tools for iOS simulators. Perform gestures, interactions, screenshots, and UI analysis for automated testing workflows. |
| utilities | iOS macOS tvOS watchOS visionOS | 1 | Utility tools for cleaning build products and managing build artifacts. |
| workflow-discovery | not platform-specific | 1 | Manage enabled workflows at runtime. |
| xcode-ide | iOS macOS tvOS watchOS visionOS | 5 | Bridge tools for connecting to Xcode's built-in MCP server (mcpbridge) to access IDE-specific functionality. |

## Related

*   [MCP Server Mode → Workflow selection](https://www.mobilebuildmcp.com/docs/mcp-mode#workflow-selection): how to enable, customize, and override workflows.
*   [Tools Reference](https://www.mobilebuildmcp.com/docs/tools): every tool by name, with the workflow it belongs to.
*   [Configuration](https://www.mobilebuildmcp.com/docs/configuration): full config schema for `.mobilebuildmcp/config.yaml`.
