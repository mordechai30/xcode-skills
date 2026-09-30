---
name: xcode-universal-debug kill update handoff
date: 2026-09-17
---

# Handoff

## Scope

Update the `xcode-universal-debug` skill with a force-kill mode for a running
macOS Xcode app.

## Completed changes

- Added canonical `--kill` mode to `scripts/xcode_debug.sh`.
- `--kill` resolves the runnable product by scheme and skips the build.
- It finds matching app PIDs with `ps` and sends `kill -KILL <pid>`.
- If the app kill fails, it reads the direct parent with `ps -p <pid> -o ppid=`
  and sends `kill -KILL <parent-pid>`.
- It verifies that no matching app process remains.
- Renamed `stop_existing_app()` to `clean_and_stop_before_launch()`.
- Updated the skill description, option list, and usage example.
- Removed the old `--stop` option. The unrelated LLDB argument
  `--stop-at-entry` remains.

## Artifacts

- `../SKILL.md`
- `../scripts/xcode_debug.sh`
- `examples.md`

## Validation

- `skill-creator` quick validation passed.
- `bash -n scripts/xcode_debug.sh` passed.
- Isolated mocked tests passed for direct app kill and parent-PID fallback.
- No live app was killed during testing.

## Suggested skills

- `xcode-universal-debug` for future launcher or debugger changes.
- `skill-creator` for future skill structure or instruction updates.
- `build-macos-apps:build-run-debug` for live macOS build and runtime checks.
