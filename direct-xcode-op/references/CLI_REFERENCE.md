# Xcode CLI Reference

Task examples for `xcodebuild` and `xcrun simctl`.

## Preconditions and discovery

Examples are templates. Replace paths, schemes, bundle identifiers, device names, and UDIDs with discovered values. Set `UDID` in the same shell before commands that use it. Check `xcode-select -p`, `xcodebuild -version`, and `xcodebuild -showsdks`. The active developer directory must provide full Xcode and the required SDK. Check `command -v jq` before JSON pipelines.

Use `xcodebuild -list` and `-showdestinations` for the chosen project or workspace. For simulator builds only, select an available simulator compatible with the scheme. For macOS, use a reported Mac destination and skip `simctl` commands. Do not assume an architecture. The device names and OS versions below are examples, not requirements. Use `xcrun simctl help <command>` and `xcodebuild -help` to check installed syntax.

For an integrated workflow, read [examples.md](examples.md). For UI test setup and actions, read [XCUITEST_GUIDE.md](XCUITEST_GUIDE.md).

Sections: Project Discovery; Building; Testing; Simulator Lifecycle; App Management; Screenshots and Video; Location; Privacy Permissions; Logging; Finding Built App Path.

## xcodebuild Commands

### Project Discovery

```bash
# List all schemes in workspace
xcodebuild -workspace /path/to/App.xcworkspace -list

# List all schemes in project
xcodebuild -project /path/to/App.xcodeproj -list

# Show available SDKs
xcodebuild -showsdks

# Show available destinations for a scheme
xcodebuild -workspace /path/to/App.xcworkspace -scheme SchemeName -showdestinations

# Show all build settings
xcodebuild -workspace /path/to/App.xcworkspace -scheme SchemeName -showBuildSettings

# Get specific build setting
xcodebuild -workspace /path/to/App.xcworkspace -scheme SchemeName \
  -showBuildSettings | grep PRODUCT_BUNDLE_IDENTIFIER
```

### Building for iOS Simulator

```bash
# Basic build
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,name=iPhone 16 Pro" \
  build

# Build with specific simulator UUID
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,id=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX" \
  -configuration Debug \
  build

# Build with custom derived data path (recommended)
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,id=$UDID" \
  -derivedDataPath /tmp/build \
  build

# Clean build
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,id=$UDID" \
  clean build

# Build with specific iOS version
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,name=iPhone 16 Pro,OS=18.0" \
  build
```

### Building for Device

```bash
# Build for generic iOS device with signing disabled
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "generic/platform=iOS" \
  -configuration Release \
  CODE_SIGNING_ALLOWED=NO \
  build

# Build for connected device
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS,id=DEVICE_UDID" \
  build
```

### Building for macOS

Use a destination reported by `-showdestinations`. If several match, specify the selected Mac ID.

```bash
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme MacScheme \
  -destination "platform=macOS" \
  build
```

### Clean and build configuration

Use the same project, scheme, destination, and derived-data path as the build. Discover supported configurations with `-list`. Set `CONFIGURATION=Debug` or `CONFIGURATION=Release` explicitly. Clean removes build outputs; it is a separate action and does not rebuild.

```bash
PROJECT='/path/to/App.xcodeproj'
SCHEME='App'
DESTINATION='platform=macOS,id=VERIFIED_MAC_ID'
DERIVED_DATA='/tmp/app-build'
CONFIGURATION=Debug  # Or Release, if listed by this project.
xcodebuild -project "$PROJECT" -scheme "$SCHEME" \
  -destination "$DESTINATION" -derivedDataPath "$DERIVED_DATA" \
  -configuration "$CONFIGURATION" clean
# Use build instead of clean to compile the selected configuration.
xcodebuild -project "$PROJECT" -scheme "$SCHEME" \
  -destination "$DESTINATION" -derivedDataPath "$DERIVED_DATA" \
  -configuration "$CONFIGURATION" build
```

### Stop a macOS app

Identify the exact app PID and verify its command before sending signals. Send TERM first. If the same live process remains after a short wait, recheck its identity and send KILL. Avoid broad name-based kills.

