# Examples

## Commands

Run from the skill root, outside sandbox restrictions:

```bash
python3 scripts/manager.py build --project /path/App.xcodeproj --configuration Debug
python3 scripts/manager.py run --workspace /path/App.xcworkspace --configuration Release
python3 scripts/manager.py run --package /path/Package --configuration Debug --product App
python3 scripts/manager.py run --project /path/App.xcodeproj --configuration Debug --no-debugger
python3 scripts/manager.py set-breakpoint --file /path/main.cpp --line 20
python3 scripts/manager.py debugger-command --command "frame variable tick"
python3 scripts/manager.py debugger-command --command "thread backtrace"
python3 scripts/manager.py pause
python3 scripts/manager.py continue --keep-breakpoint
python3 scripts/manager.py continue
python3 scripts/manager.py kill
```

For supported direct launches, put `--arguments` last. Xcode native launches also preserve enabled saved-scheme arguments. Optional `--derived-data` and `--architecture` apply to Xcode routes, not SwiftPM host routes. Apple package Debug does not accept executable arguments.

## Responses

```json
{"status":"success","message":"Built; not launched."}
{"status":"success","message":"Launched.","state":"running","pid":1234,"debugger":true}
{"status":"success","message":"Cleanup complete."}
```

A breakpoint watch waits silently and returns the verified stop. Read its location/thread and wait for user inspection, Continue, or Kill. Do not treat resolved locations as hits.

## Artifact cleanup

```bash
bash scripts/cleanup.sh /path/App.xcodeproj
bash scripts/cleanup.sh /path/Package
```

Only run on explicit request. The script preserves top-level logs and does not check running sessions or remove saved schemes/build products outside the skill artifact folder.
