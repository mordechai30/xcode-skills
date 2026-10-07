
# Final practical plan: simplify the three skills

Produce three independent skills that an agent can use from their documented commands, without reading scripts or managing debugger connections. Improve clarity, reliability, and response size. Remove complexity that does not serve the supported workflow.

This replaces the earlier simplification plan and incorporates the corrections discussed afterward.

## 1. Absolute source of truth

**Basic assumptions and instructions:**


1. The main intent in the simplification effort is **Simple and clear skills which are designated to be intuitively used!** We do not care for certain implementation details (how session is kept, bash or python is used or whatever else). **But We Do Care:** each skill is: simple, robust, with easily, clearly, "intuitively" launchable scripts with clear and unambiguous arguments. Focused, clear and concise outputs. SKILL.md should be concise and clear for more detailed info (if needed) SKILL.md might reference more info. from other .md files.
2. **Simplicity and brevity take precedence over generalization and over-engineering.**
3. Design skills with guaranteed assumption that each skill is used only: "one skill at a time, on one project, per one configuration (Debug, Release)" So no need to treat cases if the same skills is used simultaneously by more than one agent, or on more than one project!
4. No need to preserve existing commands and required operation behavior. If it contradicts with simplicity or operational ease.
5. Skill should clearly state that: **All scripts and CLI commands must run outside sandbox restrictions.**
5. Each skill’s package must contain its own scripts, examples, references, and tests. Installed documentation links, imports, and supporting-file dependencies must stay inside that package. Project-local logs and session artifacts retain their agreed locations (skill_simplification_plan.md).
6. skill should link supporting documents directly from SKILL.md. Must avoid reference chains. Use real heading anchors rather than ineffective #L123 fragments.
7. SKILL.md shape: should follow progressive disclosure (/Users/motyzas/agentc_stuff/.agents/skills-docs/progressive-disclosure.md). 
8. Keep SKILL.md short: commands, essential boundaries, destination guidance, output limits, and brief backend differences (Strictly follow: /Users/motyzas/agentc_stuff/.agents/skills-docs/skill-best-practices.md).
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

- /Users/motyzas/.codex/plugins/cache/openai-curated-remote/build-macos-apps/0.1.4
- /Users/motyzas/.codex/plugins/cache/openai-curated-remote/build-macos-apps/0.1.4/skills/build-run-debug/SKILL.md
- /Users/motyzas/.codex/plugins/cache/openai-curated-remote/build-macos-apps/0.1.4/skills/swiftpm-macos/SKILL.md
- /Users/motyzas/Downloads/mobilebuildmcp-cli/SKILL.md
- /Users/motyzas/Downloads/mobilebuildmcp/SKILL.md
- /Users/motyzas/.agents/skills_to_check/__xcode-build/references
- /Users/motyzas/.agents/skills_to_check/__xcode-build/references/examples.md
- /Users/motyzas/.agents/skills_to_check/__xcodebuildmcp-cli/references
- /Users/motyzas/.agents/skills_to_check/__xcode-cli/references
- /Users/motyzas/Downloads/apple-platform-build-tools-claude-code-plugin-main/skills/building-apple-platform-products
- /Users/motyzas/Downloads/apple-platform-build-tools-claude-code-plugin-main/agents/builder.md
- /Users/motyzas/Downloads/apple-platform-build-tools-claude-code-plugin-main/release.sh
- https://github.com/getsentry/MobileBuildMCP/tree/main  
- https://github.com/getsentry/MobileBuildMCP/tree/main/example_projects  
- https://github.com/getsentry/MobileBuildMCP/tree/main/.agents/skills

if i have repetition of sources, remove repeated.

## 2. Intended interface and behavior

### Packages

Simplify the installed packages:

- `/Users/motyzas/.agents/skills/direct-xcode-op`
- `/Users/motyzas/.agents/skills/apple-mcp-xcode-op`
- `/Users/motyzas/.agents/skills/mobilebuildmcp-xcode-op`

Each package keeps its own required scripts, tests, and focused documentation. No installed package imports another skill or depends on external reference files.

Keep one public executable entrypoint, `scripts/manager.py`, and the separate `scripts/cleanup.sh`. Agents invoke them directly. Interpreter and connection details remain internal.

### Commands