```bash
ps -p "$PID" -o pid=,ppid=,stat=,command=
kill -TERM "$PID"
# After a short wait, recheck identity and state before escalation.
ps -p "$PID" -o pid=,ppid=,stat=,command=
kill -KILL "$PID"  # Only for the verified process still alive.
```

A `Z` state is a zombie: the process has exited and cannot receive signals. Its parent must reap it. Inspect the PPID and parent command with `ps`; stop the parent only if it is a disposable app-owned helper or test launcher and its termination is authorized. Never kill PID 1 or a system service. If the parent is unrelated or its role is unclear, report it and ask before terminating it.

```bash
ps -p "$PID" -o pid=,ppid=,stat=,command=
APP_PARENT_PID=$(ps -p "$PID" -o ppid= | tr -d '[:space:]')
# Stop if the app is gone or its parent is PID 1.
[ -n "$APP_PARENT_PID" ] && [ "$APP_PARENT_PID" -gt 1 ] || exit 1
ps -p "$APP_PARENT_PID" -o pid=,ppid=,stat=,command=
# Recheck the app's parent and its identity before termination.
[ "$(ps -p "$PID" -o ppid= | tr -d '[:space:]')" = "$APP_PARENT_PID" ] || exit 1
kill -TERM "$APP_PARENT_PID"  # Only the verified, authorized disposable parent.
```

Do not use shell `$PPID`: it identifies the shell's parent, not the app's parent.

For simulator apps, use the existing `simctl terminate` example; do not apply host parent termination without identifying the simulator process and its owner.

### Set an LLDB breakpoint

Use the app path resolved from build settings. Use a Debug build for source breakpoints.

```bash
APP_PATH='/verified/path/App.app'
EXECUTABLE_NAME=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleExecutable' "$APP_PATH/Contents/Info.plist") || exit 1
[ -n "$EXECUTABLE_NAME" ] || exit 1
EXECUTABLE="$APP_PATH/Contents/MacOS/$EXECUTABLE_NAME"
[ -x "$EXECUTABLE" ] || exit 1
xcrun lldb "$EXECUTABLE"
```

Then issue these LLDB commands. Replace `AppExecutable` with the value of `EXECUTABLE_NAME` to avoid matches in system frameworks:

```text
breakpoint set --name main --shlib AppExecutable
breakpoint list
run
thread backtrace
process kill
quit
```

For a source breakpoint, use `breakpoint set --file /absolute/path/File.cpp --line 42` with a verified executable source line. Check that the breakpoint has resolved locations and execution stops there. LLDB breakpoints apply to that debugger session; they do not create Xcode breakpoint files. Release optimization can remove or move source locations. If macOS denies debugger launch or attach, report the error without changing security settings.

### Archives and Distribution

Unsigned device builds are compile checks. Installation and distribution require suitable signing. Use the project signing settings and an export options plist for the intended distribution method.

```bash
# Create archive
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "generic/platform=iOS" \
  -archivePath /tmp/App.xcarchive \
  archive

# Export IPA from archive
xcodebuild \
  -exportArchive \
  -archivePath /tmp/App.xcarchive \
  -exportPath /tmp/export \
  -exportOptionsPlist /path/to/ExportOptions.plist
```

### Testing

```bash
# Run all tests
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,id=$UDID" \
  test

# Run specific test class
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,id=$UDID" \
  -only-testing "AppTests/UserServiceTests" \
  test

# Run specific test method
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,id=$UDID" \
  -only-testing "AppTests/UserServiceTests/testLoginSuccess" \
  test

# Skip specific tests
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,id=$UDID" \
  -skip-testing "AppTests/SlowTests" \
  test

# Test with code coverage
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,id=$UDID" \
  -enableCodeCoverage YES \
  test

# Save test results
xcodebuild \
  -workspace /path/to/App.xcworkspace \
  -scheme SchemeName \
  -destination "platform=iOS Simulator,id=$UDID" \
  -resultBundlePath /tmp/TestResults.xcresult \
  test
```

### Useful Flags

