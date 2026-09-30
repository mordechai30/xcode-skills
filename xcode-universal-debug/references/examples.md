## Examples

```bash
SCHEME=renderer ~/.agents/skills/xcode-universal-debug/scripts/xcode_debug.sh ~/src/projectRoot --release --lldb
```
This builds Release of specific scheme named "renderer" and starts it in LLDB.

```bash
~/.agents/skills/xcode-universal-debug/scripts/xcode_debug.sh ~/src/projectRoot --debug
or
~/.agents/skills/xcode-universal-debug/scripts/xcode_debug.sh ~/src/projectRoot
```
This builds Debug and runs it without LLDB.

```bash
~/.agents/skills/xcode-universal-debug/scripts/xcode_debug.sh ~/src/projectRoot --debug --lldb
```
This builds Debug and starts it in LLDB.

```bash
~/.agents/skills/xcode-universal-debug/scripts/xcode_debug.sh ~/src/projectRoot --kill
```

This finds the previously running app for the selected scheme and kills it
with `kill -KILL`. If the app PID cannot be killed, the script kills the
app's direct parent PID.