| Command | Required arguments | Purpose |
|---|---|---|
| `build` | Container, `--configuration Debug\|Release` | Build without launching |
| `run` | Container, configuration | Build through the selected route and launch once |
| `status` | None | Report the owned app’s current state |
| `set-breakpoint` | `--file PATH --line NUMBER` | Set a source breakpoint and observe its outcome |
| `pause` | None | Pause running Debug execution |
| `continue` | None | Resume paused Debug execution |
| `debugger-command` | `--command TEXT` | Inspect the current debugger session |
| `kill` | None | Terminate the app and required dedicated processes |

Optional inputs:

- `--scheme`, `--target`, `--destination`: Xcode selection.
- `--product`: SwiftPM executable selection.
- `--no-debugger`: debugger-disabled Debug Run.
- `--keep-breakpoint`: retain the responsible breakpoint on Continue.
- `--detail`: explicitly request inspection within the 500-byte allowance.
- `--arguments`: executable arguments, placed last.
- `--working-directory`: supported native launch routes only.
- Other existing options remain only where useful and demonstrably supported.

Exactly one container is accepted: `--project`, `--workspace`, or `--package`. A package argument names the directory containing `Package.swift`.

Follow-up commands require no session identifier or repeated project selection.

### Explicit interface decisions

- Add `status` so an agent need not construct debugger commands merely to check state.
- Add `--detail` so larger inspection output is explicitly requested.
- Keep `--working-directory` where supported, as agreed.
- Distinguish omitted executable arguments from an explicitly empty list.
- Reject unsupported or irrelevant arguments before Clean or Build.
- Retain harmless aliases where they do not create ambiguous meanings.

These changes do not remove any current operation. Any further behavior change must be discussed explicitly before implementation.

### Defaults

- Select a unique suitable scheme/product. Return choices when selection is ambiguous.
- Reuse a suitable existing scheme, including an existing Debug or Release scheme. Copy a saved scheme only when needed.
- Select discovered **My Mac** for local Xcode Run.
- Reject **Any Mac** for Run before compilation; explain that it is a generic Build destination.
- Debug uses a debugger unless disabled explicitly.
- Release launches without a debugger.
- Run builds through the simplest supported backend route.
- A second Run or Build must not silently terminate an active app.

On supported routes, explicit `--arguments` replace saved arguments. Bare trailing `--arguments` means no arguments. With no override, Xcode uses enabled saved-scheme arguments; SwiftPM uses none.

## 3. Simplify implementation around the actual workflow

### Keep internal responsibilities narrow

The public entrypoint parses arguments, finds the current context, dispatches the command, and emits its response.

Operation modules perform their specific sequences. Backend helpers perform backend calls. Do not add a generic workflow engine, result framework, debugger-command interpreter, or cross-skill coordinator.

Keep working connection retention. Remove unnecessary indirection around it.

Because use is guaranteed to be sequential, remove machinery whose sole purpose is simultaneous agents or multiple active projects. Retain only synchronization needed for the owned debugger/transport and for Pause or Kill during watching.

Keep atomic records and process identity verification where they support recovery and safe termination.

### Use each backend’s natural route

| Skill | Xcode | SwiftPM |
|---|---|---|
| Native | `xcodebuild`; native LLDB for Debug; direct executable launch otherwise | `swift build`; native LLDB for Debug; direct launch otherwise |
| Apple | Owned `mcpbridge`; Apple Build/Run/debugger/Stop; matching native Clean fallback | Apple Debug route; approved native Release fallback |
| Mobile | Supported macOS operations; persistent Apple bridge for Debug | Supported SwiftPM operations; Apple bridge for debugger-enabled Debug |

Keep these differences internal. Document only differences that affect the agent’s arguments or capabilities.

Flatten layered SwiftPM inheritance and fallback delegation into explicit routes within each package. Do not require all three backends to share one universal adapter.

For Mobile debugger-free macOS Run, use combined `build_run_macos` when it can honor the selected app unambiguously. Otherwise choose the separate Build/Launch route before compilation. Never Build and then call another Build/Run operation.

### Practical techniques and their placement

| Technique | Where and how to use it | Result |
|---|---|---|
| Resolve selected Xcode target from build settings | Selection/backend helper reads the requested application target and its output settings | Build and Run address the intended product |
| Resolve SwiftPM executable products | Package helper uses package description and the configuration’s binary directory | No arbitrary executable search or assumed app bundle |
| Reuse resolved context | Pass selection and settings into the owning runtime; reuse while context is unchanged | Fewer discovery/settings calls |
| Retain backend connection | The owned runtime creates it once and serves later commands | Same app/debugger session without agent-managed IDs |
| Load Apple helper once | Load the package-local debugger helper once per owned debugger session | Less repeated setup during status, Pause, and breakpoint operations |
| Use supported combined Run | Mobile adapter invokes the combined operation only for an unambiguous supported selection | One Build/launch sequence |
| Read structured failures | Adapters examine actual error and operation fields before constructing outcomes | Wrapper success cannot conceal backend failure |