| Flag | Description |
|------|-------------|
| `-workspace <path>` | Path to .xcworkspace |
| `-project <path>` | Path to .xcodeproj |
| `-scheme <name>` | Build scheme |
| `-destination <spec>` | Target device/simulator |
| `-configuration <name>` | Debug or Release |
| `-derivedDataPath <path>` | Where to put build products |
| `-quiet` | Suppress xcodebuild output |
| `-parallelizeTargets` | Build targets in parallel |
| `-jobs <n>` | Number of concurrent build jobs |

---

## xcrun simctl Commands

### Listing Simulators

```bash
# List all simulators (human readable)
xcrun simctl list devices

# List as JSON (better for parsing)
xcrun simctl list devices --json

# List only available simulators
xcrun simctl list devices available

# List simulators for specific OS
xcrun simctl list devices "iOS 18"

# List device types
xcrun simctl list devicetypes

# List runtimes
xcrun simctl list runtimes
```

### Extracting UDIDs with jq

Name-based queries can return several devices across runtimes. Inspect matches and select a compatible UDID; `head -1` below is only a shorthand after confirming the selection. Stop if no available match exists.

```bash
# Get UDID of specific simulator
xcrun simctl list devices --json | \
  jq -r '.devices | .[].[] | select(.name=="iPhone 16 Pro" and .isAvailable==true) | .udid' | head -1

# Get all booted simulators
xcrun simctl list devices --json | \
  jq -r '.devices | .[].[] | select(.state=="Booted") | .udid'

# Get available simulators
xcrun simctl list devices --json | \
  jq -r '.devices | .[].[] | select(.isAvailable==true) | {name, udid}'
```

### Simulator Lifecycle

Boot only if the selected device is not already Booted. After boot, run `xcrun simctl bootstatus "$UDID" -b` before install or launch. Check errors; do not suppress all boot failures.

```bash
# Boot simulator
xcrun simctl boot $UDID

# Shutdown simulator
xcrun simctl shutdown $UDID

# Shutdown all simulators
xcrun simctl shutdown all

# Erase simulator (reset to clean state)
xcrun simctl erase $UDID

# Delete simulator
xcrun simctl delete $UDID

# Create new simulator
xcrun simctl create "My iPhone" \
  "com.apple.CoreSimulator.SimDeviceType.iPhone-16-Pro" \
  "com.apple.CoreSimulator.SimRuntime.iOS-18-0"
```

### App Management

```bash
# Install app
xcrun simctl install $UDID /path/to/App.app

# Uninstall app
xcrun simctl uninstall $UDID com.bundle.identifier

# Launch app
xcrun simctl launch $UDID com.bundle.identifier

# Launch with console output
xcrun simctl launch --console $UDID com.bundle.identifier

# Launch with stdout/stderr redirect
xcrun simctl launch \
  --stdout=/tmp/stdout.log \
  --stderr=/tmp/stderr.log \
  $UDID com.bundle.identifier

# Launch and wait for debugger
xcrun simctl launch -w $UDID com.bundle.identifier

# Terminate app
xcrun simctl terminate $UDID com.bundle.identifier

# List installed apps
xcrun simctl listapps $UDID

# Get app info
xcrun simctl appinfo $UDID com.bundle.identifier

# Get app container path
xcrun simctl get_app_container $UDID com.bundle.identifier
```

### Screenshots and Video

```bash
# Take screenshot
xcrun simctl io $UDID screenshot /tmp/screenshot.png

# Screenshot as JPEG
xcrun simctl io $UDID screenshot --type=jpeg /tmp/screenshot.jpg

# Record video
xcrun simctl io $UDID recordVideo /tmp/recording.mp4

# Record with codec
xcrun simctl io $UDID recordVideo --codec=h264 /tmp/recording.mp4

# Stop recording: Press Ctrl+C in the terminal running recordVideo
```

### Location

```bash
# Set custom location
xcrun simctl location $UDID set 37.7749,-122.4194

# Location requires coordinates; place names are not supported.
xcrun simctl location "$UDID" set 37.7749,-122.4194

# Reset location
xcrun simctl location $UDID clear
```

### Status Bar Overrides

