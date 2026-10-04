"""MobileBuildMCP macOS operations on one retained MCP server."""
import json
import os
from pathlib import Path
import plistlib
import re

from backend import apple, native
from backend.apple_mcp import MCPClient
from lifecycle.process import capture_identity, verify_identity, traced, matching_processes
from lifecycle.state import append_log
from lifecycle.schemes import launch_arguments


def server(ctx):
    """Create one owned MobileBuildMCP server with relevant workflows.
    The supported MCP lifetime remains active during paused sessions.
    """
    if ctx['runtime'].get('mobile_closed'):
        raise RuntimeError('The owned Mobile connection is closed. No replacement connection will be created.')
    if 'mobile_server' not in ctx['runtime']:
        env = dict(os.environ, MOBILEBUILDMCP_ENABLED_WORKFLOWS='macos,xcode-ide,swift-package', MOBILEBUILDMCP_MCP_IDLE_TIMEOUT_MS='0')
        ctx['runtime']['mobile_server'] = MCPClient(command=['mobilebuildmcp', 'mcp'], env=env, cwd=ctx['data_dir'], timeout=60)
    return ctx['runtime']['mobile_server']


def tool(ctx, name, values, before_send=None):
    """Invoke a current tool and validate its structured result envelope.
    Preserve schema identity, version, domain errors, and raw responses.
    """
    connection = server(ctx)
    marker = before_send or (ctx.get('mark_build') if name in ('build_macos', 'swift_package_build', 'swift_package_run') else None)
    response = connection.call(name, values, before_send=marker,
                               timeout=60 if name in ('build_macos', 'clean', 'xcode_ide_call_tool', 'swift_package_build', 'swift_package_run', 'swift_package_clean') else 15)
    if ctx.get('log'):
        append_log(ctx['log'], name, json.dumps({'arguments': values, 'response': response}))
    data = response.get('structured')
    if not isinstance(data, dict):
        if response.get('isError'):
            return {'status': 'failure', 'raw': response}
        data = apple.decode(response)
    expected = {'build_macos': 'mobilebuildmcp.output.build-result', 'clean': 'mobilebuildmcp.output.build-result',
                'swift_package_build': 'mobilebuildmcp.output.build-result', 'swift_package_clean': 'mobilebuildmcp.output.build-result',
                'swift_package_run': 'mobilebuildmcp.output.build-run-result', 'swift_package_stop': 'mobilebuildmcp.output.stop-result',
                'get_mac_app_path': 'mobilebuildmcp.output.app-path',
                'launch_mac_app': 'mobilebuildmcp.output.launch-result', 'stop_mac_app': 'mobilebuildmcp.output.stop-result',
                'xcode_ide_list_tools': 'mobilebuildmcp.output.xcode-bridge-tool-list',
                'xcode_ide_call_tool': 'mobilebuildmcp.output.xcode-bridge-call-result'}
    if not isinstance(data.get('schemaVersion'), str) or not data['schemaVersion']:
        raise RuntimeError('MobileBuildMCP result omitted schema identity or version: ' + response['raw'])
    if name in expected and data.get('schema') != expected[name]:
        return {'status': 'uncertain', 'message': 'Returned schema does not match the requested operation.', 'raw': response}
    if response.get('isError') or data.get('didError') or data.get('error'):
        return {'status': 'failure', 'raw': response, 'envelope': data}
    payload = data.get('data', {})
    if name in ('build_macos', 'clean', 'get_mac_app_path', 'launch_mac_app', 'stop_mac_app', 'swift_package_build', 'swift_package_clean', 'swift_package_run', 'swift_package_stop') and payload.get('summary', {}).get('status') != 'SUCCEEDED':
        return {'status': 'failure' if payload.get('summary', {}).get('status') == 'FAILED' else 'uncertain',
                'raw': response, 'envelope': data}
    artifacts = payload.get('artifacts', {})
    for field in ('scheme', 'configuration'):
        if artifacts.get(field) and artifacts[field] != ctx['selection'][field]:
            return {'status': 'uncertain', 'message': 'Artifact selection differs from the request.', 'raw': response}
    if name == 'xcode_ide_call_tool' and payload.get('succeeded') is not True:
        return {'status': 'failure', 'raw': response, 'envelope': data}
    return {'status': 'success', 'raw': response, 'envelope': data}