Use executable arguments as launch inputs, never as build arguments.

### Build and Clean

Preserve the existing agreed accounting:

- Clean before the first invoked Build or when the previous invoked Build is more than one hour old.
- Exactly one hour does not trigger age-based Clean.
- Failed prerequisite Clean blocks Build and leaves the timer unchanged.
- Invoked Build updates history even when it fails.
- Failed Build performs Clean, reports both outcomes, and waits without retry.
- Embedded Build/Run receives the same preparation once.
- Standalone Build never launches.

Use the log filename timestamp. Appending later operations does not change Build age.

Combined Run must distinguish:

- Build failure.
- Successful Build followed by launch failure.
- Successful launch.
- Immediate app exit.
- Uncertain outcome or timeout.

After a timeout, reconcile current app state before another launch. Extract required evidence before discarding responses or artifacts.

### Breakpoints, watching, Pause, and Continue

- Require an existing source file and positive line number.
- Record breakpoint identity and requested/resolved locations.
- Report relocation; do not describe resolution as a hit.
- Leave pending breakpoints intact and request input. Pending-breakpoint handling is separate from resolved-breakpoint watching.
- Watch a resolved breakpoint until a hit, another stop, exit, interruption, or connection loss.
- Preserve the operation’s facts when watching finishes.
- An interrupted watch does not change execution. Report the verified current state or uncertainty.
- A verified stop waits for the user’s next operation.
- Continue removes only the responsible owned breakpoint unless retained.
- Manual/runtime pauses remove no breakpoint; unrelated breakpoints survive.
- Inspection reads the current available state without trying to police arbitrary LLDB commands.

Watch checks must leave Pause and Kill available. Remove unused opaque event recording; retain the actual state observation used by the workflow.

Keep adapter requests at no more than 60 seconds. Replace Pause’s iteration count with the proposed 15-second total deadline, starting at command submission. Expired queued requests must not execute silently later. Expiry returns uncertainty without automatic Continue, reconnection, or relaunch.

### Kill and recovery

- Remove owned breakpoints while the debugger connection is usable.
- Terminate the app before required dedicated debugger parents/helpers.
- Verify identities before fallback signals.
- Preserve shared IDEs/services and unrelated processes.
- Assess app and helper cleanup separately. A missing app PID must not strand verified dedicated helpers.
- Retain unresolved app uncertainty until reconciled.
- After verified process cleanup, release the context when lost connectivity prevents breakpoint-removal verification, and warn that a breakpoint may remain.
- Write an accurate closed record only after cleanup is complete.

Keep `cleanup.sh` separate: no app/session checks, no automatic invocation, preserve top-level logs, and remove only non-log content inside the selected skill artifact folder.

## 4. Focused output, storage, and documentation

### Public responses

Each operation constructs its useful result. The formatter only serializes and enforces the byte limit; it does not search arbitrary backend envelopes for valuable text.

Use compact valid JSON:

- Normal response: at most **200 UTF-8 bytes**.
- Exceptional error or requested detailed inspection: at most **500 bytes**.
- Count stdout, stderr, and the final newline together.
- Watching emits no progress chatter.
- Help and argument errors use the bounded response path.

Keep essential facts before optional text:

- Build: outcome or failing stage/cause.
- Run: verified state, PID, debugger choice.
- Breakpoint: ID, resolution, stop location.
- Continue: state and removed/retained breakpoint.
- Pause: state and useful stop location.
- Inspection: requested output and any command error.
- Kill: app/helper cleanup and uncertainty.

Render once. Emit and log those exact bytes.

Shorten optional text at readable UTF-8 boundaries. Never truncate serialized JSON into invalid JSON or discard critical operation facts merely to retain a long message.

For oversized inspection, disclose omission and recommend a narrower query. Omitted content is discarded; do not imply that it exists in a log.

Practical documented queries:

```bash
./scripts/manager.py debugger-command --command "frame variable tick"
./scripts/manager.py debugger-command --command "frame variable object.member"
./scripts/manager.py debugger-command --command "thread backtrace -c 3" --detail
```

Explain that the first two inspect specific values and the third limits stack depth.

### Logs and retained data

