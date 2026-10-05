"""Apple operation adapter using the skill's retained bridge connection."""
import json
import os
from pathlib import Path
import re
import time

from backend import native
from backend.apple_mcp import MCPClient
from lifecycle.process import capture_identity, verify_identity, traced
from lifecycle.schemes import configured
from lifecycle.state import append_log, atomic_json


def discover(args, ctx):
    """Discover container ownership with native settings before connection setup.
    Live Apple discovery later verifies the actual scheme and destination.
    """
    return native.discover(args, ctx)


def client(ctx):
    """Return the retained Apple connection created by this skill.
    MobileBuildMCP supplies its own persistent bridge client here.
    """
    if ctx['runtime'].get('bridge_closed'):
        raise RuntimeError('The owned Apple connection is closed. No replacement connection will be created.')
    if 'bridge' not in ctx['runtime']:
        factory = ctx.get('bridge_factory', MCPClient)
        ctx['runtime']['bridge'] = factory()
    return ctx['runtime']['bridge']


class ToolError(RuntimeError):
    """Retain an Apple tool error's actual result envelope.
    Build handling can use explicit failure evidence without guessing from text.
    """
    def __init__(self, response):
        """Save the full response and its raw diagnostic text.
        The original envelope remains available to Build classification.
        """
        # Original remote result used to distinguish failure from uncertainty.
        self.response = response
        super().__init__(response['raw'])


def decode(value):
    """Extract structured Apple results without losing raw responses.
    Text JSON is accepted when structuredContent is absent.
    """
    if value.get('isError'):
        raise ToolError(value)
    data = value.get('structured')
    if data is None:
        for part in value.get('content', []):
            if part.get('type') == 'text':
                try:
                    data = json.loads(part['text'])
                    break
                except json.JSONDecodeError:
                    continue
    if not isinstance(data, dict):
        raise RuntimeError('Apple result has no usable structured evidence: ' + value['raw'])
    return data


def call(ctx, name, arguments=None):
    """Invoke one live-schema tool on the retained workspace connection.
    Requests and complete responses are appended to the operation log.
    """
    arguments = dict(arguments or {})
    if name != 'XcodeOpenWorkspace' and ctx['runtime'].get('workspace'):
        arguments['workspaceIdentifier'] = ctx['runtime']['workspace']
    connection = client(ctx)
    marker = ctx.get('mark_build') if name in ('BuildProject', 'RunProject') else None
    try:
        value = connection.call(name, arguments, before_send=marker,
                                timeout=60 if name in ('BuildProject', 'RunProject') else 15)
    except (RuntimeError, OSError, TimeoutError) as error:
        if ctx.get('log'):
            append_log(ctx['log'], name, json.dumps({'arguments': arguments, 'error': str(error)}))
        raise
    evidence = name + ' ' + json.dumps(arguments) + '\n' + value['raw']
    if ctx.get('log'):
        append_log(ctx['log'], 'Backend response', evidence)
    else:
        ctx.setdefault('evidence', []).append(evidence)
    return decode(value)


def discover_destinations(args, ctx):
    """Open the selected container and verify scheme and destination selection.
    No existing debugger session is adopted.
    """
    selection = ctx['selection']
    scheme = configured(selection, ctx['skill'])
    opened = call(ctx, 'XcodeOpenWorkspace', {'path': selection['workspace'] or selection['project']})
    ctx['runtime']['workspace'] = opened['workspaceIdentifier']
    listed = call(ctx, 'XcodeListSchemes')
    deadline = time.monotonic() + 5
    while not any(item.get('name') == scheme for item in listed.get('schemes', [])):
        if time.monotonic() >= deadline:
            raise RuntimeError('Apple backend has not discovered the selected scheme: ' + scheme)
        time.sleep(.2)
        listed = call(ctx, 'XcodeListSchemes')
    switched = call(ctx, 'XcodeSwitchScheme', {'schemeName': scheme})
    if switched.get('activeSchemeName') != scheme:
        raise RuntimeError('Apple backend selected a different scheme.')
    selection['scheme'] = scheme
    destinations = call(ctx, 'XcodeListRunDestinations')
    candidates = [item for item in destinations.get('destinations', [])
                  if item.get('isEligible') and 'macos' in item.get('platformIdentifier', '').lower()]
    ctx['runtime']['apple_destinations'] = candidates
    return [item['displayTitle'] for item in candidates]