class AppleBridge:
    """Use MobileBuildMCP's existing Apple bridge.
    This adapter does not start a separate debugger or Apple transport.
    """
    def __init__(self, ctx):
        """Discover current remote schemas through the retained Mobile server.
        Response artifacts supply the full remote contracts.
        """
        # Runtime context containing the one owned MCP connection.
        self.ctx = ctx
        listed = tool(ctx, 'xcode_ide_list_tools', {})
        if listed['status'] != 'success':
            raise RuntimeError(str(listed))
        envelope = listed['envelope']
        artifact = self.artifact(envelope)
        if artifact.get('operation') != 'list-tools':
            raise RuntimeError('Tool-list artifact does not describe discovery.')
        # Live remote tools used to validate each forwarded request.
        self.tools = artifact['response']['tools']

    def artifact(self, envelope):
        """Read an explicitly returned bridge artifact.
        Missing or malformed artifacts cannot establish remote success.
        """
        data = envelope.get('data', envelope)
        path = data.get('artifacts', {}).get('rawResponseJsonPath')
        if not path:
            raise RuntimeError('MobileBuildMCP omitted the raw bridge artifact.')
        return json.loads(Path(path).expanduser().read_text())

    def call(self, name, arguments, before_send=None, timeout=None):
        """Validate and forward one remote Apple request.
        Verify artifact tool and arguments against the request.
        """
        schema = next((item for item in self.tools if item['name'] == name), None)
        if not schema or set(arguments) - set(schema['inputSchema'].get('properties', {})):
            raise RuntimeError('Unsupported live Apple bridge request: ' + name)
        missing = set(schema['inputSchema'].get('required', [])) - set(arguments)
        if missing:
            raise RuntimeError('Missing required Apple bridge fields: ' + ', '.join(sorted(missing)))
        deadline = int(min(timeout or 60, 60) * 1000)
        outer = next(item for item in server(self.ctx).tools if item['name'] == 'xcode_ide_call_tool')
        limit = outer.get('inputSchema', {}).get('properties', {}).get('timeoutMs', {}).get('maximum')
        if isinstance(limit, (int, float)):
            deadline = min(deadline, int(limit))
        result = tool(self.ctx, 'xcode_ide_call_tool', {'remoteTool': name, 'arguments': json.dumps(arguments), 'timeoutMs': deadline}, before_send=before_send)
        if result['status'] != 'success':
            raise RuntimeError(str(result))
        artifact = self.artifact(result['envelope'])
        if artifact.get('remoteTool') != name or artifact.get('arguments') != arguments:
            raise RuntimeError('Bridge artifact does not match the requested tool and arguments.')
        response = artifact['response']
        return {'isError': response.get('isError', False), 'structured': response.get('structuredContent'),
                'content': response.get('content', []), 'raw': json.dumps(response)}

    def close(self):
        """Leave server closure to the owning Mobile adapter.
        The Apple gateway has no separate transport to terminate.
        """
        return None


def discover(args, ctx):
    """Discover app ownership and supported macOS destinations.
    Mobile architecture selection is derived from supported native destinations.
    """
    return native.discover(args, ctx)


def discover_destinations(args, ctx):
    """Use live Apple destinations only for the Debug Run route.
    Standalone macOS Build and product-reuse routes use native discovery.
    """
    if embedded_build(args):
        use_bridge(ctx)
        return apple.discover_destinations(args, ctx)
    return None


def request_values(args, ctx):
    """Supply the selected app's Build context to macOS tools.
    Architecture is passed once through the supported arch input.
    """
    selected = ctx['selection']
    value = {'scheme': selected['scheme'], 'configuration': selected['configuration'],
             'derivedDataPath': selected.get('derived_data') or str(ctx['data_dir'] / 'DerivedData')}
    value['projectPath' if selected['project'] else 'workspacePath'] = selected['project'] or selected['workspace']
    match = re.search(r'arch=([^,]+)', selected['destination'])
    arch = selected.get('architecture') or (match.group(1) if match else None)
    if arch:
        value['arch'] = arch
    return value


def macos_context(args, ctx):
    """Set supported in-memory defaults on this owned MCP server.
    Do not persist defaults into the application project.
    """
    if ctx['runtime'].get('macos_defaults'):
        return
    value = request_values(args, ctx) | {'persist': False, 'preferXcodebuild': True}
    response = server(ctx).call('session_set_defaults', value)
    result = apple.decode(response)
    if result.get('didError') or result.get('error'):
        raise RuntimeError('MobileBuildMCP rejected selected defaults: ' + response['raw'])
    if ctx.get('log'):
        append_log(ctx['log'], 'Mobile macOS defaults', json.dumps({'arguments': value, 'response': response}))
    ctx['runtime']['macos_defaults'] = value