Keep the agreed project-local skill folders and exact log naming:

```text
log-[skill-name]-[Debug|Release]-[YY-MM-DD-HH-MM-SS].txt
```

Logs contain only:

1. Failures, warnings, errors, and directly related diagnostic context.
2. Short stage information.
3. Exact public responses.

Remove full transcripts, settings dumps, ordinary repeated app output, overlapping response copies, opaque event files, and full stop descriptions.

Implementation:

- Consume output incrementally.
- Preserve structured diagnostics and useful multiline native error context.
- Carry split lines across reads and flush the final incomplete line.
- Record each received diagnostic once; do not suppress genuine later occurrences.
- Drain MCP stderr and required notifications without unbounded accumulation.
- Keep only one decoded response during a request.
- Consume bootstrap records after startup.
- Store only selections, ownership, state, and breakpoint facts needed for subsequent operations or recovery.

For temporary/backend artifacts, extract outcomes, products, identities, and diagnostics first. Delete only files proven to be request-owned. Returned paths alone do not authorize deleting shared backend files.

Remove known obsolete skill-created raw artifacts only after confirming no active session depends on them. Preserve build products, dependencies, and shared Xcode/backend storage.

### Documentation shape

Keep `SKILL.md` concise but sufficient for ordinary operation:

- Purpose and supported project types.
- Outside-sandbox instruction.
- One-project/configuration boundary.
- Runnable command table.
- Required inputs, useful defaults, and route restrictions.
- My Mac/Any Mac guidance.
- Debug/Release behavior.
- Output limits and essential lifecycle behavior.
- Direct links to conditional detail.

Keep two focused references:

- `references/examples.md`: extra copyable workflows, arguments, and expected outcomes.
- `references/backend.md`: backend limits, Clean details, recovery, and diagnostics.

Use paths relative to the skill root. Link both directly from `SKILL.md` with real heading anchors. Avoid reference chains and external supporting-file dependencies.

Do not require agents to choose an interpreter, read implementation files, load helper modules, or retain connection identifiers.

## 5. Sources and verification

### Guidance

Apply:

- `/Users/motyzas/agentc_stuff/.agents/skills-docs/progressive-disclosure.md`
- `/Users/motyzas/agentc_stuff/.agents/skills-docs/skill-best-practices.md`
- `/Users/motyzas/.codex/skills/.system/skill-creator/SKILL.md`

The source plan is `/Users/motyzas/Downloads/skill_simplification_plan.md`. Its conflicting instructions are replaced by the decisions in this plan.

### Deduplicated source locations

Parent sources are grouped with their specifically requested child material.

