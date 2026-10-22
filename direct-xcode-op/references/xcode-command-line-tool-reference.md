<!--
{
  "documentType" : "article",
  "framework" : "Xcode",
  "identifier" : "/documentation/Xcode/xcode-command-line-tool-reference",
  "metadataVersion" : "0.1.0",
  "role" : "article",
  "title" : "Xcode command-line tool reference"
}
-->

# Xcode command-line tool reference

Use command-line tools that require you to install Xcode and set the app as the active developer directory.

## Overview

Xcode includes a set of command-line tools that only ship with the app, such as
`devicectl`, `simctl`, and `xcodebuild`. You must install and set Xcode as the
active developer directory before you can invoke these commands in Terminal.

### Automate build and version numbers

- `agvtool`:
  Manage build and version numbers.
  To learn more about this command, enter `man agvtool` in Terminal.

### Build a project

- `xcodebuild`: Build Xcode projects and workspaces.
  To learn more about this command, enter `man xcodebuild` in Terminal.

### Debug a project

- `devicectl`:
  Manage and interact with devices connected to a host.
  To learn more about this command, enter `xcrun devicectl help` in Terminal.
- `xcdebug`:
  Start a debugging session in Xcode.
  To learn more about this command, enter `xcdebug --help` in Terminal.

### Edit files

- `xed`:
  Open files in the Xcode app.
  To learn more about this command, enter `man xed` in Terminal.

### Identify and merge changes

- `opendiff`:
  Use FileMerge to graphically compare or merge files or directories.
  To learn more about this command, enter `man opendiff` in Terminal.

### Inspect result bundles

- `xcresulttool`:
  Read result bundles.
  To learn more about this command, enter `man xcresulttool` in Terminal.

### Manage Instruments files

- `xctrace`:
  Record, import, export and symbolicate Instruments `.trace` files.
  To learn more about this command, enter `man xctrace` in Terminal.

### Manage scripting definition

- `desdp`:
  Generate scripting definition (“sdef”).
  To learn more about this command, enter `man desdp` in Terminal.
- `sdef`:
  Extract scripting definition (“sdef”).
  To learn more about this command, enter `man sdef` in Terminal.
- `sdp`:
  Process scripting definition (“sdef”).
  To learn more about this command, enter `man sdp` in Terminal.

### Manage the interface

- `actool`:
  Compile, print, update, and verify asset catalogs.
  To learn more about this command, enter `man actool` in Terminal.
- `ibtool`:
  Compile, print, update, and verify Interface Builder documents.
  To learn more about this command, enter `man ibtool` in Terminal.
- `xcstringstool`:
  Generate string tables from source code.
  To learn more about this command, enter `xcrun xcstringstool help` in Terminal.

### Manage the Simulator

- `simctl`:
  Control the Simulator.
  To learn more about this command, enter `xcrun simctl help` in Terminal.

---

Copyright &copy; 2026 Apple Inc. All rights reserved. | [Terms of Use](https://www.apple.com/legal/internet-services/terms/site.html) | [Privacy Policy](https://www.apple.com/privacy/privacy-policy)