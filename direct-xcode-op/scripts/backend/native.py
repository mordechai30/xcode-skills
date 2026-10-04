"""Native xcodebuild and LLDB adapter for macOS app projects."""
from __future__ import annotations

import json
import os
from pathlib import Path
import plistlib
import re
import subprocess

from lifecycle.state import append_log
from backend.native_debug import launch, close, request


def debug_status(ctx):
    """Refresh state from the retained LLDB controller.
    PID records are never used as a command channel.
    """
    return request(ctx, 'status')


def debug_action(ctx, action, **values):
    """Forward an operation to the retained controller.
    Operation modules supply the lifecycle rules.
    """
    return request(ctx, action, **values)


def stop(ctx):
    """Request app termination from the owning native backend.
    Direct launches use their retained child handle.
    """
    if ctx['session']['debugger']:
        return request(ctx, 'kill')
    child = ctx['runtime'].get('app_child')
    if child and child.poll() is None:
        child.terminate()
        try:
            child.wait(timeout=3)
        except subprocess.TimeoutExpired:
            return {'status': 'uncertain', 'message': 'App did not exit after TERM.'}
    return {'status': 'success'}


def _container(ctx):
    """Return the selected container argument pair.
    Keep project and workspace paths as individual arguments.
    """
    selection = ctx["selection"]
    if selection["project"]:
        return ["-project", selection["project"]]
    return ["-workspace", selection["workspace"]]


def _call(command, timeout=7200, cwd=None):
    """Run one native command with a bounded wait.
    Preserve stdout and stderr separately, plus complete diagnostic output.
    """
    try:
        result = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False, cwd=cwd)
    except subprocess.TimeoutExpired as error:
        stdout = error.stdout or b''
        stderr = error.stderr or b''
        stdout = stdout.decode(errors='replace') if isinstance(stdout, bytes) else stdout
        stderr = stderr.decode(errors='replace') if isinstance(stderr, bytes) else stderr
        return {'status': 'uncertain', 'raw': str(error) + '\n' + stdout + stderr,
                'stdout': stdout, 'stderr': stderr, 'command': command}
    except OSError as error:
        return {"status": "failure", "raw": str(error), "command": command}
    raw = result.stdout + result.stderr
    return {"status": "success" if result.returncode == 0 else "failure",
            "exit_code": result.returncode, "raw": raw, "stdout": result.stdout,
            "stderr": result.stderr, "command": command}


def _listing(ctx):
    """Read Xcode's JSON listing for schemes and configurations.
    Parse stdout only so stderr warnings do not corrupt the JSON.
    """
    result = _call(["xcrun", "xcodebuild", *_container(ctx), "-list", "-json"])
    if result["status"] != "success":
        raise RuntimeError("Could not discover the selected Xcode container: " + result["raw"])
    try:
        return json.loads(result["stdout"])
    except json.JSONDecodeError as error:
        raise RuntimeError("xcodebuild -list returned invalid JSON.") from error


def discover(args, ctx):
    """Discover schemes, app targets, configurations, and Mac destinations.
    Validate configurations independently and resolve workspace target ownership.
    """
    listing = _listing(ctx)
    project = listing.get("project") or listing.get("workspace") or {}
    schemes = project.get("schemes", [])
    configs = project.get("configurations", [])
    if args.configuration not in (configs or [args.configuration]):
        raise RuntimeError(f"Configuration {args.configuration} is not listed for the selected container.")
    base = ["xcrun", "xcodebuild", *_container(ctx)]
    scheme = args.scheme or (schemes[0] if len(schemes) == 1 else None)
    if not scheme:
        return {"choices": {"scheme": schemes, "target": [], "destination": []}, "raw": listing}
    destination_result = _call(base + ["-scheme", scheme, "-showdestinations"], timeout=180)
    if destination_result["status"] != "success":
        raise RuntimeError("Could not discover Xcode destinations: " + destination_result["raw"])
    destinations = []
    compatible = destination_result['raw'].split('Destinations incompatible')[0]
    for entry in re.findall(r'\{([^}]+)\}', compatible):
        fields = dict((key.strip(), value.strip()) for key, value in
                      re.findall(r'([^,:]+):([^,]+)', entry))
        if fields.get('platform') == 'macOS' and not fields.get('error'):
            value = 'platform=macOS' + (',id=' + fields['id'] if fields.get('id') else '')
            if value not in destinations:
                destinations.append(value)
    settings = _call(base + ["-scheme", scheme, "-configuration", args.configuration or "Debug", "-showBuildSettings", "-json"], timeout=300)
    if settings["status"] != "success":
        raise RuntimeError("Could not inspect selected scheme build settings: " + settings["raw"])
    try:
        rows = json.loads(settings["stdout"])
    except json.JSONDecodeError as error:
        raise RuntimeError("xcodebuild returned invalid JSON build settings.") from error
    targets = sorted({row.get("target") for row in rows if row.get("target") and
                      row.get("buildSettings", {}).get("PRODUCT_TYPE") == "com.apple.product-type.application" and
                      row.get("buildSettings", {}).get("PLATFORM_NAME") == "macosx"})
    owners = {row['target']: row['buildSettings'].get('PROJECT_FILE_PATH') for row in rows
              if row.get('target') in targets}
    for target in targets:
        projects = {row['buildSettings'].get('PROJECT_FILE_PATH') for row in rows if row.get('target') == target}
        if len(projects) > 1:
            raise ValueError('Several projects contain app target ' + target + '. Select a scheme that identifies one app.')
    if not configs:
        selected_owner = owners.get(args.target) or (next(iter(owners.values())) if len(owners) == 1 else None)
        if not selected_owner and len(targets) > 1 and not args.target:
            return {'owners': owners, 'choices': {'scheme': schemes, 'target': targets, 'destination': destinations},
                    'raw': {'listing': listing, 'settings': settings['raw']}}
        if selected_owner:
            owner_list = _call(['xcrun', 'xcodebuild', '-project', selected_owner, '-list', '-json'])
            if owner_list['status'] != 'success':
                raise RuntimeError('Could not validate owning project configurations.')
            configs = json.loads(owner_list['stdout']).get('project', {}).get('configurations', [])
        if not configs:
            raise RuntimeError('Select an app target to establish workspace configuration support.')
    if args.configuration not in configs:
        raise ValueError('Configuration is not supported by the owning project: ' + args.configuration)
    return {"owners": owners, "choices": {"scheme": schemes, "target": targets, "destination": destinations,
                        "configuration": configs},
            "raw": {"listing": listing, "destinations": destination_result["raw"], "settings": settings["raw"]}}