def setup(ctx):
    """Verify the selected actual Apple destination before Build or Run.
    A generic destination is not substituted with a device silently.
    """
    if ctx['runtime'].get('apple_destination'):
        return
    if not ctx['runtime'].get('workspace'):
        raise RuntimeError('Apple workspace discovery has not completed.')
    title = ctx['selection']['destination']
    candidates = [item for item in ctx['runtime']['apple_destinations'] if item['displayTitle'] == title]
    if len(candidates) != 1:
        raise ValueError('Select an actual returned Apple destination title.')
    chosen = call(ctx, 'XcodeSwitchRunDestination', {'displayTitle': title})
    if chosen.get('activeDestinationDisplayTitle') != title:
        raise RuntimeError('Apple selected a different run destination.')
    ctx['runtime']['apple_destination'] = title
    item = candidates[0]
    ctx['runtime']['native_destination'] = 'platform=macOS' + (',arch=' + item['architecture'] if not item.get('isGenericDevice') else '')


def settings(ctx):
    """Read the selected target's actual Apple Build context.
    Configuration mismatch prevents Build, Clean, and product claims.
    """
    setup(ctx)
    if ctx['runtime'].get('apple_settings'):
        return ctx['runtime']['apple_settings']
    result = call(ctx, 'GetTargetBuildSettings', {'targetName': ctx['selection']['target']})
    rows = result['buildSettings']
    if rows and all('macroName' in row for row in rows):
        macros = {row['macroName']: row.get('evaluatedValue', row.get('value')) for row in rows}
        if macros.get('CONFIGURATION') and macros['CONFIGURATION'] != ctx['selection']['configuration']:
            raise RuntimeError('Existing scheme uses ' + str(macros.get('CONFIGURATION')) + '; requested ' + ctx['selection']['configuration'] + '. Select a matching scheme.')
        if not macros.get('OBJROOT') or not macros.get('SYMROOT'):
            raise RuntimeError('Apple settings omitted the actual Build roots needed for native Clean.')
        selection = ctx['selection']
        command = ['xcrun', 'xcodebuild', *native._container(ctx), '-scheme', selection['scheme'],
                   '-configuration', selection['configuration'], '-destination', ctx['runtime']['native_destination'],
                   'OBJROOT=' + macros['OBJROOT'], 'SYMROOT=' + macros['SYMROOT'], '-showBuildSettings', '-json']
        if selection.get('generated_scheme'):
            index = command.index('-configuration')
            del command[index:index + 2]
        resolved = native._call(command, timeout=60, ctx=ctx)
        if resolved['status'] != 'success':
            raise RuntimeError('Computed Apple Build paths could not be established: ' + resolved['raw'])
        matches = [row['buildSettings'] for row in json.loads(resolved['stdout']) if row.get('target') == selection['target']]
    else:
        matches = [row.get('buildSettings', row) for row in rows]
    matches = [row for row in matches if row.get('PRODUCT_TYPE') == 'com.apple.product-type.application'
               and row.get('CONFIGURATION') == ctx['selection']['configuration']]
    if len(matches) != 1:
        raise RuntimeError('Apple build settings do not establish exactly one app in the selected configuration.')
    ctx['runtime']['apple_settings'] = matches[0]
    return matches[0]


