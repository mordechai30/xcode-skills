# Simplify and make the three skills self-contained

## 1. Principles and boundaries

**Simplicity and brevity take precedence over generalization and over-engineering.**

Support one skill at a time, one project, one configuration, and one owned app session. Preserve existing commands and required operation behavior.

Use each backend’s native workflow. Keep managers thin and imported operation modules focused. Do not introduce a general workflow engine, debugger framework, or cross-skill coordinator.

All scripts and CLI commands run outside sandbox restrictions.

Installed packages:

- `/Users/motyzas/.agents/skills/direct-xcode-op`
- `/Users/motyzas/.agents/skills/apple-mcp-xcode-op`
- `/Users/motyzas/.agents/skills/mobilebuildmcp-xcode-op`

Each package contains its own scripts, examples, references, and tests. Installed documentation links, imports, and supporting-file dependencies must stay inside that package. Project-local logs and session artifacts retain their agreed locations.

## 2. Short instructions, guidance, and optional reference materials

**Use relative paths from the skill root. Link supporting documents directly from `SKILL.md`; avoid reference chains. Use real heading anchors rather than ineffective `#L123` fragments.**

Apply progressive disclosure. Keep `SKILL.md` short: commands, essential boundaries, destination guidance, output limits, and brief backend differences.

Read supporting references only when needed. Ordinary execution must not require reading script implementations.

Keep two focused documents per skill:

| Document | Content |
|---|---|
| `references/backend.md` | Necessary backend techniques, limitations, and diagnostics |
| `references/examples.md` | Installed commands and short expected responses |

### Skill-writing guidance

Read and apply:

- `~/agentc_stuff/.agents/skills/progressive-disclosure.md`
- `~/agentc_stuff/.agents/skills/skill-best-practices.md`
- `~/.codex/skills/.system/skill-creator/SKILL.md`

### Optional examples and reference materials

**These materials show examples of what is possible. They do not prescribe implementation, architecture, commands, or behavior.**

The implementing agent must evaluate their relevance and choose what, if anything, to use, adapt, cite, or reference. The approved plan remains authoritative.

Available locations:

- `/Users/motyzas/src/GL_renderer/docs/handoffs/xcode-build-help.txt`
- `/Users/motyzas/.agents/skills_to_check/__xcode-build/references`
- `/Users/motyzas/.agents/skills_to_check/__xcode-cli/references`
- `/Users/motyzas/.agents/skills_to_check/__xcode-universal-debug/references`
- `/Users/motyzas/.codex/plugins/cache/openai-curated-remote/build-macos-apps/0.1.4/skills/build-run-debug/SKILL.md`
- `/Users/motyzas/.codex/plugins/cache/openai-curated-remote/build-macos-apps/0.1.4/skills/swiftpm-macos/SKILL.md`
- [Official MobileBuildMCP CLI skill](https://github.com/getsentry/MobileBuildMCP/blob/main/skills/mobilebuildmcp-cli/SKILL.md)

If supporting material is needed, copy or adapt only focused, applicable content into the relevant skill folder. Installed skills must not reference external files.

Preserve useful local material already corrected by the user. Remove obsolete external-helper commands, unrelated material, and unsupported examples.

Installed help and live schemas determine supported backend arguments. Reference versions must not become hard-coded contracts.

## 3. Execution and output

### Public responses

Use one public output function per package.

- Normal invocation: at most **200 UTF-8 bytes**.
- Exceptional error or requested detailed inspection: at most **500 UTF-8 bytes**.
- Count combined stdout/stderr, newlines, and watch results.
- Return valid compact JSON with status, a short message, and necessary operation data.
- Capture backend output, app output, and tracebacks in local logs.
- Shorten oversized inspection output at readable boundaries. Disclose omissions and include a compact log reference.
- Watching stays silent until a stop, exit, interruption, or lost connection.
- Help and argument errors use the same bounded output path.

### Backend routes

| Skill | Route |
|---|---|
| Native | `xcodebuild` / `swift build`; retained LLDB for Debug; direct launch without debugger |
| Apple MCP | Owned `mcpbridge`; Apple selection, Build, Run, debugging, and Stop |
| MobileBuildMCP | Supported macOS/SwiftPM operations and session defaults; persistent Apple bridge for Debug |

Keep the approved Apple native Clean fallback and native SwiftPM Release fallback. Adapter requests remain limited to 60 seconds.

### Simplification

Replace reflective routing with explicit dispatch. Remove repeated discovery between launcher and runtime. Open backend connections only in their owning runtime.

Select discovered **My Mac** for local execution; honor explicit supported choices. Reject **Any Mac** for Run before compilation and explain its generic Build purpose.

Build on every Run through the simplest supported route. Remove unused product-reuse checks and fingerprints. Resolve the executable once where possible, pass it forward, and reuse unchanged settings within an attempt.

Replace universal cross-backend SwiftPM branching with focused handling in each skill. Save each backend response once. Remove overlapping diagnostic copies, diagnostics in session/bootstrap records, unused helpers, imports, and unreachable branches.

Keep retained connections, necessary atomic ownership records, command serialization, and verified termination.