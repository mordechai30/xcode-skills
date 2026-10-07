I read [final-practical-plan2.md](./final-practical-plan2.md) in full.

**The two plans agree on nearly all implementation work. The supplied plan is better organized around ordinary skill use and lifecycle behavior. Mine provides stronger evidence of current defects, explicitly identifies already implemented simplifications, and maps every section 4 fix to concrete outcomes and tests.**

I would use the supplied plan as the main structure, with the corrections and additions below.

### Where they agree

Both propose:

- One manager entrypoint per independent package.
- `status` and explicitly requested detailed inspection.
- Argument validation before Clean or Build.
- Explicit arguments replacing saved-scheme arguments.
- Operation-owned responses, with watch facts preserved.
- One rendering step for public output and logging.
- Flattened SwiftPM routing.
- One Apple helper load per debugger session.
- Supported Mobile combined Run.
- Removal of raw transcripts, duplicated results, stop dumps, and unused event recording.
- Structured diagnostics and incremental line handling.
- Accurate closed records and recovery of verified helpers.
- Short `SKILL.md` files with directly linked local references.
- Tests on the four local projects.

The supplied plan covers all twelve highest-value changes in section 4. However, several are spread across sections rather than explicitly mapped to that list.

### Material differences

| Topic | My plan | Supplied plan | Assessment |
|---|---|---|---|
| `--working-directory` | Remove it | Keep it on native routes | The supplied choice is reasonable: retaining a supported, useful input does not require generalized handling |
| Aliases | Separate Xcode target and package product; remove package scheme synonym | Retain harmless aliases | Either can be simple, but the final contract must name exactly which aliases remain |
| Pending breakpoint | My test wording implied watching a pending breakpoint | Return input request; keep it pending; watch resolved breakpoints | **The supplied plan is more accurate.** Current code already returns immediately for unresolved breakpoints |
| Pause deadline | Total deadline, but insufficiently explicit about queueing | Starts at submission; expired queued requests must not execute later | **Adopt the supplied requirement** |
| Cleanup script | Add active-context rejection | Keep explicit cleanup without session checks | My addition expanded scope. Prefer the supplied simple cleanup contract, with documentation directing ordinary session termination through Kill |
| Clean accounting | Preserved, but distributed across the plan | Exact boundary and invocation rules collected together | **Adopt the supplied explanation** |
| Combined Run outcomes | Tests and workflow guards | Explicitly separates Build failure, launch failure, immediate exit, and uncertainty | **Adopt its explicit outcome list** |
| Live acceptance | Equivalent coverage described procedurally | Explicit 24 baseline combinations, plus Debug lifecycle cases | Its count is clearer and easier to audit |
| Existing implementation | Detailed implemented/partial/missing table | Mostly describes intended work | Add my baseline table to avoid implementing work already done |
| Source application | Specific defects, source methods, payloads, and expected JSON | Useful technique-placement table, but often defers detailed source examination | Add concrete examples and evidence from my plan |

### Corrections my plan needs

**1. Pending breakpoints**

My “pending breakpoint followed by interruption” example was misleading. The current operation returns an input request when the breakpoint has no resolved locations.

The correct workflow is:

```text
create breakpoint
→ unresolved: retain it and return pending information
→ resolved while running: watch for an actual stop
```

The operation result must survive watching, but a pending breakpoint should not enter that resolved-breakpoint watch automatically.

**2. Pause must expire before execution, not just during observation**

A deadline measured only inside the operation can allow this sequence:

```text
Pause submitted
→ waits behind a slow status request
→ caller times out
→ Pause executes later
```

The supplied plan correctly prohibits that. Carry the submission deadline through the request and check it before sending the backend action.

**3. Removing `--working-directory` was not necessary**

Your instructions permit removing commands for simplicity, but do not require removing a useful supported argument. Keeping it only on native launch routes, with rejection elsewhere before Build, is a clear contract.

**4. Cleanup protection was an additional behavior change**

My proposed active-session check was not one of section 4’s required fixes. The supplied plan keeps cleanup narrow and explicit. That is a better scope fit, provided its destructive effect and separation from Kill remain clear.

### Corrections the supplied plan needs

**1. Restore the session’s authority explicitly**

Its “Absolute source of truth” section does not name **Skills-analysis.md**, even though you made that document authoritative.

Add:

> This plan implements section 4 of Skills-analysis.md and the relevant interface improvements in section 5. The user’s current Basic assumptions and instructions override conflicting earlier material.