```bash
# Override time
xcrun simctl status_bar $UDID override --time "9:41"

# Override battery
xcrun simctl status_bar $UDID override --batteryLevel 100 --batteryState charged

# Override network
xcrun simctl status_bar $UDID override --dataNetwork wifi --wifiBars 3

# Clear all overrides
xcrun simctl status_bar $UDID clear
```

### Push Notifications

```bash
# Send push notification
xcrun simctl push $UDID com.bundle.identifier /path/to/payload.json

# Payload example (payload.json):
# {
#   "aps": {
#     "alert": {
#       "title": "Test",
#       "body": "Hello from simctl"
#     }
#   }
# }
```

### Privacy Permissions

Check `xcrun simctl help privacy` for supported services. `camera` is not in the checked service list. Handle its permission prompt through the app or UI test when applicable.

```bash
# Grant permission
xcrun simctl privacy $UDID grant photos com.bundle.identifier
xcrun simctl privacy $UDID grant microphone com.bundle.identifier
xcrun simctl privacy $UDID grant location com.bundle.identifier

# Revoke permission
xcrun simctl privacy $UDID revoke photos com.bundle.identifier

# Reset all permissions
xcrun simctl privacy $UDID reset all com.bundle.identifier
```

### Pasteboard

```bash
# Get pasteboard contents
xcrun simctl pbinfo $UDID

# Copy text to pasteboard
echo "Hello" | xcrun simctl pbcopy $UDID

# Paste from pasteboard
xcrun simctl pbpaste $UDID
```

### URL Handling

```bash
# Open URL in simulator
xcrun simctl openurl $UDID "https://example.com"

# Open deep link
xcrun simctl openurl $UDID "myapp://path/to/screen"
```

### Keychain

```bash
# Add certificate to keychain
xcrun simctl keychain $UDID add-root-cert /path/to/cert.pem

# Add certificate to the keychain
xcrun simctl keychain "$UDID" add-cert /path/to/cert.pem
```

### Diagnostics

```bash
# Collect diagnostic info
xcrun simctl diagnose

# Verbose logging
xcrun simctl logverbose $UDID enable
# ... reproduce issue ...
xcrun simctl logverbose $UDID disable

# Spawn process in simulator
xcrun simctl spawn $UDID log stream --predicate 'processImagePath CONTAINS "App"'
```

---

## Logging with /usr/bin/log

The examples below read host logs for macOS apps. For simulator apps, run the log command through `xcrun simctl spawn "$UDID" log stream` with the same filter.

```bash
# Stream logs for specific app
/usr/bin/log stream \
  --predicate 'processImagePath CONTAINS[cd] "AppName"' \
  --level debug

# Stream with JSON output
/usr/bin/log stream \
  --predicate 'processImagePath CONTAINS[cd] "AppName"' \
  --style json

# Stream with timeout
/usr/bin/log stream \
  --predicate 'processImagePath CONTAINS[cd] "AppName"' \
  --timeout 60s

# Filter by message content
/usr/bin/log stream \
  --predicate 'eventMessage CONTAINS[cd] "error"' \
  --level debug

# Save to file (background)
/usr/bin/log stream \
  --predicate 'processImagePath CONTAINS[cd] "AppName"' \
  --style json > /tmp/logs.json &
LOG_PID=$!

# Stop logging
kill $LOG_PID
```

### Common Predicates

| Predicate | Description |
|-----------|-------------|
| `processImagePath CONTAINS[cd] "App"` | Filter by app name |
| `eventMessage CONTAINS[cd] "error"` | Filter by message |
| `category == "network"` | Filter by category |
| `subsystem == "com.apple.xxx"` | Filter by subsystem |
| `messageType == error` | Only errors |

---

## Finding Built App Path

Use `-showBuildSettings -json` with the same scheme, destination, configuration, and derived-data path as the build. Select the app target, then join `TARGET_BUILD_DIR` and `FULL_PRODUCT_NAME`. Project settings such as `SYMROOT` can place products outside `-derivedDataPath`; use the reported product path. Read `CFBundleIdentifier` from that product's Info.plist. See [examples.md](examples.md) for the commands.

Do not use `find ... | head -1`: it can select stale products, nested apps, or test runners.
