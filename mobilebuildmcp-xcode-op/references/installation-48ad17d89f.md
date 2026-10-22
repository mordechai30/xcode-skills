Source: [https://www.mobilebuildmcp.com/docs/installation](<https://www.mobilebuildmcp.com/docs/installation>)

<a id="installation"></a>

# Installation

Install MobileBuildMCP via Homebrew or npm. Both give you the CLI and the MCP server. Once installed, head to Setup to wire it into your editor.

Requires macOS 14.5+Xcode 16.x+Node.js 18+ (npm only)

<a id="requirements"></a>

## Requirements[#](#requirements)

- macOS 14.5 Sonoma or later
- Xcode 16.x or later (Xcode 26+ unlocks the [Xcode IDE Bridge](https://www.mobilebuildmcp.com/docs/xcode-ide))
- Node.js 18+ if using the npm install path
- Homebrew if using the Homebrew install path

<a id="option-a-homebrew-recommended-no-nodejs"></a>

## Option A: Homebrew (recommended, no Node.js)[#](#option-a-homebrew-recommended-no-nodejs)

shell

```
brew tap getsentry/xcodebuildmcp
brew install mobilebuildmcp
```

<a id="option-b-npm--npx"></a>

## Option B: npm / npx[#](#option-b-npm--npx)

For CLI use, install globally:

shell

```
npm install -g mobilebuildmcp@latest
mobilebuildmcp --help
```

For MCP-server-only use, no global install needed, just reference `npx` in your MCP client config (covered in [Setup](https://www.mobilebuildmcp.com/docs/setup)).

Pin a specific version by replacing `@latest` with a tag, for example `@2.3.2`.

<a id="keeping-it-up-to-date"></a>

## Keeping it up to date[#](#keeping-it-up-to-date)

Once installed, run the built-in self-update command:

shell

```
mobilebuildmcp upgrade
```

It checks for a newer version and installs it in place using whichever package manager you installed with. See [CLI → Keeping the CLI up to date](https://www.mobilebuildmcp.com/docs/cli#keeping-the-cli-up-to-date) for available flags.

<a id="verify"></a>

## Verify[#](#verify)

Run the doctor to check your environment:

shell

```
npx --package mobilebuildmcp@latest mobilebuildmcp-doctor
```

Or, if you installed globally:

shell

```
mobilebuildmcp-doctor
```

The doctor reports on Node/Xcode versions, required dependencies, environment variables, and feature availability. Always include its output when filing an issue.

<a id="uninstall"></a>

## Uninstall[#](#uninstall)

shell

```
# Homebrew
brew uninstall mobilebuildmcp

# npm
npm uninstall -g mobilebuildmcp
```

<a id="next-step"></a>

## Next step[#](#next-step)

With MobileBuildMCP installed, head to [Setup](https://www.mobilebuildmcp.com/docs/setup) to wire it into your editor, run the project config wizard, and do your first build.

[← Previous

Introduction](https://www.mobilebuildmcp.com/docs/introduction)[Next →

Setup](https://www.mobilebuildmcp.com/docs/setup)
