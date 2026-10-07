# Final practical plan: simplify the three Xcode operation skills

Produce three independent skills that an agent can use through clear documented commands, without reading implementation files or managing backend connections.

Implement the twelve fixes in section 4 of **Skills-analysis.md**, together with the relevant interface improvements in section 5. Preserve useful existing simplifications. Remove unnecessary code, requests, output, and stored data.

This plan replaces earlier implementation proposals. It retains supported native working-directory overrides, separates pending breakpoints from watching, and defines Pause expiry from command submission.

## 1. Absolute source of truth

The following **Basic assumptions and instructions** and **Source-use instructions** are reproduced from section 1 of the supplied plan. The source locations are grouped to remove repeated parent/child entries.

**Basic assumptions and instructions:**

1. The main intent in the simplification effort is **Simple and clear skills which are designated to be intuitively used!** We do not care for certain implementation details (how session is kept, bash or python is used or whatever else). **But We Do Care:** each skill is: simple, robust, with easily, clearly, "intuitively" launchable scripts with clear and unambiguous arguments. Focused, clear and concise outputs. SKILL.md should be concise and clear for more detailed info (if needed) SKILL.md might reference more info. from other .md files.
2. **Simplicity and brevity take precedence over generalization and over-engineering.**
3. Design skills with guaranteed assumption that each skill is used only: "one skill at a time, on one project, per one configuration (Debug, Release)" So no need to treat cases if the same skills is used simultaneously by more than one agent, or on more than one project!
4. No need to preserve existing commands and required operation behavior. If it contradicts with simplicity or operational ease.
5. Skill should clearly state that: **All scripts and CLI commands must run outside sandbox restrictions.**
5. Each skill’s package must contain its own scripts, examples, references, and tests. Installed documentation links, imports, and supporting-file dependencies must stay inside that package. Project-local logs and session artifacts retain their agreed locations (skill_simplification_plan.md).
6. skill should link supporting documents directly from SKILL.md. Must avoid reference chains. Use real heading anchors rather than ineffective #L123 fragments.
7. SKILL.md shape: should follow [progressive disclosure](~/agentc_stuff/.agents/skills-docs/progressive-disclosure.md).
8. Keep SKILL.md short: commands, essential boundaries, destination guidance, output limits, and brief backend differences. Strictly follow: [skill-best-practices](~/agentc_stuff/.agents/skills-docs/skill-best-practices.md).
9. skill's output should not exceed at most 200 UTF-8 bytes,
Exceptional error flow or requested detailed inspection of big codes' objects: at most 500 UTF-8 bytes
10. for tests use 4 projects in /Users/motyzas/src/skill-test-projects
11. An agent must be able to execute each skill's action/operation/task (such as build, set breakpoint etc. ) by reading its SKILL.md only (if needed .md files that referenced within SKILL.md). It should not /(must not) need read Python/Bash scripts or understand how the script work or any details such is how connection is retained or what python lib/version is used.
12. the current "Basic assumptions and instructions:" should be added to final plan as is.

These instructions override conflicting earlier plans, reference examples, and existing implementations.

### Source-use instructions

1. All the sources listed below show what is possible only. They do not prescribe implementation, architecture, commands, or behavior.
2. However Agent must go over all sources in depth (subfolders/files in subfolders/links/sub-links)
Agent must examine the sources (folders/files/examples/scripts/links) and identify what is needed and relevant to implement requested functionality. Agent should choose what (if anything) and how, to use to fulfill the user's request of skills simplification.
3. After understanding and explaining general ideas, quote specific methods, workflows, functions.
Note. Agent does not have to quote a thing it can present its own workflows, commands, examples, scripts and etc. (probably based on the sources).
4. Finally (regardlessly of source, fetched or inferred) Agent must present not only (quoted) info but how it should be used in scripts, or md or other relevant files to produce needed result. I.E. all workflows, commands, examples, scripts and etc. have to be focused, practical and well explained!

For every technique selected, identify **where it is used, how it works in the skill, and what useful result it produces**. Quotation is optional. Practical application is mandatory.

### Sources