def clean(args, ctx):
    """Clean through the macOS backend with matching Build context.
    Debug embedded builds use the matching Apple context fallback.
    """
    if ctx['runtime'].get('workspace'):
        return apple.clean(args, ctx)
    macos_context(args, ctx)
    return tool(ctx, 'clean', {'platform': 'macOS'})


def build(args, ctx):
    """Build through MobileBuildMCP without launch.
    Product evidence is verified by the Build operation afterward.
    """
    macos_context(args, ctx)
    return tool(ctx, 'build_macos', {})


def use_bridge(ctx):
    """Provide the Mobile-owned Apple bridge to shared adapter logic.
    The same connection is reused by every debugger operation.
    """
    ctx['bridge_factory'] = lambda: AppleBridge(ctx)


def embedded_build(args):
    """Identify the Apple RunProject route used for macOS Debug.
    Release and disabled Debug use product-reuse launch.
    """
    return args.operation == 'run' and args.configuration == 'Debug' and not args.no_debugger


def resolve_product(args, ctx):
    """Verify a returned app against selected native Build settings.
    Debug bridge products use actual Apple settings after setup.
    """
    if embedded_build(args):
        use_bridge(ctx)
        return apple.resolve_product(args, ctx)
    expected = native.resolve_product(args, ctx)
    if expected['status'] != 'success':
        return expected
    macos_context(args, ctx)
    result = tool(ctx, 'get_mac_app_path', {})
    if result['status'] != 'success':
        return result
    data = result['envelope'].get('data', result['envelope'])
    path = data.get('artifacts', {}).get('appPath') or data.get('appPath')
    if not path or os.path.realpath(path) != os.path.realpath(expected['product']):
        return {'status': 'uncertain', 'message': 'Returned app path does not match selected Build settings.', 'response': result}
    return expected | {'response': result}


def launch(args, ctx, product):
    """Launch Debug through the retained bridge or Release through macOS Launch.
    Verify PID independently of the launcher's name-based lookup.
    """
    if embedded_build(args):
        use_bridge(ctx)
        return apple.launch(args, ctx, product)
    existing = matching_processes(product['executable'])
    if existing:
        return {'status': 'needs_user_input', 'state': 'not_launched', 'debugger': False,
                'message': 'The selected app is already running outside this skill. The installed Launch uses open and can reuse it. No external app session will be adopted.',
                'processes': existing}
    result = tool(ctx, 'launch_mac_app', {'appPath': product['product'], 'launchArgs': launch_arguments(ctx['selection'])})
    if result['status'] != 'success':
        return result
    data = result['envelope'].get('data', result['envelope'])
    pid = data.get('artifacts', {}).get('processId')
    identity = capture_identity(pid) if isinstance(pid, int) else None
    if not identity or not verify_identity(identity, product['executable']):
        return {'status': 'uncertain', 'state': 'uncertain', 'app': None, 'debugger': False,
                'dedicated': [], 'message': 'Launch PID does not identify the selected executable.', 'launch': result}
    detached = traced(pid) is False
    return {'status': 'success' if detached else 'uncertain', 'state': 'running', 'app': identity, 'debugger': False,
            'attachment_verified': detached, 'dedicated': [], 'launch': result}


def debug_status(ctx):
    """Refresh current state through the Mobile Apple bridge.
    No simulator debugger interface is used.
    """
    return apple.debug_status(ctx)


def debug_action(ctx, action, **values):
    """Forward an explicit operation through the retained Mobile bridge.
    Shared rules remain in the independently packaged operation modules.
    """
    return apple.debug_action(ctx, action, **values)


def stop(ctx):
    """Stop through Apple for Debug or a verified PID for direct launch.
    Broad process-name termination is never requested.
    """
    if ctx['session']['debugger']:
        return apple.stop(ctx)
    app = ctx['session'].get('app')
    if not app or not verify_identity(app):
        return {'status': 'uncertain', 'message': 'App identity is absent or no longer matches.'}
    return tool(ctx, 'stop_mac_app', {'processId': app['pid']})


def close(ctx):
    """Close and reap only the skill-owned Mobile MCP server.
    Shared Xcode services remain running.
    """
    ctx['runtime']['bridge_closed'] = True
    ctx['runtime']['mobile_closed'] = True
    ctx['runtime'].pop('bridge', None)
    connection = ctx['runtime'].pop('mobile_server', None)
    if connection:
        connection.close()