| Source | Material to examine |
|---|---|
| `/Users/motyzas/.codex/plugins/cache/openai-curated-remote/build-macos-apps/0.1.4` | Includes `skills/build-run-debug/SKILL.md`, `skills/swiftpm-macos/SKILL.md`, scripts, references, and linked material |
| `/Users/motyzas/Downloads/mobilebuildmcp-cli/SKILL.md` | CLI workflow and linked material |
| `/Users/motyzas/Downloads/mobilebuildmcp/SKILL.md` | MCP workflow, defaults, capabilities, and linked material |
| `/Users/motyzas/.agents/skills_to_check/__xcode-build/references` | Requested `XCUITEST_GUIDE.md` and `examples.md` |
| `/Users/motyzas/.agents/skills_to_check/__xcodebuildmcp-cli/references` | Nested references and linked contracts/examples |
| `/Users/motyzas/.agents/skills_to_check/__xcode-cli/references` | Nested Apple interface references and examples |
| `/Users/motyzas/Downloads/apple-platform-build-tools-claude-code-plugin-main` | Requested `skills/building-apple-platform-products`, `agents/builder.md`, and `release.sh` |
| [MobileBuildMCP repository](https://github.com/getsentry/MobileBuildMCP/tree/main) | Includes requested `example_projects` and `.agents/skills`, relevant implementations, tests, and linked material |

Examine the sources in depth. Select only relevant techniques. Copy or adapt focused content into the installed package when needed.

Quotation is optional. Every selected or independently designed workflow must explain its application in scripts or documentation and its expected result.

Do not expand this simplification into UI automation, distribution, project scaffolding, or a new testing framework merely because sources demonstrate those capabilities.

### Acceptance projects

Use:

| Fixture | Container |
|---|---|
| C++ app | `/Users/motyzas/src/skill-test-projects/HelloCpp/HelloCpp.xcodeproj` |
| Objective-C++ app | `/Users/motyzas/src/skill-test-projects/HelloObjCpp/HelloObjCpp.xcodeproj` |
| Swift app | `/Users/motyzas/src/skill-test-projects/HelloSwift/HelloSwift.xcodeproj` |
| SwiftPM executable | `/Users/motyzas/src/skill-test-projects/HelloSwiftPackage/Package.swift` |

Discover current selections and source breakpoint locations. Production code must contain no fixture-specific defaults.

### Required tests

Keep tests inside each package. Use fake backend responses, injected clocks, and disposable processes for unit tests.

Verify:

- Byte limits, valid JSON, Unicode, long text, errors, and inspection omission.
- Arguments reach launch; unsupported arguments cause zero Clean/Build/launch calls.
- Supported working directory changes reach the actual native launch.
- Connection/helper setup occurs once; unchanged settings are not queried repeatedly.
- Build never launches; Run builds and launches once.
- Clean timing/failures and separate combined Build/launch outcomes.
- Pending/relocated breakpoints, actual hits, watch interruption, retained operation facts.
- Continue deletion/retention, unrelated breakpoints, manual Pause, unexpected stops.
- Timeout reconciliation, immediate exit, lost connection, PID reuse, helper recovery.
- Accurate closed records and cleanup without session checks.
- Useful diagnostic blocks, split lines, and absence of discarded data.
- Local links, real anchors, executable entrypoints, and package independence.

Run all **24 Build/Run/Kill combinations**: three skills × four projects × Debug/Release. Additionally exercise debugger-disabled Debug and Debug lifecycle operations across all backends, including SwiftPM.

Expected fixture stops may be automated under existing authorization. Unexpected stops wait for user input. Finish with all test apps and owned debugger/helper sessions terminated.

### Evaluation against the absolute instructions

The simplification succeeds only when:

- An agent can intuitively select and run the documented operation.
- No script reading or connection management is required.
- One-project sequential use remains simple; multi-agent/multi-project machinery is absent.
- Responses contain useful facts within the specified limits.
- Documentation and runtime support remain package-local.
- References improve a concrete workflow rather than enlarge the skill unnecessarily.
- Existing complexity is reduced without concealing failures or weakening agreed behavior silently.

**Unresolved material questions: none.** Report a demonstrated backend limitation before changing the agreed behavior.

## 6. Concrete implementation steps

1. **Define the command contract and document it first.**  
   Write the runnable command table, required inputs, defaults, supported options, and short outcomes for each skill. Add Status and detailed inspection. Specify argument replacement and supported working directories. Verify ordinary workflows are understandable without scripts.

2. **Reduce entrypoint and operation responsibilities.**  
   Keep parsing, context lookup, explicit dispatch, and response emission in the entrypoint. Keep operation rules in their modules. Remove multi-agent/multi-project coordination and unused indirection while retaining the owned connection and necessary debugger synchronization.

3. **Fix operation-owned responses.**  
   Preserve breakpoint and Continue facts through watching. Implement valid bounded JSON, error preservation, inspection omission, and render-once logging. Test combined stdout/stderr limits and long Unicode values through the public entrypoint.

4. **Simplify selection and backend routes.**  
   Reuse resolved context, select suitable existing schemes, initialize connections/helpers once, and flatten SwiftPM routing. Choose supported Mobile combined Run before Build. Measure discovery, settings, Build, and launch calls to prove redundant work is removed.

5. **Correct lifecycle and failure handling.**  
   Separate Build/launch outcomes, reconcile timeouts, fix interrupted watching and Pause deadlines, and recover verified helpers after incomplete launch. Verify breakpoint ownership, app-first termination, lost-connection warnings, and closed records.

6. **Remove unnecessary output storage and code.**  
   Remove unused event recording, transcripts, duplicated envelopes, full stop dumps, and obsolete reuse helpers. Process diagnostics incrementally. Delete consumed request-owned artifacts only after extracting required evidence. Verify discarded markers do not remain in skill-controlled files.

7. **Finish focused package documentation.**  
   Apply the supplied guidance. Select or create practical examples and explain their inputs and results. Keep conditional detail in the two directly linked local references. Verify all links, anchors, commands, and restrictions against the actual implementation.

8. **Test and verify installed packages.**  
   Run focused unit/transport tests, the 24 fixture combinations, and Debug lifecycle acceptance. Verify each package independently, using only its documentation and bundled resources. Record measured results, terminate all owned test sessions, and report any remaining limitations. Do not commit.