| Source location | Included requested material |
|---|---|
| `/Users/motyzas/.codex/plugins/cache/openai-curated-remote/build-macos-apps/0.1.4` | Includes `skills/build-run-debug/SKILL.md`, `skills/swiftpm-macos/SKILL.md`, and supporting material |
| `/Users/motyzas/Downloads/mobilebuildmcp-cli/SKILL.md` | CLI skill and supporting material |
| `/Users/motyzas/Downloads/mobilebuildmcp/SKILL.md` | MCP skill and supporting material |
| `/Users/motyzas/.agents/skills_to_check/__xcode-build/references` | Includes `examples.md` and `XCUITEST_GUIDE.md` |
| `/Users/motyzas/.agents/skills_to_check/__xcodebuildmcp-cli/references` | References, nested files, contracts, and examples |
| `/Users/motyzas/.agents/skills_to_check/__xcode-cli/references` | Apple interface references and examples |
| `/Users/motyzas/Downloads/apple-platform-build-tools-claude-code-plugin-main` | Requested `skills/building-apple-platform-products`, `agents/builder.md`, and `release.sh` |
| [MobileBuildMCP repository](https://github.com/getsentry/MobileBuildMCP/tree/main) | Includes requested `example_projects` and `.agents/skills`, implementations, manifests, and tests |

### Application of this authority

Section 1 is the final statement of user intent. Use [Skills-analysis.md](./Skills-analysis.md) to identify the required fixes and existing safeguards. Use [SimplifySkills.md](./SimplifySkills.md) to identify simplifications already implemented and remaining work.

Apply these conflict resolutions:

- Existing commands may change where this plan specifies a simpler contract.
- Raw-output retention and references to omitted inspection data are removed.
- Preliminary ownership discovery and final selected-context settings remain distinct.
- Required connection retention, ownership verification, Clean accounting, atomic records, and request serialization remain.
- Remove coordination whose sole purpose is simultaneous agents or multiple active projects. Retain synchronization required by the owned transport and by Pause/Kill during watching.

## 2. Current baseline and intended interface

### Installed packages

Simplify:

- `~/.agents/skills/direct-xcode-op`
- `~/.agents/skills/apple-mcp-xcode-op`
- `~/.agents/skills/mobilebuildmcp-xcode-op`

Each package contains its own implementation, references, examples, and tests. Do not import another installed skill or create a shared external support package.

Keep one public executable entrypoint, `scripts/manager.py`, and the separate `scripts/cleanup.sh`. Make both directly executable. Resolve package resources from the script’s own location, so an absolute entrypoint path works from any working directory.

### What is already implemented

| Simplification | Verified baseline | Work required |
|---|---|---|
| Explicit command dispatch | Manager uses an explicit operation map | Keep; add Status |
| Discovery passed into retained runtime | Existing discovery is reused | Remove only demonstrated duplicate queries |
| Connection ownership | Preliminary discovery is native; retained backend connections belong to their runtime | Preserve |
| My Mac preference and Any Mac Run rejection | Present before Build | Verify through public commands |
| Build on every Run | Present | Preserve; remove stale reuse descriptions |
| Cached settings/product paths | Partly present | Reuse only under unchanged context |
| Package-local resources | Present | Preserve and test independence |
| Focused SwiftPM routing | Separate files exist, but layered inheritance remains | Flatten |
| Compact operation logs | Implemented in part | Remove raw data retained elsewhere |
| Compact session records | Some fields filtered | Remove full stop dumps and write accurate closed state |

Do not reconstruct working behavior merely to reduce file count or change internal style. Measure requests and stored data to prove that a simplification removes redundant work.

### Public commands

Commands below run from the skill root, outside sandbox restrictions.

| Command | Required inputs | Optional inputs |
|---|---|---|
| `build` | One container; `--configuration Debug\|Release` | Supported selection/output options |
| `run` | One container; configuration | Supported selection/output options, `--no-debugger`, supported launch inputs |
| `status` | None | None |
| `set-breakpoint` | `--file PATH --line POSITIVE_NUMBER` | None |
| `pause` | None; running debugger-enabled Debug session | None |
| `continue` | None; paused debugger-enabled Debug session | `--keep-breakpoint` |
| `debugger-command` | `--command TEXT` | `--detail` |
| `kill` | None; owned context | None |
| `cleanup.sh` | Project/package path or containing folder | None |

Exactly one container is accepted:

```text
--project PATH.xcodeproj
--workspace PATH.xcworkspace
--package PACKAGE_DIRECTORY
```

A package input names the directory containing `Package.swift`.

Follow-up commands need no project selection, session identifier, or connection details.

### Argument decisions

- Use `--target` as the documented Xcode target input.
- Use `--product` as the documented SwiftPM executable input.
- Retain target/product aliases because both identify the same selected build product. If both are supplied, accept identical values and reject different values.
- Package selection uses `--product`; remove the redundant package `--scheme` input.
- `--configuration` remains explicit for Build and Run.
- Paths resolve against the caller’s working directory. Examples use absolute project/source paths.
- Reject irrelevant options on follow-up commands.
- Reject unsupported route options before Clean or Build.
- Put `--arguments` last. Distinguish absent arguments from an explicitly empty list.

### Route-specific launch and build options

| Route | Explicit arguments | Working directory | Derived data / architecture override |
|---|---|---|---|
| Native Xcode | Supported | Supported | Supported |
| Native SwiftPM | Supported | Supported | Reject; current host and SwiftPM build location |
| Apple Xcode | Reject explicit override; use saved scheme arguments | Reject override; saved scheme behavior | Reject overrides the Apple route cannot honor |
| Apple SwiftPM Debug | Reject explicit override | Reject | Reject |
| Apple SwiftPM Release fallback | Supported | Supported | Reject |
| Mobile Xcode, debugger-enabled Debug | Reject unsupported Apple bridge launch overrides | Reject | Reject overrides the bridge cannot honor |
| Mobile Xcode, debugger-free | Supported | Reject | Supported through macOS tools |
| Mobile SwiftPM, debugger-enabled Debug | Reject unsupported Apple bridge overrides | Reject | Reject |
| Mobile SwiftPM, debugger-free | Supported | Reject | Reject |

For native launches, an omitted working directory defaults to the executable’s parent directory. Preserve documented saved-scheme/backend defaults on other routes.

A rejected request returns the actual unsupported option and a useful next action:

```json
{"status":"failure","stage":"validate","message":"This route does not accept --working-directory.","next":"Omit that option."}
```

Tests must prove zero Clean, Build, and launch calls for such a request.

## 3. Required fixes and backend workflows

### Section 4 traceability

The internal names below identify existing edit locations. They are not required knowledge for an agent using the finished skill.

| Required fix | Concrete change | Acceptance evidence |
|---|---|---|
| Preserve operation facts | Manager watch completion adds observed state without replacing the command’s facts | Breakpoint ID and Continue deletion/retention survive |
| Simplify response construction | Each operation constructs public fields; formatter only serializes and limits output | No envelope searching or frame-description substitution |
| Fix misleading truncation | Remove false log recovery references; recommend narrower inspection | Omitted marker absent from stored artifacts |
| Fix launch arguments | Carry explicit arguments through Xcode selection and launch; define replacement | Public command produces exact launch argument list |
| Validate unsupported options | Validate operation and selected route before preparation | Zero Clean/Build/launch calls on rejection |
| Reduce Apple polling overhead | Load package-local SB helper once per debugger session | One load across repeated actions |
| Remove unused event recording | Remove opaque LLDB event recorder, thread, offsets, and files | Stops still detected; no event artifact |
| Flatten package adapters | Replace inheritance/fallback delegation with explicit local routes | Correct backend selected without cross-package imports |
| Use Mobile combined Run | Select supported combined macOS route before compilation | One Build/launch invocation, no preliminary Build |
| Improve diagnostics | Use structured fields; preserve native blocks; carry incomplete lines | Warnings, notes, and split errors retained once |
| Close session records | Write compact closed state only after verified cleanup | No stale active-looking record |
| Recover incomplete launches | Clean verified helpers even without an app PID; preserve app uncertainty | Helpers removed without claiming unverified app cleanup |

### A. Selection and product resolution

Select a unique suitable scheme, app target, or executable product. Return an ambiguity result when several remain.

Reuse a suitable existing Debug/Release scheme. Copy a saved scheme only when necessary to make the requested configuration available. Preserve originals and reuse a suitable existing copy.

For local Xcode Run, select the discovered **My Mac** destination. Honor explicit supported destinations. Reject **Any Mac**, generic destinations, and placeholders for Run before compilation.

Resolve the selected Xcode application from its build settings:

```text
selected target
→ exactly one application settings row
→ TARGET_BUILD_DIR + EXECUTABLE_PATH
→ selected executable
```

Use the project/workspace, scheme, configuration, destination, architecture, and build roots of the actual operation.

The source example selects the requested application target before reading its product path. Apply that technique in the existing Python selection helper; do not add a `jq` dependency. [Selected-target example](~/.agents/skills_to_check/__xcode-build/references/examples.md)

For native SwiftPM:

```bash
swift package --package-path /path/Package describe --type json
swift build --package-path /path/Package --configuration debug --product Product
swift build --package-path /path/Package --configuration debug --show-bin-path
```

Identify executable products from the manifest and resolve the selected name beneath the returned binary directory. Do not search for an arbitrary executable or assume an app bundle exists.

Reuse only the small settings/product fields needed for the operation. Cache them within the attempt while the complete command context remains unchanged.

### B. Backend routes

| Skill | Xcode Build/Run | SwiftPM Build/Run |
|---|---|---|
| Native | `xcodebuild`; retained native LLDB for Debug; direct launch otherwise | `swift build`; retained native LLDB for Debug; direct launch otherwise |
| Apple | Owned Apple bridge; BuildProject or embedded RunProject; native matching Clean fallback | Apple Debug route; native SwiftPM Release fallback |
| Mobile | macOS tools for Build/debugger-free Run; persistent Apple bridge for debugger-enabled Debug | SwiftPM tools; Apple bridge for debugger-enabled Debug |

Keep the existing connection mechanism. Flatten package routing by giving each package explicit `clean`, `build`, `launch`, `status`, `stop`, and `close` behavior.

Remove inherited fallback chains and reflective delegation. Do not replace them with a universal adapter framework.

### C. Build and Clean accounting

Preserve these rules:

- Build never launches.
- Every Run invokes Build once and launch once through its selected route.
- Clean before the first invoked Build.
- Clean when the previous invoked Build is **more than** one hour old.
- Exactly one hour does not trigger age-based Clean.
- Failed prerequisite Clean blocks Build and does not update Build history.
- Mark history immediately before actual Build invocation.
- An invoked failed Build updates history, performs Clean, and waits without retry.
- Incomplete required Clean remains recorded for the next attempt.
- Embedded Build/Run receives preparation once.

Use the log filename timestamp for Build age. Later appended commands must not alter it.

Keep outcomes separate:

```text
Build failure
Build success → launch failure
Build success → verified running app
Build success → immediate exit
timeout / uncertain outcome
```

An uncertain Build or launch must not trigger an automatic second Run. Reconcile the owned state first.

### D. Explicit launch arguments

For supported direct launch routes:

| Input | Result |
|---|---|
| No `--arguments` | Enabled saved-scheme arguments for Xcode; none for SwiftPM |
| `--arguments ARG...` | Exactly that list, replacing saved arguments |
| Bare trailing `--arguments` | Empty launch argument list |

Never merge lists implicitly.

Example:

```bash
./scripts/manager.py run \
  --project /path/App.xcodeproj \
  --configuration Debug \
  --arguments --mode test
```

If the saved scheme contains `--mode normal`, the process receives only `--mode test`.

Implement the complete path:

```text
public parser
→ selected launch arguments
→ saved-scheme override decision
→ native/Mobile launch input
→ process arguments
```

Pass executable arguments only to launch. Mobile’s build `extraArgs` and runtime `launchArgs` have different purposes. [Combined macOS implementation](https://github.com/getsentry/MobileBuildMCP/blob/main/src/mcp/tools/macos/build_run_macos.ts)

### E. Mobile combined Run

The CLI source says:

> “Choose the smallest command sequence that satisfies the request.”

Apply that to supported debugger-free macOS Run. [CLI source](/Users/motyzas/Downloads/mobilebuildmcp-cli/SKILL.md)

Replace:

```text
Build → get app path → Launch → verify
```

with:

```text
validate selection and external-app absence
→ required Clean
→ build_run_macos
→ extract Build/launch outcome, app path, PID
→ verify executable identity and debugger absence
```

Never call Build and then combined Build/Run.

Inspect relevant session defaults once. Set the selected context with `persist:false` when needed, and reuse it for that owned server connection. Do not write configuration into the application project.

Use combined Run only when the selected scheme’s app product is unambiguous and the tool can honor the requested context. Otherwise choose the separate supported Build/Launch route **before compilation** and record the reason as a short stage.

This qualification is required because:

- The upstream product resolver extracts a product without the skill’s exact selected-target guarantee.
- The launcher resolves its returned PID by process name.
- A launcher may reuse an existing external application instance.

Retain pre-launch external-process checks and independent verification of PID, executable, and debugger absence. A returned PID alone does not establish ownership. [Product resolver](https://github.com/getsentry/MobileBuildMCP/blob/main/src/utils/app-path-resolver.ts), [launch helper](https://github.com/getsentry/MobileBuildMCP/blob/main/src/utils/macos-steps.ts)

### F. Apple helper setup

Load the package-local SB helper once in each owned debugger session. Later structured actions call its existing `handle(...)` function with a small request.

```text
first action: load → handle
later actions: handle
```

Apply this to Apple directly and Mobile’s Apple bridge.

Reset helper state when the debugger session ends. Lost connectivity returns uncertainty; do not create a replacement debugger or attach another session automatically.

## 4. Debugger behavior, responses, and recovery

### Breakpoints and watching

- Require an existing source file and a positive line.
- Record the owned breakpoint ID and requested/resolved locations.
- Report relocation explicitly.
- A location list is not proof of resolution; use actual resolution evidence.
- An unresolved breakpoint remains pending and returns immediately with a request for input.
- A resolved breakpoint set while running watches for a hit, another stop, exit, interruption, or lost connection.
- A resolved breakpoint set while paused returns immediately.
- Resolution is never reported as a hit.

Preserve command facts while adding the observed watch outcome.

```json
{"status":"success","state":"paused","breakpoint":2,"resolved":true,"location":"main.swift:9"}
```

Watching emits no progress chatter. An interrupted watch leaves execution unchanged and reports the freshly verified state or uncertainty.

Release the public operation lock between checks. Keep backend requests serialized, but do not hold a watch-wide lock that blocks Pause or Kill.

### Pause and Continue

Pause requires a running debugger-enabled Debug session.

Use a **15-second total deadline starting at submission**. Carry that deadline through queueing and execution:

```text
submission → queue wait → pre-action expiry check → interrupt → verify stop
```

An expired queued request must not send the interrupt later. Each backend call uses the remaining allowance.

Expiry returns uncertainty without automatic Continue, reconnection, or relaunch. A request already sent may still have affected the app; Status must report the observed state honestly.

Continue requires a paused debugger-enabled Debug session.

- Remove only the responsible owned breakpoint.
- `--keep-breakpoint` retains it and watches again.
- Manual pauses and runtime stops remove none.
- Unrelated breakpoints remain.

```json
{"status":"success","state":"running","removed":2}
```

```json
{"status":"success","state":"paused","kept":2,"location":"main.swift:9"}
```

Unexpected stops wait for user instruction. Do not automatically resume or change sanitizer settings.

### Status and inspection

Status reports the owned state for Debug and Release:

```text
running | paused | exited | uncertain | none
```

For debugger-enabled Debug, use the retained debugger. For debugger-free execution, verify the recorded process identity. A missing launch identity remains uncertain; do not adopt a matching external process.

Inspection forwards the requested LLDB command. Do not add a command parser or a framework that tries to police arbitrary debugger commands.

Preserve both output and error when both exist. Refresh recorded state when the command changes execution.

Examples:

```bash
./scripts/manager.py debugger-command --command "frame variable tick"
./scripts/manager.py debugger-command --command "frame variable object.member"
./scripts/manager.py debugger-command --command "thread backtrace -c 3" --detail
```

These inspect one value, one member, and a bounded stack respectively.

### Public response construction

Each operation constructs its public result. The formatter does not search backend envelopes or replace messages with long frame descriptions.

Keep essential facts:

| Operation | Facts to preserve |
|---|---|
| Build | Outcome; failing stage and actual cause |
| Run | Verified state, PID, debugger choice |
| Breakpoint | ID, resolution, actual stop location |
| Continue | State and removed/retained breakpoint |
| Pause | State and useful stop location |
| Inspection | Requested output and command error |
| Kill | App/helper cleanup and remaining uncertainty |
| Status | Owned app state |

Normal output is at most **200 UTF-8 bytes**. Exceptional errors or explicit `--detail` inspection may use **500**. Ordinary warnings and inspection do not automatically receive the larger allowance.

Count stdout, stderr, and the final newline together. Help and parser errors use the same bounded path.

Render once. Emit those bytes and append the exact same bytes to the operation log.

Shorten optional text at readable boundaries. Keep valid JSON and essential operation facts. For oversized inspection:

```json
{"status":"success","output":"...","omitted":true,"next":"Inspect one member or fewer frames."}
```

Discard omitted content. Do not claim it exists in a log.

### Kill and incomplete-launch recovery

When the connection is usable, remove owned breakpoints, terminate the app, and then close required dedicated debugger/helpers.

Verify process identities before fallback signals. Preserve shared IDE services and unrelated processes.

Assess app and helper cleanup separately:

```text
known app identity:
    app termination → verified helper cleanup

unknown app identity:
    retain app uncertainty → verified helper cleanup
```

A missing app PID must not strand verified dedicated helpers.

```json
{"status":"uncertain","stage":"kill","helpers":"terminated","app":"unverified","next":"Reconcile app state before another Run."}
```

After verified process cleanup, release the active context even if lost connectivity prevented breakpoint-removal verification. Warn that an IDE breakpoint may remain.

Write a compact completed record:

```json
{"state":"closed","configuration":"Debug","app":"terminated","helpers":"terminated"}
```

If app or required helper cleanup remains unresolved, retain only the facts needed for recovery and do not mark the context closed.

### Timeout distinctions

Keep these limits separate:

- MCP adapter requests: at most 60 seconds.
- Native Build: preserve its existing longer execution allowance.
- Native Clean/discovery: preserve their operation-specific limits.
- Breakpoint watching: may continue until a defined watch-ending event.
- Pause: 15 seconds total from submission.

Do not impose the adapter limit on an entire native build or on the complete watch.

## 5. Diagnostics and storage removal

The storage change applies throughout skill-controlled files and memory, not only to the named operation log.

### Retention policy

| Data | Required treatment |
|---|---|
| Operation logs | Stages, failures/warnings/errors, directly related diagnostic context, exact public responses |
| Backend transcripts and duplicate envelopes | Extract required facts, then discard |
| Ordinary app output | Consume incrementally and discard |
| App diagnostics | Preserve useful error/warning blocks |
| Opaque LLDB events | Remove recorder, thread, artifacts, and offsets |
| Mobile bridge response artifacts | Validate tool/arguments; extract useful result; remove verified request-owned file |
| Backend build logs | Extract diagnostics; remove only proven request-owned files |
| Notifications | Handle required protocol events; discard unrelated notifications |
| MCP stderr | Drain continuously; record relevant diagnostics once |
| Bootstrap files | Consume after startup; remove when no longer required |
| Session records | Keep selection, ownership, state, and necessary breakpoint facts |
| Full frame descriptions/repeated stop dumps | Discard; retain short location, reason, and responsible breakpoint |
| Clean accounting | Keep |
| Build products/dependencies | Keep |
| Shared Xcode/backend storage | Preserve |

A returned artifact path alone does not prove permission to delete it. Confirm that the artifact belongs to the current request and is not shared.

Native app streams may use pipes or temporary spools according to the existing launch mechanism. Consume them promptly; do not leave an accumulating raw archive. Reset or remove consumed spool storage.

Remove full selection dumps, launch argument dumps, and settings dumps from logs. Preserve the small context required for agreed Build accounting.

### Diagnostics

Use structured backend error/diagnostic fields first. Keep only one decoded result during each request.

For native output, preserve the useful diagnostic block:

```text
file:line:column: error: actual failure
relevant source/caret context
related note explaining the failure
```

Carry incomplete lines across reads and flush the final incomplete line at EOF.

Record each received diagnostic once. Do not suppress a genuine later occurrence merely because its text matches an earlier one.

Request Apple `GetBuildLog` with `severity:"warning"` where supported. Its default error-only behavior must not silently omit warnings.

Treat explicit backend failure fields as evidence even when their text lacks an `error:` label. Keep Build failure distinct from transport uncertainty and launch failure.

A permitted log resembles:

```text
Stage: required Clean succeeded
Stage: Build invoked
Warning: main.swift:12: unused value
Stage: selected executable verified
Public: {"status":"success","state":"running","pid":1234,"debugger":true}
```

### Existing obsolete data

After confirming no active context depends on it, remove known obsolete skill-created event files, raw-output archives, consumed response artifacts, and startup files.

Do not delete arbitrary backend folders, build products, shared files, or operation logs.

### Cleanup script

Keep cleanup separate and explicitly invoked:

```bash
./scripts/cleanup.sh /path/App.xcodeproj
./scripts/cleanup.sh /path/Package
```

It:

- Performs no app/session checks.
- Does not terminate processes.
- Is never invoked automatically.
- Removes only non-log content inside the selected skill artifact folder.
- Preserves top-level operation logs.
- Uses bounded success/error output.

Documentation must distinguish Kill from artifact cleanup. Ordinary session termination uses Kill; cleanup removes artifacts on explicit request.

## 6. Documentation and practical agent workflows

### Package shape

```text
SKILL.md
scripts/manager.py
scripts/cleanup.sh
scripts/...
references/examples.md
references/backend.md
tests/...
```

Keep imports, links, helper scripts, examples, and tests inside each package. Duplication between installed packages is acceptable when it preserves independence.

Do not add a new framework, cross-skill coordinator, UI controller, distribution workflow, or project scaffolding.

### SKILL.md

Keep the main document sufficient for ordinary operation:

- Specific purpose and supported project types.
- **All scripts and CLI commands must run outside sandbox restrictions.**
- One-project/configuration boundary.
- Runnable command table.
- Required inputs and useful defaults.
- Route restrictions beside affected arguments.
- My Mac/Any Mac guidance.
- Debug/Release behavior.
- Essential breakpoint, ownership, and failure rules.
- Output limits.
- Two direct reference links.

Use relative paths from the skill root. References must use real heading anchors.

```markdown
[Arguments and workflows](references/examples.md#arguments)
[Backend limits and recovery](references/backend.md#backend-limits)
```

Keep implementation details out of the ordinary workflow. The caller executes the supplied script; it does not choose an interpreter, load helpers, or manage connection identifiers.

### Supporting references

`references/examples.md` contains complete argument types/defaults, route restrictions, command/output pairs, and focused workflows.

`references/backend.md` contains backend limitations, Clean details, diagnostics, agreed storage locations, and recovery instructions.

Both are directly discoverable from `SKILL.md`. Neither introduces another supporting-document chain. Add a contents list if a reference exceeds 100 lines.

The local authoring guidance says:

> “Keep references one level deep from SKILL.md.”

Apply that to these two files. [Progressive-disclosure guidance](~/agentc_stuff/.agents/skills-docs/progressive-disclosure.md)

### Practical Debug workflow

Native skill example, from its root:

```bash
./scripts/manager.py run \
  --package ~/src/skill-test-projects/HelloSwiftPackage \
  --configuration Debug \
  --product HelloSwift

./scripts/manager.py set-breakpoint \
  --file ~/src/skill-test-projects/HelloSwiftPackage/Sources/HelloSwift/main.swift \
  --line 9
```

The breakpoint command watches until the loop breakpoint is actually hit. Verify the source line during acceptance before using it.

At the verified stop:

```bash
./scripts/manager.py debugger-command --command "frame variable tick"
./scripts/manager.py continue
./scripts/manager.py status
./scripts/manager.py kill
```

Expected behavior:

1. Run builds once and owns one debugger-enabled app.
2. Breakpoint output identifies the actual paused location.
3. Inspection returns `tick` from the stopped frame.
4. Continue removes the responsible breakpoint.
5. Status reports the owned app.
6. Kill verifies process cleanup.

To retain the breakpoint instead:

```bash
./scripts/manager.py continue --keep-breakpoint
```

This resumes and watches for the next hit.

### Practical Release and immediate-exit workflow

```bash
./scripts/manager.py run \
  --package ~/src/skill-test-projects/HelloSwiftPackage \
  --configuration Release \
  --product HelloSwift \
  --arguments --exit

./scripts/manager.py status
./scripts/manager.py kill
```

The existing fixture supports `--exit`. Report the observed early-exit evidence accurately. Do not invent a verified live PID after the process has disappeared.

Provide equivalent package-local examples for Apple and Mobile, showing supported inputs and pre-Build rejection where a route cannot accept an override.

## 7. Sources: selected methods and practical application

These sources guide implementation; installed packages must not depend on their external locations.

| Source | Method selected | Application and result |
|---|---|---|
| [Skills-analysis.md](./Skills-analysis.md) | Sections 4/5 and source relevance | Twelve-fix mapping, retained safeguards, independent interface |
| [SimplifySkills.md](./SimplifySkills.md) | Simplification section | Baseline verification, reduced routing/discovery/storage |
| Three installed packages | Current operations, adapters, transport, records, and tests | Fix demonstrated defects without rebuilding working mechanisms |
| macOS plugin Build/Run/Debug and SwiftPM material | Clear entrypoint; product-specific build/launch | One public manager; native product resolution without assumed bundles |
| Local Mobile CLI/MCP skills | Minimal sequences, help/schema discovery, defaults | Choose supported combined operations; establish defaults once |
| `__xcode-build` examples | Exact target and matching settings context | Resolve the intended product instead of the first available app |
| XCUITest guide | Condition-based waits and precise assertions | Test actual stops/state; do not add UI-test targets |
| Mobile output/schema/MCP/bridge references | Structured outcomes, session defaults, retained bridge | Decode once; classify actual errors; keep one connection |
| Apple interface references | Returned workspace identifiers, live contracts, partial debugger responses | Use actual identifiers and reject incomplete/unsupported results |
| Apple platform build references | `xcrun`, explicit containers, package description/bin path | Focused native discovery and executable resolution |
| `builder.md` | Operation/result/error/next-action reporting | Short useful outcomes without compiler transcripts |
| `release.sh` | Plugin metadata release workflow | No implementation adaptation required |
| Mobile macOS implementation and helpers | Combined Run, product/PID artifacts, launch limitations | Fewer calls with independent ownership checks |
| Mobile example projects | Multiple executable and failure fixtures | Unit ambiguity/error scenarios; live testing stays on the four local projects |
| Mobile internal review skills | Contract, structured-output, test-boundary, packaging checks | Documentation/runtime alignment and injected dependencies |
| Skill creator and supplied authoring guidance | Progressive disclosure, concrete examples, executable resources | Short discoverable SKILL.md and package-local references |

Use live schemas and installed help to validate supported backend inputs. Do not turn a reference version into a hard-coded universal backend contract.

Use web-jina-reader for relevant public-source gaps. Do not claim that reviewing an entire repository tree requires copying its architecture or retaining its data.

## 8. Tests and acceptance

### Unit and public-command tests

Keep tests in each package. Use fake backend responses, injected clocks, temporary directories, and disposable process identities.

The upstream test guidance states:

> “Unit tests inject command/filesystem/external dependencies.”

Apply that technique with the existing Python tests. Do not introduce the upstream TypeScript test stack. [Test-boundary source](https://github.com/getsentry/MobileBuildMCP/blob/main/.agents/skills/mobilebuildmcp-test-boundary-review/SKILL.md)

| Area | Required cases |
|---|---|
| Inputs | Missing/conflicting containers; route restrictions; aliases; positive breakpoint lines |
| Launch arguments | Absent, explicit, empty; saved-scheme replacement; actual backend payload |
| Working directory | Explicit/default native directory; unsupported routes rejected before Build |
| Output | Valid JSON, Unicode, long signatures, simultaneous output/error, combined byte count |
| Watching | Preserve operation facts; hit, other stop, exit, interruption, lost connection |
| Breakpoints | Pending, unresolved locations, relocation, actual hit, unrelated breakpoint |
| Continue/Pause | Deletion/retention; manual stop; submission deadline; expired queued action |
| Build/Clean | First Build; exactly/more than one hour; failed prerequisite; failed invoked Build; no retry |
| Combined Run | One invocation; Build/launch distinction; wrong product/PID; external instance |
| Connections | One retained setup; one helper load; no automatic replacement |
| Recovery | Missing app PID; verified helpers; PID reuse; incomplete cleanup; closed records |
| Diagnostics | Structured warnings; Apple warning request; multiline native notes; split/final lines |
| Storage | Discarded markers absent; consumed artifacts removed; shared artifacts preserved |
| Packaging | Local imports/resources, links/anchors, executable entrypoints, independent tests |

Test public commands through backend inputs. Helper-only tests are insufficient for argument propagation and watch result preservation.

Preserve distinct outcomes instead of forcing every backend success wrapper into public success.

### Live acceptance projects

| Fixture | Container |
|---|---|
| C++ | `~/src/skill-test-projects/HelloCpp/HelloCpp.xcodeproj` |
| Objective-C++ | `~/src/skill-test-projects/HelloObjCpp/HelloObjCpp.xcodeproj` |
| Swift | `~/src/skill-test-projects/HelloSwift/HelloSwift.xcodeproj` |
| SwiftPM | `~/src/skill-test-projects/HelloSwiftPackage` |

Run sequentially.

Complete **24 baseline cases**: three skills × four projects × Debug/Release. Each case verifies standalone Build without launch, Run, Status, and Kill.

Additionally:

- Exercise debugger-disabled Debug across all skills and projects.
- Exercise breakpoint hit, inspection, Pause, Continue deletion/retention, and interrupted watching on debugger-enabled routes.
- Verify supported arguments and pre-Build rejection elsewhere.
- Exercise the package’s immediate-exit behavior.
- Measure setup, settings, Build, and launch calls.
- Check stdout/stderr byte limits and every skill-controlled artifact.
- Use isolated fixture copies for deliberate build failures.
- Use injected time for the one-hour boundary.
- Finish with all owned test apps/helpers terminated.

Expected fixture stops may be automated during acceptance. Unexpected stops require user input.

### Independent agent use

Verify each package without relying on the other two packages or external reference files.

Exercise three documentation-driven scenarios:

1. Build the selected configuration without launch.
2. Run Debug, stop at a source breakpoint, inspect, Continue, and Kill.
3. Diagnose an unsupported input or failure and take the documented next action.

Success requires completing these scenarios from `SKILL.md` and its directly linked references without reading scripts.

### Completion evidence

Record measured results:

- Public-command tests passed.
- Baseline and additional live cases completed.
- Redundant request counts reduced.
- Output limits satisfied.
- Discarded data absent from stored artifacts.
- Correct closed/uncertain records.
- Package independence verified.
- No owned test processes left running.

No commit is part of this plan.

## 9. Concrete implementation steps

**Unresolved material questions: none.** If an installed backend demonstrably cannot satisfy a specified route, report the limitation before changing the public behavior.

1. **Define the contract and acceptance cases.** Document commands, required inputs, aliases, route restrictions, defaults, argument replacement, working directories, and short outcomes. Add focused tests for the demonstrated gaps.
2. **Simplify the entrypoint and public results.** Keep explicit dispatch, add Status, preserve watch facts, render once, and enforce combined output limits.
3. **Correct input propagation and validation.** Carry launch arguments and native working directories end to end. Reject unsupported/irrelevant inputs before Clean or Build.
4. **Simplify selection and backend routing.** Reuse unchanged context, flatten SwiftPM adapters, load the Apple helper once, and choose supported Mobile combined Run before compilation.
5. **Correct lifecycle behavior.** Preserve Clean accounting, distinguish Build/launch outcomes, implement submission-based Pause expiry, recover verified helpers, and write accurate closed records.
6. **Remove unnecessary storage and code.** Remove unused event recording, duplicated results, transcripts, full stop dumps, consumed startup/artifact files, and unused reuse helpers. Improve diagnostic extraction and verify discarded-data absence.
7. **Finish the independent skill documentation.** Keep SKILL.md short, move conditional detail into the two directly linked references, and verify every example, restriction, path, and anchor.
8. **Verify the installed packages.** Run unit/transport tests, the 24 baseline cases, additional Debug lifecycle cases, and documentation-driven independent use. Terminate owned test sessions and report measured results and any remaining limitations.