def _args(args, ctx, action):
    """Create a command from the resolved Build selection.
    Use the same derived-data location for Build and Clean.
    """
    selection = ctx["selection"]
    data = ctx["data_dir"]
    derived = Path(selection['derived_data']) if selection.get('derived_data') else data / "DerivedData"
    derived.mkdir(parents=True, exist_ok=True)
    architecture = ['-arch', selection['architecture']] if selection.get('architecture') else []
    return ["xcrun", "xcodebuild", *_container(ctx), "-scheme", selection["scheme"],
            "-configuration", selection["configuration"], "-destination", selection["destination"],
            "-derivedDataPath", str(derived), *architecture, action]


def clean(args, ctx):
    """Clean the selected scheme and configuration.
    Capture the complete native result for prerequisite and failure handling.
    """
    result = _call(_args(args, ctx, "clean"))
    if ctx.get("log"):
        append_log(ctx["log"], "xcodebuild Clean command", json.dumps(result["command"]))
    return result


def build(args, ctx):
    """Build without launching and preserve complete command output.
    Mark history only at the backend invocation boundary.
    """
    command = _args(args, ctx, 'build')
    ctx['mark_build']()
    result = _call(command)
    if ctx.get("log"):
        append_log(ctx["log"], "xcodebuild Build command", json.dumps(result["command"]))
    return result


def resolve_product(args, ctx):
    """Resolve the selected app executable from matching Build settings.
    Respect custom output paths and report missing products explicitly.
    """
    selection = ctx["selection"]
    command = ["xcrun", "xcodebuild", *_container(ctx), "-scheme", selection["scheme"],
               "-configuration", selection["configuration"], "-destination", selection["destination"],
               "-derivedDataPath", selection.get('derived_data') or str(ctx['data_dir'] / 'DerivedData'),
               "-showBuildSettings", "-json"]
    if selection.get('architecture'):
        command.extend(['-arch', selection['architecture']])
    result = _call(command, timeout=300)
    if result["status"] != "success":
        return result
    try:
        rows = json.loads(result["stdout"])
    except json.JSONDecodeError:
        return {"status": "failure", "raw": "Build settings response was not JSON."}
    matches = [row for row in rows if row.get("target") == selection["target"] and
               row.get("buildSettings", {}).get("PRODUCT_TYPE") == "com.apple.product-type.application" and
               row.get("buildSettings", {}).get("PLATFORM_NAME") == "macosx"]
    if len(matches) != 1:
        return {"status": "failure", "raw": f"Expected one macOS app target; found {len(matches)}."}
    settings = matches[0]["buildSettings"]
    executable = Path(settings["TARGET_BUILD_DIR"]) / settings["EXECUTABLE_PATH"]
    product = Path(settings["TARGET_BUILD_DIR"]) / settings["FULL_PRODUCT_NAME"]
    if not executable.is_file() or not os.access(executable, os.X_OK):
        return {"status": "missing", "raw": f"Selected executable is missing or not executable: {executable}",
                "product": str(product), "executable": str(executable)}
    return {"status": "success", "target": selection["target"], "product": str(product),
            "executable": str(executable), "bundle_identifier": settings.get("PRODUCT_BUNDLE_IDENTIFIER")}
