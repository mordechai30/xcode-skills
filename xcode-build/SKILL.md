---
name: xcode-build
description: Build, run, and test Xcode iOS, macOS with native CLI tools. Use for simulator and device targets, app logs, screenshots, and XCUITest automation.
---

# Xcode Build

All scripts (Python, Bash) and CLI commands must be run outside sandbox restrictions.  
Use `xcodebuild` and `xcrun simctl` for native build and simulator tasks. Respect an explicit user choice of another tool.

## Read the relevant reference

Resolve these paths relative to this skill folder. Read the relevant section before executing its commands. Do not load all references for each task.

- For builds, simulator commands, logs, screenshots, archives, or test execution, read [CLI_REFERENCE.md](references/CLI_REFERENCE.md).
- For standalone Clean, Debug/Release selection, stopping macOS apps, or LLDB breakpoints, read the matching sections in [CLI_REFERENCE.md](references/CLI_REFERENCE.md).
- For a build, install, and launch workflow, read [examples.md](references/examples.md). It includes prerequisite checks and app selection.
- Before writing or running UI interactions, read the Setup and relevant action sections in [XCUITEST_GUIDE.md](references/XCUITEST_GUIDE.md).
- For installation or package requirements only, read [README.md](references/README.md).

## Before execution

- Check macOS, the active full Xcode installation, and required SDKs. Stop and report a missing prerequisite; do not install tools or runtimes without authorization.
- Discover the actual project or workspace, scheme, and destinations. Replace example values with verified values. Do not assume a test target has a scheme with the same name.
- Use a destination reported by `-showdestinations`; do not assume its architecture. For simulator builds only, select one available compatible simulator and validate its UDID. Skip simulator commands for macOS builds.
- Check installed command help when a flag or service is uncertain. Installed tool behavior takes precedence over these examples.

## Execute and verify

- Use one explicit derived-data path for the build. Project settings can place products elsewhere; read `TARGET_BUILD_DIR` and `FULL_PRODUCT_NAME` to locate the app target's product. Read its bundle identifier from its Info.plist; do not select the first `.app` found.
- Before simulator installation or launch, boot the selected device if needed and wait for `simctl bootstatus`. Do not hide boot errors or use a fixed delay.
- Run Swift UI examples inside a configured XCTest UI test target. Use a discovered scheme with that target in its Test action.
- Keep session values explicit. Shell variables can be lost between tool calls; pass them again when needed.
- Check each command's result before continuing. After a failure, diagnose the cause before retrying. Report the destination, app or test result, and any incomplete verification.
