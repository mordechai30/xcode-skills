

# Skill analysis
The three skills retain the session behavior you requested, but their implementation can still be simplified substantially. The main weaknesses are **incomplete command contracts, information loss in public responses, duplicated backend handling, and uneven diagnostic capture**.

I made no changes during this audit. I inspected the installed code, documentation, relevant source examples, current CLI help, and Apple’s live MCP schemas. I used **web-jina-reader** for the web sources. I did not repeat application acceptance tests.

## 0. Major design and architecture

### A. Shared assumptions and design decisions

All three installed skills follow these boundaries:

- One project, one configuration, and one owned app session.
- Build never launches.
- Run builds, then launches once.
- Debug uses LLDB unless disabled.
- Release has no debugger.
- Follow-up operations reuse the skill-created session.
- No external debugger-session adoption.
- Breakpoint hits and unexpected stops wait for user instructions.
- Continue removes only the responsible owned breakpoint unless retention is requested.
- Kill terminates the app and performs required dedicated-process cleanup.
- Scripts and CLI commands must be invoked outside sandbox restrictions.
- Each package contains its own code and documentation.

The sandbox requirement is an instruction to the calling agent. A Python script cannot remove restrictions imposed by its parent execution environment.

All three use this basic structure:

```text
Agent → manager command → retained runtime → backend → owned app
```

The retained runtime preserves the live connection between separate manager invocations. A small locator identifies its project folder; project-local records contain process identities, breakpoints, and session state.

**That retained connection is necessary for your requested debugging workflow.** The surrounding selection, response, logging, and adapter code is where most simplification remains possible.

One distinction matters: “one skill at a time” is an operating instruction. There is no global coordinator preventing an agent from starting another skill. Each package maintains its own active-context record, consistent with the approved decision to avoid a coordinator.

### B. Differences visible to an agent

The operation names are the same. The differences an agent needs to understand are:

| Area | Native | Apple MCP | MobileBuildMCP |
|---|---|---|---|
| Required tools | Xcode command-line tools and LLDB | Apple MCP bridge and Xcode backend | MobileBuildMCP and its Apple bridge for debugging |
| Xcode app Build/Run | Native commands | Apple tools | Mobile tools; debugger-enabled Run uses Apple bridge |
| SwiftPM Debug | Native Swift build and LLDB | Apple package scheme | Apple package scheme through Mobile bridge |
| SwiftPM Release | Native Swift build | Approved native fallback | Mobile SwiftPM tools |
| Launch arguments | Native route supports arguments, with an implementation defect described below | Package Debug rejects explicit arguments | Package Debug through Apple has the same limitation |
| Failure surface | Compiler/process/debugger errors | Those errors plus bridge/IDE responses | Those errors plus Mobile result envelopes and bridge artifacts |
| GUI interaction today | Not exposed | Not exposed | Not exposed |

An agent should not need to understand the internal transport layers to perform normal operations.

### C. When each is preferable

| Skill | Best fit | Reason |
|---|---|---|
| `direct-xcode-op` | Straightforward macOS and SwiftPM debugging | Fewest external components; direct control over the executable and LLDB |
| `apple-mcp-xcode-op` | Work that benefits from Xcode’s selected workspace, schemes, debugger, and IDE tools | Uses Apple’s existing execution and debugger environment |
| `mobilebuildmcp-xcode-op` | Work already using MobileBuildMCP, or future supported device/simulator workflows | Provides established defaults, structured results, and a broader tool catalog |

For the present scope—simple local macOS Build/Run/debugging—**the native skill is the simplest technical route**.

Apple is useful when IDE context matters. Mobile adds value when its broader workflows are needed. Its macOS Debug route currently passes through Apple, so it introduces an additional layer for that particular task.

I did not measure response-time or memory differences in this audit. A speed ranking would require measurements.

## 1. Each skill’s technology and session connection

### Native: `direct-xcode-op`

Installed at `~/.agents/skills/direct-xcode-op`.

Its technologies are:

- `xcrun xcodebuild` for Xcode projects/workspaces.
- `swift build` for standalone SwiftPM packages.
- `xcrun lldb` and LLDB’s Python SB APIs for Debug.
- Direct executable launch for Release and debugger-disabled Debug.

For Debug, the runtime starts one owned LLDB process. LLDB loads the bundled controller, which opens a short local socket.

The controller uses concrete LLDB APIs:

- `CreateTarget`
- `SBLaunchInfo`
- `target.Launch`
- `BreakpointCreateByLocation`
- `BreakpointDelete`
- `process.Stop`
- `process.Continue`
- `process.Kill`
- `SBCommandInterpreter.HandleCommand`

Later manager commands reach that same controller. They do not create another debugger.

There are two connection levels:

```text
manager command → retained runtime socket → retained LLDB socket
```

The runtime stores the LLDB child handle and verified process identities. Kill can close and reap owned processes.

**Finding:** an event-reader thread writes LLDB event objects to an artifact, but public breakpoint watching still polls debugger status. That event recorder does not currently provide event-driven watching.

### Apple MCP: `apple-mcp-xcode-op`

Installed at `~/.agents/skills/apple-mcp-xcode-op`.

Its main technologies are:

- Owned `xcrun mcpbridge` stdio connection.
- Apple workspace, scheme, destination, Build, Run, Stop, and debugger tools.
- Native Clean fallback using matching build settings.
- Native SwiftPM Release fallback.

The runtime starts and retains one bridge connection. It initializes MCP and discovers current tool schemas.

Run uses `RunProject`, explicitly choosing debugger attachment. Later debugger operations use `InvokeDebuggerCommand` through the retained connection.

Importantly, **it does not start another native LLDB controller**. It executes bundled SB-API helper functions inside Xcode’s existing LLDB interpreter.

For example, a status request loads the helper and calls its structured snapshot function against `lldb.debugger`.

**Finding:** the helper module is loaded again for each status/action request. This adds avoidable work to polling and makes the command strings unnecessarily large.

Closing the bridge does not itself establish app termination. The Kill operation verifies and handles app/debugger cleanup separately.

### MobileBuildMCP: `mobilebuildmcp-xcode-op`

Installed at `~/.agents/skills/mobilebuildmcp-xcode-op`.

Its technologies are:

- Owned `mobilebuildmcp mcp` server.
- Mobile macOS and SwiftPM operations.
- Mobile’s persistent Apple bridge for debugger-enabled Debug.
- The same bundled Apple debugger adapter used within this independent package.

The runtime retains the Mobile server. Supported session defaults are set in memory.

For debugger-enabled Debug:

```text
manager → retained runtime → Mobile MCP → Apple bridge → Xcode LLDB
```

