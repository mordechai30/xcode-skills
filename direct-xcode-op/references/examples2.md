# Build and Run Example

Use this Bash example for an iOS simulator app. Run it as one shell session. Replace all four configuration values after project, scheme, target, and destination discovery in [CLI_REFERENCE.md](CLI_REFERENCE.md). For a project, replace `-workspace` with `-project` in `PROJECT_ARGS`.

This example requires `jq`. It selects the app target by name and product type. If the selection is not unique, inspect the settings instead of guessing. Run a separate workflow for macOS or physical devices.

```bash
set -euo pipefail

# Verified workspace, scheme, app target, and available simulator.
PROJECT_ARGS=(-workspace '/path/to/App.xcworkspace')
SCHEME='App'
APP_TARGET='App'
UDID='REPLACE_WITH_VERIFIED_SIMULATOR_UDID'

# Check required tools and active Xcode.
[ "$(uname -s)" = Darwin ]
command -v jq >/dev/null
xcode-select -p
xcodebuild -version
xcrun --find simctl

# Check that this exact simulator is available.
DEVICES=$(xcrun simctl list devices --json)
jq -e --arg id "$UDID"   '[.devices[][] | select(.udid == $id and .isAvailable == true)] | length == 1'   <<< "$DEVICES" >/dev/null
STATE=$(jq -r --arg id "$UDID"   '.devices[][] | select(.udid == $id) | .state' <<< "$DEVICES")
if [ "$STATE" != Booted ]; then
  xcrun simctl boot "$UDID"
fi
xcrun simctl bootstatus "$UDID" -b

# Use a separate directory for this build.
DERIVED_DATA=$(mktemp -d "${TMPDIR:-/tmp}/xcode-build.XXXXXX")
DESTINATION="platform=iOS Simulator,id=$UDID"
xcodebuild "${PROJECT_ARGS[@]}" -scheme "$SCHEME"   -destination "$DESTINATION" -configuration Debug   -derivedDataPath "$DERIVED_DATA" build

# Resolve the app product for the same target and build settings.
SETTINGS=$(xcodebuild "${PROJECT_ARGS[@]}" -scheme "$SCHEME"   -destination "$DESTINATION" -configuration Debug   -derivedDataPath "$DERIVED_DATA" -showBuildSettings -json)
APP_SETTINGS=$(jq -ce --arg target "$APP_TARGET"   '[.[] | select(.target == $target and
    .buildSettings.PRODUCT_TYPE == "com.apple.product-type.application")]
   | if length == 1 then .[0].buildSettings
     else error("Expected one app target") end' <<< "$SETTINGS")
PRODUCTS_DIR=$(jq -er '.TARGET_BUILD_DIR' <<< "$APP_SETTINGS")
PRODUCT_NAME=$(jq -er '.FULL_PRODUCT_NAME' <<< "$APP_SETTINGS")
APP_PATH="$PRODUCTS_DIR/$PRODUCT_NAME"
[ -d "$APP_PATH" ]
BUNDLE_ID=$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$APP_PATH/Info.plist")
[ -n "$BUNDLE_ID" ]
xcrun simctl install "$UDID" "$APP_PATH"
xcrun simctl launch "$UDID" "$BUNDLE_ID"
printf 'Build products: %s\n' "$DERIVED_DATA"
```

For console output, use `simctl launch --console`; it remains attached until the app exits or the session ends. For simulator unified logs, use `simctl spawn "$UDID" log stream` with the app's process or subsystem filter. Use host `/usr/bin/log` for macOS apps.