Also include Skills-analysis.md and SimplifySkills.md in its Sources section. The older `skill_simplification_plan.md` should not replace them as the governing source.

**2. Preserve your original instructions verbatim**

The supplied plan rewrites, expands, and renumbers “Basic assumptions and instructions.” It also omits the original explicit requirement:

> “Use relative paths from the skill root.”

Although that requirement appears later, your instruction was to include the original list **as is**. Keep the original list unchanged and append the additional source-use instructions separately.

**3. Remove unsupported claims of agreement**

The phrase [“Keep `--working-directory` where supported, as agreed”](./final-practical-plan2.md:107) presents agreement that is not established in this conversation.

It should say:

> Proposed decision: retain `--working-directory` on native launch routes; reject it elsewhere before Clean or Build.

Likewise, the statement requiring discussion before *any* further behavior change adds a restriction beyond your assumption 3. Material changes should be explicit in the plan, but ordinary simplification choices should not create repeated approval questions.

**4. Name the Apple warning fix**

Its diagnostic section is sound but does not explicitly identify the concrete section 4 defect:

```text
GetBuildLog defaults to errors
→ warnings may be omitted
→ request severity:"warning" where supported
```

Add that action and its test.

**5. Distinguish timeout categories**

“Adapter requests at no more than 60 seconds” should not be read as a 60-second limit on every native build or on the entire breakpoint watch.

Skills-analysis.md explicitly distinguishes:

- MCP adapter request limits.
- Longer native Build/Clean execution.
- Potentially indefinite breakpoint watching.
- The proposed total Pause deadline.

State those separately.

### What should be added from my plan

The following additions make the supplied plan demonstrably more specific than section 4.

**A. An implementation baseline**

Include the implemented/partial/missing table. In particular, explicit dispatch, cached discovery, My Mac selection, Run compilation, and connection ownership already exist. Their implementation steps should be verification or focused cleanup—not reconstruction.

**B. A section 4 traceability table**

For each of the twelve changes, name:

```text
current defect
→ affected operation/helper
→ intended observable behavior
→ acceptance test
```

For example:

```text
Watch replaces the original result
→ manager watch completion
→ preserve breakpoint ID or Continue removal fact
→ manager-level test with a stop returned after the operation
```

**C. Actual backend restrictions**

“Other existing options remain only where useful” leaves the implementing agent too much contract work.

Add a per-route option table covering:

- Launch arguments.
- Working directory.
- Architecture.
- Derived data.
- Destination.
- SwiftPM product selection.

For every unsupported combination, prove zero Clean/Build/launch calls.

**D. Concrete public responses and complete workflows**

Keep its focused inspection examples, but add expected outcomes:

```json
{"status":"success","state":"paused","breakpoint":2,"resolved":true,"location":"main.swift:9"}
```

```json
{"status":"success","state":"running","removed":2}
```

Also include the complete fixture workflow:

```text
Run → set breakpoint → actual hit → inspect tick → Continue → Status → Kill
```

Explain what each step establishes.

**E. Specific Mobile combined-Run guards**

The supplied plan correctly says “unambiguously,” but should explain why:

- The upstream launcher’s name-based PID lookup requires independent executable verification.
- The upstream product resolver does not provide the skill’s exact selected-target guarantee.
- Ownership checks must happen before a launch that might reuse an external app.

These are concrete conditions for choosing the combined route.

**F. A storage disposition table**

Its storage prose is strong. Add the explicit table identifying what happens to app streams, bridge JSON, build-log artifacts, bootstrap records, notifications, stop records, and obsolete files.

That makes “remove unnecessary data” verifiable across the whole workflow.

### Recommended result

Use the supplied plan’s structure and adopt its clearer Clean rules, pending-breakpoint handling, submission deadline, outcome classification, and acceptance matrix. Add my implementation baseline, twelve-fix mapping, route restrictions, source-grounded examples, and storage table. Correct its authority and verbatim-instruction sections.

That combined plan would provide both a clear operational contract and a concrete implementation specification.

1. Correct the authority, instruction preservation, and unsupported “as agreed” wording.
2. Resolve the interface explicitly, retaining supported working directories and naming retained aliases.
3. Add the current-state baseline and section 4 traceability table.
4. Add exact backend restrictions, workflows, responses, and storage dispositions.
5. Retain the supplied lifecycle and test structure, with the Apple warning fix and timeout distinctions made explicit.