def resolve_product(args, ctx):
    """Verify the app resolved from the current Apple build settings.
    Missing products are distinguished from configuration uncertainty.
    """
    values = settings(ctx)
    executable = Path(values['TARGET_BUILD_DIR']) / values['EXECUTABLE_PATH']
    product = Path(values['TARGET_BUILD_DIR']) / values['FULL_PRODUCT_NAME']
    return {'status': 'success' if executable.is_file() and os.access(executable, os.X_OK) else 'missing',
            'executable': str(executable), 'product': str(product), 'configuration': values['CONFIGURATION']}


def clean(args, ctx):
    """Clean with native xcodebuild using the actual Apple Build paths.
    An unavailable context blocks Clean instead of substituting a location.
    """
    values = settings(ctx)
    selection = ctx['selection']
    command = ['xcrun', 'xcodebuild', *native._container(ctx), '-scheme', selection['scheme'],
               '-configuration', selection['configuration'], '-destination', ctx['runtime']['native_destination']]
    for key in ('SYMROOT', 'OBJROOT', 'CONFIGURATION_BUILD_DIR'):
        if key not in values:
            raise RuntimeError('Apple Clean context is missing ' + key)
        command.append(key + '=' + values[key])
    return native._call(command + ['clean'], ctx=ctx)


def build_evidence(value):
    """Classify explicit build evidence and preserve uncertainty.
    Empty error arrays alone are insufficient success evidence.
    """
    errors = value.get('errors', value.get('buildErrors', []))
    if any(item.get('classification', '').lower() == 'error' for item in errors):
        return {'status': 'failure', 'raw': value}
    text = value.get('buildResult', '').lower()
    if 'fail' in text:
        return {'status': 'failure', 'raw': value}
    if 'succeed' in text or 'success' in text:
        return {'status': 'success', 'raw': value}
    path = value.get('fullLogPath')
    if path and Path(path).is_file():
        log = Path(path).read_text(errors='replace')
        if '** BUILD FAILED **' in log:
            return {'status': 'failure', 'raw': value}
        if '** BUILD SUCCEEDED **' in log:
            return {'status': 'success', 'raw': value}
    return {'status': 'uncertain', 'raw': value}


def build(args, ctx):
    """Build through Apple without launch.
    Live configuration is verified before the request.
    """
    settings(ctx)
    try:
        return build_evidence(call(ctx, 'BuildProject'))
    except ToolError as error:
        value = error.response.get('structured')
        evidence = build_evidence(value) if isinstance(value, dict) else {'status': 'uncertain'}
        return evidence | {'raw': error.response}
    except (RuntimeError, OSError, TimeoutError) as error:
        return {'status': 'uncertain', 'message': str(error)}


def embedded_build(args):
    """Identify Apple's unavoidable build during RunProject.
    Run preparation applies once before this call.
    """
    return True