The bridge tools are `xcode_ide_list_tools` and `xcode_ide_call_tool`. MobileBuildMCP documents this bridge as persistent and exposes its live remote tool catalog. [MobileBuildMCP Xcode IDE bridge](https://github.com/getsentry/xcodebuildmcp.com/blob/main/app/docs/_content/xcode-ide.mdx).

Release and debugger-disabled routes use Mobile’s macOS/SwiftPM launch operations.

The skill independently verifies returned executable/PID identity. This check is justified: the installed macOS launcher resolves a PID using `pgrep -x` and selects the first returned match.

## 2. How the managers and operations work

### A. Manager responsibilities, limits, and implementation

The managers are byte-identical across the three packages.

Their proper responsibilities are already fairly narrow:

1. Parse and validate arguments.
2. Read the active-context locator.
3. Start a retained runtime for Run.
4. Forward follow-up commands to that runtime.
5. Dispatch explicit operation modules.
6. Watch through short status requests.
7. Emit the compact public response.

They use an explicit operation table rather than reflective operation discovery.

The retained runtime:

- Owns the backend connection.
- Holds current selection and session state.
- Serializes backend requests.
- Updates ownership records.
- Closes after completed cleanup.

The manager’s limitations are significant:

- It cannot infer whether arbitrary truncated text contains the most valuable information.
- It cannot make a slow backend interruptible merely by releasing the public operation lock.
- It cannot use a PID as a debugger command channel.
- It cannot guarantee correct behavior for an accepted argument that a backend silently ignores.

**Watching and command availability:** the public watch loop releases the operation lock between checks. Pause and Kill can therefore be submitted. However, the runtime handles requests serially. A slow backend status call can delay the next Pause or Kill request.

**Timeout distinction:** MCP adapter requests are capped at 60 seconds. Native Build/Clean commands currently have a 7,200-second timeout; the initial runtime request allows 7,500 seconds. Breakpoint watching can continue indefinitely by design. The documentation should distinguish these limits explicitly.

### B. Operation responsibilities and limits

These operation modules are also shared as independently packaged copies.

| Operation | Required sequence | Important limit |
|---|---|---|
| Build | Resolve selection; prepare log; required Clean; Build; verify selected product | Never launches |
| Clean | Clean matching build context | Imported helper; no standalone public command |
| Run | Prepare Build once; Build or combined Build/Run; launch once; verify identity and attachment | Blocks replacement of an active context |
| Set Breakpoint | Validate file/line; create owned breakpoint; record resolution; watch if running | Resolution is not a hit |
| Pause | Verify running Debug; interrupt; query actual stop | Backend queries can extend the total wait |
| Continue | Verify paused Debug; identify owned cause; delete unless retained; resume; verify | Preserves unrelated breakpoints |
| Debugger command | Forward requested command to retained debugger | Thin gateway, not a comprehensive interpreter |
| Kill | Remove owned breakpoint records where possible; terminate app; verify; clean dedicated processes | Shared/unrelated parents require a choice |

#### Build and Clean

The implementation retains the agreed accounting:

- First invoked Build requires Clean.
- More than one hour requires Clean.
- Exactly one hour does not.
- Failed prerequisite Clean blocks Build and does not advance Build history.
- Invoked failed Build advances history, then triggers Clean.
- Failed Build does not retry automatically.

Every Run now builds. The unused product-reuse policy is no longer needed.

#### Breakpoint and Continue

The implementation records requested and resolved source locations separately.

Continue intersects the actual stop’s breakpoint IDs with the skill-owned breakpoint IDs. It removes only the responsible owned breakpoint. Manual/runtime pauses remove none.

These are useful, focused rules. They should remain in the operation modules.

#### Inspection

The gateway forwards the requested LLDB command. Common value/stack commands require a paused session.

It intentionally does not prevent every possible debugger mutation. Follow-up operations query current state.

A simpler agent interface could add explicit value and stack commands while retaining `debugger-command` as the escape hatch.

#### Kill

Breakpoint removal happens while the connection remains usable, before app termination. Process termination itself is app-first, followed by dedicated cleanup.

This ordering addresses Apple breakpoints surviving into later launches.

After verified process cleanup, a lost connection can produce a warning that an IDE breakpoint may remain, then release the context. That matches your selected policy.

Two gaps remain:

- Recovery refuses a lost context without a recorded app identity, even when dedicated helper identities exist.
- Completed cleanup removes the active locator but leaves the project-local session record describing its earlier state.

The latter should be marked closed so agents do not mistake historical state for an active session.

## 3. Output filtering

### Current mechanism

The formatter is ordinary deterministic Python. **No agent or model runs inside it.**

It selects fields such as:

- Status and message.
- Running/paused/exited state.
- Run PID and debugger flag.
- Breakpoint ID.
- Removed breakpoint IDs.
- Stop location and thread.
- Inspection text.

It then serializes compact JSON and measures UTF-8 bytes, including the newline.

The limits are:

- 200 bytes for ordinary results.
- 500 bytes for failures, warnings, and inspection.

It does **not** inspect the whole response and determine semantic importance. Its rules decide which fields survive, then shorten the message prefix.

### Verified weaknesses

| Finding | Consequence |
|---|---|
| Watch completion replaces the original operation result | Breakpoint ID, resolution information, or Continue deletion information can disappear |
| Long frame descriptions become message text | A C++ signature can consume the available message space |
| Truncation keeps a byte prefix | It can cut through a meaningful line or value |
| Any nonempty location list is described as “resolved” | A pending breakpoint with unresolved locations can be misleadingly presented |
| Truncated responses include a log reference | Omitted inspection data is no longer stored in that log |
| Choices are appended to message text | A long ambiguity list can lose actionable choices |
| Inspection prefers output over error | A command returning both can conceal its error |

The correct simplification is **operation-specific short outcomes**, rather than trimming arbitrary backend text.

For example:

```json
{"status":"success","state":"paused","breakpoint":2,"location":"scenePipelineManager.cpp:788"}
```

A Build failure should return the failing stage and a short actual diagnostic. A Continue result should preserve whether the responsible breakpoint was removed or retained.

### Logs

The new operation-log policy is intended to keep only:

1. Failures, warnings, and errors.
2. Stage information.
3. Exact public responses.

The diagnostic extractor still needs work:

- It relies heavily on regular expressions.
- Multiline diagnostic context and notes can be dropped.
- Unlabelled runtime errors can be missed.
- Incremental app-output collection does not preserve incomplete lines between reads.
- Apple `GetBuildLog` is called without `severity: "warning"`; its live schema defaults to errors.

Also, compact operation logs and backend artifacts are different. Raw app-output files and Mobile bridge artifacts can still exist outside the named operation log.

The documentation and comments must state this accurately.

## 4. What should be fixed, removed, or simplified

The measured Python source sizes, including comments and blank lines, are:

| Package | Python files | Lines |
|---|---:|---:|
| Native | 27 | 1,961 |
| Apple | 30 | 2,667 |
| Mobile | 32 | 3,065 |

Some code implements your required ownership and debugger behavior. Several other parts remain unnecessarily complex.

### Highest-value changes

| Change | Specific action | Benefit |
|---|---|---|
| Preserve operation facts | Merge watch results with the original short result | Retains breakpoint ID and deletion/retention outcome |
| Simplify response construction | Each operation supplies its public fields; formatter only enforces the limit | Removes generic envelope interpretation |
| Fix misleading truncation | Remove false “full data in log” implications; tell the agent to narrow inspection | Matches your log policy |
| Fix launch arguments | Pass explicit arguments through Xcode native launches; define interaction with saved scheme arguments | Accepted options actually work |
| Validate unsupported options | Reject backend-unsupported arguments before Build | Avoids silent ignored inputs |
| Reduce Apple polling overhead | Load the SB helper once per owned debugger session | Smaller requests and fewer repeated imports |
| Remove unused event recording | Remove opaque LLDB event artifacts if polling remains the chosen implementation | Less code and storage |
| Flatten package adapters | Replace layered fallback inheritance with short explicit backend branches | Makes backend behavior easier to verify |
| Use Mobile combined Run | For supported debugger-free macOS routes, use `build_run_macos` after required Clean preparation | Fewer calls and less duplicated orchestration |
| Improve diagnostic extraction | Use backend diagnostic fields; preserve native diagnostic blocks | More reliable warnings/errors with smaller logs |
| Close session records accurately | Write a compact completed state after cleanup | Removes stale active-looking records |
| Improve incomplete-launch recovery | Clean verified dedicated helpers even when no app PID was established, while reporting app uncertainty separately | Avoids stranded owned processes |

The launch-argument defect is concrete: Xcode native launches read saved-scheme arguments, but explicit CLI arguments are stored in selection only for package routes. The existing launch-argument test checks scheme parsing, not the full manager-to-launch path.

### Further focused simplifications

- Keep one canonical backend result instead of overlapping `raw`, `response`, and `envelope` copies.
- Keep only required MCP notifications/diagnostics; current in-memory lists can grow during long sessions.
- Reuse settings only when their actual command context is unchanged.
- Preserve the difference between a preliminary discovery settings query and final settings using the selected destination/output directory.
- Remove stale comments claiming complete raw output is retained in the operation log.
- Replace iteration-count waits with an explicit total deadline where prompt Pause behavior matters.

### What should remain

Do not remove:

- The retained debugger connection.
- Verified process identities and cleanup safeguards.
- Required Clean accounting.
- Breakpoint ownership.
- Atomic session records.
- Request serialization.
- Honest uncertain-outcome handling.

The comparison skills are useful because they choose fewer commands and have clearer entrypoints. Their broad output and cleanup behavior do not satisfy all your requirements.

## 5. Making each skill an independent agent-facing work unit

The packages already contain their supporting code and references. An agent should use the public manager commands without reading Python.

**Separate executable operation scripts are unnecessary for this goal.** The approved imported-module arrangement already permits:

```text
manager.py build
manager.py run
manager.py pause
manager.py continue
manager.py kill
```

What is missing is a complete, reliable public contract.

### Required documentation improvements

Each `SKILL.md` should contain a compact command/argument table:

| Command | Required inputs | Optional inputs |
|---|---|---|
| Build | Container, configuration | Scheme, target/product, supported destination, output/architecture options |
| Run | Container, configuration | Same selection inputs; debugger choice; supported launch arguments |
| Set Breakpoint | File, positive line | None for the current session |
| Pause | Existing running Debug session | None |
| Continue | Existing paused Debug session | Keep breakpoint |
| Debugger command | Command text | None |
| Kill | Existing owned context | None |
| Cleanup script | Project/package path or containing folder | Explicit invocation only |

Backend differences must be stated beside the affected argument. An agent must not discover that an option is unsupported after compilation.

The current parser also accepts `--working-directory`, but the documentation does not clearly describe where it works.

### Useful small additions

1. **Status command.**  
   Report the owned app state for Debug or Release without using a debugger inspection command.

2. **Complete argument reference.**  
   Include accepted types, defaults, and backend restrictions. Short help can point to it.

3. **Predictable failure responses.**  
   Include stage, actual short cause, and next action.

4. **Explicit inspection behavior.**  
   Explain how to request individual fields when output is too large.

5. **Command-level acceptance tests.**  
   Test documented manager calls through to backend inputs, rather than testing only isolated helpers.

For execution from any working directory, an agent can use the absolute manager path, for example:

```bash
python3 /Users/motyzas/.agents/skills/direct-xcode-op/scripts/manager.py pause
```

The skill’s relative documentation links can remain unchanged.

The tests should prove that documented commands work without reading implementation files. That is the practical definition of an independent work unit here.

## 6. Adding interaction with the running app

### What is currently available

None of the three managers exposes mouse, keyboard, screenshots, or UI-element inspection.

There are also platform limitations that must be handled accurately:

| Technology | Verified capability | Remaining issue for this task |
|---|---|---|
| Mobile UI automation | Simulator snapshots, element references, taps, typing, waits, screenshots | Its workflow targets iOS simulators, not host macOS |
| Apple bridge | Current device-interaction session and event tools | Local macOS support is not established by the schemas |
| XCUITest/XCUIAutomation | macOS mouse, keyboard, scrolling, element queries, screenshots | Requires a UI-test execution environment |
| Native macOS Accessibility and Quartz | PID-scoped accessibility objects and input events | Would be an additional explicitly approved UI implementation |

Mobile’s workflow manifest explicitly lists iOS, and `snapshot_ui` requires a simulator identity. Enabling that workflow would not give the existing macOS skills mouse control. [Workflow manifest](https://github.com/getsentry/MobileBuildMCP/blob/main/manifests/workflows/ui-automation.yaml), [snapshot implementation](https://github.com/getsentry/MobileBuildMCP/blob/main/src/mcp/tools/ui-automation/snapshot_ui.ts).

### A. Minimum agent-facing UI interface

A small proposed interface could offer:

```text
ui snapshot
ui click
ui type
ui key
ui scroll
ui screenshot
```

These are proposed commands, not existing commands.

Their responsibilities should be limited:

- Use the skill’s recorded app identity.
- Verify it before interaction.
- Select the appropriate owned window.
- Return a short result.
- Verify the visible result where possible.
- Do not launch another app or silently resume a paused debugger.
- Close any owned UI-session resources during Kill.

Screenshots and large hierarchies should be artifacts, with a short response identifying them. They should not be encoded into the 200-byte public JSON or copied into the operation log.

### B. Native skill: XCUITest route

Your XCUITest proposal is technically valid for macOS.

Apple provides `click()`, `doubleClick()`, `rightClick()`, `typeText`, keyboard modifiers, scrolling, coordinates, and screenshot APIs. [Apple XCUIElement documentation](https://developer.apple.com/documentation/xcuiautomation/xcuielement).

A concrete test can use:

```swift
let app = XCUIApplication(bundleIdentifier: verifiedBundleID)
XCTAssertTrue(app.state == .runningForeground ||
              app.state == .runningBackground)

app.activate()

let button = app.buttons["RunScene"]
XCTAssertTrue(button.waitForExistence(timeout: 5))
button.click()
```

This belongs inside a UI-test target.

The critical detail is `activate()`: it preserves an existing running instance, but launches the app if it is not running. Therefore the skill must verify the owned process before and after activation. [Apple activate documentation](https://developer.apple.com/documentation/xcuiautomation/xcuiapplication/activate()).

To integrate this route:

1. Reuse an existing suitable UI-test target, or explicitly approve creating one.
2. Use the recorded bundle/product identity.
3. Avoid the reference guide’s automatic `app.launch()` and teardown termination for an already-owned app.
4. Build the UI-test runner once.
5. Run selected tests using `test-without-building`.
6. Verify that the same app instance remained under the skill’s debugger.

**For open-ended agent interaction**, a retained UI-test runner would need a small request channel. That introduces additional lifecycle code. Ordinary `xcodebuild test` calls alone do not provide an interactive mouse/keyboard command service.

### C. A simpler native macOS alternative

For arbitrary interaction with the existing app, a small macOS Accessibility/Quartz helper is worth considering.

Concrete APIs include:

- `AXUIElementCreateApplication(pid)` to target the recorded app.
- Accessibility attribute queries to find windows and controls.
- `AXUIElementPerformAction` for supported semantic actions.
- Quartz mouse/keyboard events for coordinate interaction.

The first two action APIs are present in the installed macOS SDK headers. Quartz provides event posting. [Apple CGEvent documentation](https://developer.apple.com/documentation/coregraphics/cgevent/post(tap:)).

This can avoid adding UI-test targets to each application. It requires appropriate macOS permissions and a dedicated helper.

It would be new implementation technology, so it needs agreement before implementation.

### D. Apple MCP route

The live bridge currently exposes:

- `DeviceInteractionStartWorkspaceSession`
- `DeviceInteractionSynthesize`
- `DeviceInteractionEndSession`

The start response supplies an interaction-session key. Synthesize can return screenshot and hierarchy paths alongside application state.

There is a concrete schema detail: Synthesize accepts `interactSessionKey`; Start and End use `interactionSessionKey`. The adapter must follow the discovered schema.

However, their descriptions target physical devices and simulators. **I have not established that these tools can operate on the local macOS app.**

Before selecting them for this feature, perform a focused macOS capability test. Do not call an install-and-run operation on an app already launched by the debugger skill.

Apple’s test tools can also run an existing UI-test target. That supports the XCUITest route, with the same runner and app-instance limitations.

### E. MobileBuildMCP route

For a future supported simulator route, the concrete workflow is:

```text
snapshot_ui → choose fresh elementRef → tap/type_text → wait_for_ui → refresh
```

Its implementation already guards UI actions against a stopped debugger.

For the present macOS skills, the choices are:

- Use a verified Apple macOS interaction tool through the existing bridge, if capability testing establishes support.
- Run existing macOS UI tests through Mobile’s testing route.
- Use a separately approved macOS helper.

Its simulator debugger/UI tools must not be substituted for macOS operations.

### F. A complete real-world interaction sequence

For example, to click a control and inspect the resulting code:

1. Run the app in Debug.
2. Set the requested source breakpoint.
3. Inspect the current UI and identify the control.
4. Click the control while the app runs.
5. Wait for the actual breakpoint hit.
6. Inspect variables and stack.
7. Continue through the existing operation, removing or retaining the breakpoint.
8. Inspect the resulting UI.
9. Kill the app and all required owned helpers.

While paused, the app generally cannot process new UI input. UI operations should report that state rather than automatically continuing.

For custom-rendered controls, semantic accessibility elements may be absent. Coordinate actions require current window geometry and visual verification; adding a UI framework alone does not create meaningful control identifiers.

## Sources: relevance to 4, 5, and 6

### 1. `/Users/motyzas/.agents/skills_to_check/__xcode-build/references/XCUITEST_GUIDE.md`

**Relevant to 5 and 6; limited relevance to 4.**

Useful methods include element queries, `waitForExistence`, typing, coordinates, screenshots, and attachments.

Combine them into a small UI-test case: identify a control, wait, act, verify a visible result, and capture evidence on failure.

Adapt the simulator examples to macOS. Do not copy its automatic app launch/termination behavior into an already-owned debugger session.

Its page-object examples are optional; introducing a large test abstraction would conflict with your simplicity preference.

### 2. `/Users/motyzas/.agents/skills_to_check/__xcode-build/references/examples.md`

**Relevant to 4 and 5.**

Its strongest example selects exactly one application target from build settings and constructs:

```text
TARGET_BUILD_DIR / FULL_PRODUCT_NAME
```

That is useful for correct product resolution and a clear command contract.

Its simulator boot/install/launch sequence is not a macOS UI driver. Do not incorporate those stages into these skills.

### 3. `/Users/motyzas/.agents/skills_to_check/__xcodebuildmcp-cli/references`

**Relevant to all three.**

The useful parts are:

- CLI: minimal command sequences, JSON arguments, combined Build/Run.
- MCP mode/configuration: retained server, workflow selection, session defaults.
- Output formats/schemas: domain errors, structured outcomes, artifacts.
- Xcode IDE bridge: current tool discovery and forwarded calls.
- Workflows/tools: platform boundaries and UI operations.

The applicable combination is:

```text
establish defaults once → call supported operation → inspect canonical result → verify identity
```

The UI material supports simulator interaction, not a demonstrated host-macOS route.

Installation/client/migration documents belong in conditional troubleshooting. Tool-authoring material is useful only if extending Mobile itself; it should not inflate these skills.

### 4. `/Users/motyzas/.agents/skills_to_check/__xcode-cli/references`

**Relevant to 4 and 5; partial relevance to 6.**

`installed-xcode-tools.md` is useful for returned workspace identifiers, scheme configuration, Build/Run/Stop, and partial debugger responses.

`cursor-xcode.md` explains the Apple MCP connection and discovery surface.

`mcpservers-xcode-mcp.md` describes a third-party `@devyhan/xcode-mcp` server. Its tools are not Apple’s `mcpbridge` tools. Do not mix their names or parameter contracts.

Preview rendering is useful for previews. It does not establish interaction with the running app.

### 5. `/Users/motyzas/Downloads/apple-platform-build-tools-claude-code-plugin-main/skills/building-apple-platform-products`

**Relevant to all three.**

Useful concrete techniques:

- `xcrun` tool resolution.
- Explicit project/workspace selection.
- `swift package describe`.
- `swift build --show-bin-path`.
- `build-for-testing` followed by `test-without-building`.
- `-only-testing`.
- `xcresulttool` result extraction.

For UI work, combine a selected macOS UI-test target, a narrow test filter, and a result bundle.

The archive/distribution/device-management references provide no necessary addition to the current lifecycle. Binary/signing references are useful only when diagnosing a corresponding failure.

### 6. `/Users/motyzas/Downloads/apple-platform-build-tools-claude-code-plugin-main/agents/builder.md`

**Relevant to 4 and 5.**

Its useful idea is to report operation, result, key error, artifact, and next action while shielding the caller from compiler output.

Its filtering is performed by an agent. Our scripts use deterministic rules; these are different mechanisms.

Do not adopt its subagent architecture or automatic retry policy. The latter conflicts with your Build-failure rule.

### 7. `/Users/motyzas/Downloads/apple-platform-build-tools-claude-code-plugin-main/release.sh`

**No substantive relevance to 4, 5, or 6.**

It releases the plugin by updating metadata, committing, tagging, and pushing. It does not build a Release app or provide debugging/UI behavior.

Nothing from it needs to enter the three skills.

### 8. `/Users/motyzas/.codex/plugins/cache/openai-curated-remote/build-macos-apps/0.1.4`

**Relevant to all three, through different parts.**

The strongest simplification examples are:

- `build-run-debug`: shell-first execution and one clear entrypoint.
- `swiftpm-macos`: straightforward manifest/product Build/Run/Test.
- `test-triage`: small test scope and precise failure categories.
- `run-button-bootstrap`: project-specific execution and optional GUI bundling.

Do not copy broad `pkill` cleanup or automatic Kill-before-Build behavior.

For UI-related work:

- AppKit interop and window management help make an application’s windows and controls behave correctly.
- SwiftUI patterns help construct testable UI.
- Telemetry can verify that a UI action reached its code path.

These materials implement application behavior. They do not supply an external generic mouse/keyboard controller.

### 9. `/Users/motyzas/Downloads/mobilebuildmcp-cli/SKILL.md`

**Strong relevance to 4 and 5; limited relevance to 6.**

Its useful principles are help-first discovery and the smallest command sequence.

Apply that by using installed help, choosing a supported combined operation, and returning a short actual outcome.

Its capability overview mentions UI automation but does not establish macOS support.


### 10. `/Users/motyzas/Downloads/mobilebuildmcp/SKILL.md`

**Strong relevance to 4 and 5; partial relevance to 6.**

It recommends checking `session_show_defaults` before discovery, discovering only missing context, and reporting the failing step and next action.

Our owned server currently sets defaults but does not first inspect them. Reading relevant existing defaults once would make configuration handling clearer.

Its broad UI/debugging overview must be read together with workflow platform definitions.

### 11. [MobileBuildMCP repository](https://github.com/getsentry/MobileBuildMCP/tree/main)

**Relevant to all three.**

The most useful implementation areas are:

- Tool manifests and argument schemas.
- Domain result construction.
- macOS launch helpers.
- Apple bridge routing.
- UI workflow manifests and snapshot/action implementations.

The installed launcher’s name-based PID resolution supports retaining our independent identity check.

Its structured results support extracting operation facts before rendering. Its simulator UI implementation supplies a useful observe–act–verify pattern, with fresh element references and a paused-debugger guard.

The repository’s entire runtime architecture should not be copied into these small skills.

### 12. [MobileBuildMCP example projects](https://github.com/getsentry/MobileBuildMCP/tree/main/example_projects)

**Relevant to 4 and 5; limited relevance to 6.**

The macOS example is a small SwiftUI application with ordinary test fixtures. Its XCTest and Swift Testing cases include intentional failures for result testing.

The SwiftPM example provides multiple executables, a library, and tests. It is useful for product ambiguity and short-lived versus long-running executable behavior.

The inspected macOS example does not demonstrate a general interactive UI driver. It cannot establish the missing capability by itself.

### 13. [MobileBuildMCP internal skills](https://github.com/getsentry/MobileBuildMCP/tree/main/.agents/skills)

**Relevant mainly to 4 and 5, with some lessons for 6.**

These are development/review skills rather than simpler replacements for our operation skills.

Useful checks include:

- **Runtime boundary:** avoid duplicate invocation paths and silent fallbacks.
- **Tool contract:** keep documented arguments aligned with manifests.
- **Structured output:** use the canonical result contract.
- **Rendering:** separate progress from final results.
- **Snapshot fixtures:** preserve intentional contract behavior.
- **Test boundary:** inject external dependencies in unit tests.
- **Packaging:** include required local resources.

For UI extensions, snapshot and tool-contract checks help prevent stale references and unsupported platform claims.

The Warden orchestration and repository-sweep workflows add no required capability to these three skills. They should not be incorporated.