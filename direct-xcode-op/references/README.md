# xcode-build-skill

An agent plugin that teaches your agent to build and manage iOS/macOS projects using native Xcode CLI tools (`xcodebuild`, `xcrun simctl`).

## Installation

### Option 1: Install from skills.sh (Recommended)

npx skills add pzep1/xcode-build-skill

## What It Does

This plugin provides agents with comprehensive guidance for:

- **Building iOS/macOS apps** with `xcodebuild`
- **Managing simulators** with `xcrun simctl` (boot, install, launch, logs)
- **Taking screenshots** and recording video
- **UI automation** via XCUITest framework (tap, type, gestures, element queries)


## Usage

Once installed, the skill auto-activates when you ask the agent about:

- Building iOS/macOS apps
- Running simulators
- Managing Xcode projects
- UI testing and automation

**Example prompts:**
- "Build the app for iPhone simulator"
- "List available simulators"
- "Take a screenshot of the running app"
- "How do I tap a button in a UI test?"

## Plugin Structure

```
xcode-build-skill/
├── skills/
│   └── xcode-build/
│       ├── SKILL.md          # Main skill definition
│       └── references/
│           ├── CLI_REFERENCE.md  # CLI examples
│           ├── XCUITEST_GUIDE.md # UI test guidance
│           ├── examples.md       # Build and run workflow
│           └── README.md         # Package overview
```

## Command Examples

Read [CLI_REFERENCE.md](CLI_REFERENCE.md) for commands, [examples.md](examples.md) for a build and run workflow, and [XCUITEST_GUIDE.md](XCUITEST_GUIDE.md) for UI tests. Replace example values with discovered project values before execution.

## Requirements

- macOS with Xcode installed
- agentic harness
- `jq` for the provided JSON parsing examples; optional for other commands

## License

MIT License; see the package LICENSE file

## Contributing

Contributions welcome! Please feel free to submit issues and pull requests.

---