def launch(args, ctx, product):
    """Build and launch once with explicit debugger selection.
    Return Build and launch outcomes as separate evidence.
    """
    settings(ctx)
    debug = args.configuration == 'Debug' and not args.no_debugger
    try:
        value = call(ctx, 'RunProject', {'attachDebugger': debug})
    except ToolError as error:
        value = error.response.get('structured')
        evidence = build_evidence(value) if isinstance(value, dict) else {'status': 'uncertain'}
        return {'status': evidence['status'], 'state': 'uncertain', 'build': evidence,
                'debugger': debug, 'launch': error.response}
    if ctx.get('session'):
        pid = value.get('processIdentifier')
        early = capture_identity(pid) if pid else None
        if early and product.get('executable') and verify_identity(early, product['executable']):
            ctx['session']['app'] = early
            parent = capture_identity(early['parentPID']) if debug else None
            if parent and Path(parent['executable']).name == 'debugserver':
                ctx['session']['dedicated'].append(parent)
        atomic_json(ctx['data_dir'] / 'session.json', ctx['session'])
    direct_evidence = build_evidence(value)
    if direct_evidence['status'] == 'failure':
        return {'status': 'failure', 'state': 'not_launched', 'build': direct_evidence, 'launch': value,
                'debugger': debug, 'app': ctx.get('session', {}).get('app')}
    evidence = build_evidence(call(ctx, 'GetBuildLog'))
    resolved = resolve_product(args, ctx)
    pid = value.get('processIdentifier')
    identity = capture_identity(pid) if pid else None
    verified = bool(identity and resolved.get('executable') and verify_identity(identity, resolved['executable']))
    dedicated = []
    if verified and debug:
        parent = capture_identity(identity['parentPID'])
        if parent and Path(parent['executable']).name == 'debugserver':
            dedicated.append(parent)
    if verified and ctx.get('session'):
        ctx['session']['app'] = identity
        ctx['session']['state'] = 'launch_verifying'
        ctx['session']['dedicated'].extend(dedicated)
        atomic_json(ctx['data_dir'] / 'session.json', ctx['session'])
    state = debug_status(ctx) if debug else None
    exited = bool(pid and not identity and 'launched successfully' in value.get('runResult', '').lower())
    result = {'status': 'success' if verified and evidence['status'] == 'success' else 'uncertain',
              'state': state.get('state') if state else 'running' if verified else 'exited' if exited else 'uncertain',
              'debugger': debug, 'app': identity if verified else None, 'dedicated': dedicated, 'build': evidence, 'launch': value,
              'attachment_verified': traced(pid) == debug if verified else False}
    if not result['attachment_verified']:
        result['status'] = 'uncertain'
    if debug and verified and state.get('pid') != pid:
        result['status'] = 'uncertain'
    if debug and state.get('state') == 'exited' and state.get('pid') == pid and evidence['status'] == 'success':
        result['status'] = 'success'
        result['message'] = 'App exited before live executable and attachment verification.'
    elif not verified and exited:
        result['message'] = 'Returned app PID is no longer present; launch identity could not be verified while alive.'
    if 'fail' in value.get('runResult', '').lower() and evidence['status'] == 'success':
        result['status'] = 'failure'
        result['message'] = 'Build succeeded; backend reported launch failure.'
    return result


def debug_action(ctx, action, **values):
    """Send an operation through InvokeDebuggerCommand without another controller.
    SB queries return structured state and preserve all raw bridge output.
    """
    if action == 'command':
        response = call(ctx, 'InvokeDebuggerCommand', {'command': values['command'], 'timeout': 2})
        return {'status': 'uncertain' if response['isWaitingForMore'] else 'success', 'response': response}
    script = Path(__file__).with_name('lldb_controller.py')
    request = json.dumps({'action': action, **values})
    code = ('import importlib.util,json,lldb; '
            f's=importlib.util.spec_from_file_location("skill_ops",{str(script)!r}); '
            'm=importlib.util.module_from_spec(s); s.loader.exec_module(m); '
            f'print("SKILL_RESULT="+json.dumps(m.handle(lldb.debugger,json.loads({request!r}),{{}})))')
    response = call(ctx, 'InvokeDebuggerCommand', {'command': 'script ' + code, 'timeout': 2})
    output = response['output']
    for line in reversed(output.splitlines()):
        if line.startswith('SKILL_RESULT='):
            return json.loads(line[len('SKILL_RESULT='):])
    return {'status': 'uncertain', 'message': 'Debugger response has no completed result.', 'response': response}


def debug_status(ctx):
    """Query current process state through the retained bridge.
    Report partial or lost connection evidence without reattaching.
    """
    return debug_action(ctx, 'status')


def stop(ctx):
    """Terminate the app through its owning Apple workspace.
    Process disappearance is checked by the Kill operation.
    """
    return {'status': 'success', 'raw': call(ctx, 'StopProject')}


def close(ctx):
    """Close only the skill-owned bridge connection.
    The shared IDE is never terminated by transport cleanup.
    """
    ctx['runtime']['bridge_closed'] = True
    connection = ctx['runtime'].pop('bridge', None)
    if connection:
        connection.close()
