"""Route macOS executable packages through each skill's supported backend.
Reuse the existing debugger and process lifecycle operations.
"""
import json
import os
from pathlib import Path
import re

from backend import native
from lifecycle.process import capture_identity, verify_identity, traced
from lifecycle.state import atomic_json, read_json


class Adapter:
    """Add package discovery and executable operations to one backend.
    Delegate debugger requests to its existing retained connection.
    """
    def __init__(self, base):
        """Store the independently packaged backend module.
        Its name selects native, Apple, or Mobile package routes.
        """
        # Backend module supplying its owned transport and debugger.
        self.base = base
        # Stable backend name, independent of the installed package path.
        self.kind = base.__name__.rsplit('.', 1)[-1]

    def __getattr__(self, name):
        """Expose unchanged backend operations to lifecycle modules.
        Package-specific operations are defined directly on this adapter.
        """
        return getattr(self.base, name)

    def discover(self, args, ctx):
        """Read executable products from the actual package manifest.
        Libraries and test targets are not runnable selections.
        """
        path = ctx['selection']['package']
        result = native._call(['swift', 'package', '--package-path', path, 'describe', '--type', 'json'], timeout=60)
        if result['status'] != 'success':
            raise RuntimeError(result['raw'])
        manifest = json.loads(result['stdout'])
        products = [p['name'] for p in manifest.get('products', []) if 'executable' in p.get('type', {})]
        chosen = ctx['selection'].get('target') or ctx['selection'].get('scheme')
        if chosen in products:
            products = [chosen]
        if ctx['selection'].get('target') and ctx['selection'].get('scheme') and ctx['selection']['target'] != ctx['selection']['scheme']:
            raise ValueError('Package scheme and executable product must identify the same product.')
        return {'choices': {'scheme': products, 'target': products, 'destination': ['macOS']},
                'owners': {p: path for p in products}, 'raw': result}

    def bridge(self, ctx):
        """Choose the existing Apple connection for package Debug.
        Mobile supplies its existing proxy, not another debugger controller.
        """
        from backend import apple
        if self.kind == 'mobilebuildmcp':
            self.base.use_bridge(ctx)
        return apple

    def apple_route(self, args):
        """Identify package requests routed through Apple's scheme tools.
        Native and Mobile debugger-free requests use SwiftPM routes.
        """
        return (self.kind == 'apple' and args.configuration == 'Debug') or (self.kind == 'mobilebuildmcp' and args.operation == 'run' and args.configuration == 'Debug' and not args.no_debugger)

    def discover_destinations(self, args, ctx):
        """Open the package directory and select its executable scheme.
        Native SwiftPM uses the current host and no Xcode destination.
        """
        if not self.apple_route(args):
            return ['macOS']
        if getattr(args, 'arguments', []):
            raise ValueError('Apple package Run has no launch-argument input. Use native Run or saved package scheme arguments.')
        apple = self.bridge(ctx)
        opened = apple.call(ctx, 'XcodeOpenWorkspace', {'path': ctx['selection']['package']})
        ctx['runtime']['workspace'] = opened['workspaceIdentifier']
        listed = apple.call(ctx, 'XcodeListSchemes')
        name = ctx['selection']['target']
        if name not in [item['name'] for item in listed['schemes']]:
            raise ValueError('The package executable scheme is unavailable: ' + name)
        apple.call(ctx, 'XcodeSwitchScheme', {'schemeName': name})
        destinations = apple.call(ctx, 'XcodeListRunDestinations')
        return [item['displayTitle'] for item in destinations['destinations']
                if item.get('isEligible') and 'macos' in item.get('platformIdentifier', '').lower()]

    def setup(self, ctx):
        """Select the destination that discovery and the user resolved.
        Verify the actual Apple selection before Clean, Build, or Run.
        """
        title = ctx['selection']['destination']
        chosen = self.bridge(ctx).call(ctx, 'XcodeSwitchRunDestination', {'displayTitle': title})
        if chosen.get('activeDestinationDisplayTitle') != title:
            raise RuntimeError('Apple selected a different package destination.')

    def command(self, ctx, action):
        """Create one SwiftPM command using the selected package context.
        Build uses the chosen executable product and configuration.
        """
        s = ctx['selection']
        if action == 'clean':
            return ['swift', 'package', '--package-path', s['package'], 'clean']
        return ['swift', 'build', '--package-path', s['package'], '--configuration', s['configuration'].lower(),
                '--product', s['target']]

    def mobile_values(self, ctx, tool, values):
        """Supply configuration using the live Mobile MCP contract.
        Session-aware schemas can expose configuration only through defaults.
        """
        connection = self.base.server(ctx)
        schema = next(item for item in connection.tools if item['name'] == tool)
        configuration = ctx['selection']['configuration']
        if 'configuration' in schema['inputSchema'].get('properties', {}):
            return values | {'configuration': configuration}
        from backend.apple import decode
        response = decode(connection.call('session_set_defaults', {'configuration': configuration, 'persist': False}, timeout=60))
        if response.get('didError') or response.get('error'):
            raise RuntimeError('Mobile rejected package configuration defaults: ' + str(response))
        return values

    def clean(self, args, ctx):
        """Clean the selected package through its build route.
        Apple uses the generated package workspace and selected scheme.
        """
        if self.apple_route(args):
            self.setup(ctx)
            workspace = str(Path(ctx['selection']['package']) / '.swiftpm/xcode/package.xcworkspace')
            return native._call(['xcrun', 'xcodebuild', '-workspace', workspace, '-scheme', ctx['selection']['scheme'],
                                 '-configuration', args.configuration, '-destination', 'platform=macOS', 'clean'], timeout=60)
        if self.kind == 'mobilebuildmcp':
            return self.base.tool(ctx, 'swift_package_clean', {'packagePath': ctx['selection']['package']})
        return native._call(self.command(ctx, 'clean'), timeout=60)

    def remember(self, ctx, value):
        """Resolve the selected Apple executable from its actual linker log.
        Retain verified paths for builds that are already up to date.
        """
        log = Path(value.get('fullLogPath', ''))
        if not log.is_file():
            return
        s = ctx['selection']
        for line in log.read_text(errors='replace').splitlines():
            found = re.search(r'^\s*Ld (.+?) normal(?:\s|$)', line)
            if found:
                path = Path(found.group(1))
                if path.name == s['target'] and path.parent.name == s['configuration']:
                    atomic_json(ctx['data_dir'] / ('package-path-' + s['configuration'] + '.json'), {'executable': str(path)})

    def build(self, args, ctx):
        """Build the selected package without launching it.
        Retain backend evidence and mark actual invocation for logs.
        """
        if self.apple_route(args):
            self.setup(ctx)
            apple = self.bridge(ctx)
            result = apple.call(ctx, 'BuildProject')
            self.remember(ctx, result)
            return apple.build_evidence(result)
        if self.kind == 'mobilebuildmcp':
            values = self.mobile_values(ctx, 'swift_package_build', {'packagePath': ctx['selection']['package']})
            return self.base.tool(ctx, 'swift_package_build', values)
        ctx['mark_build']()
        return native._call(self.command(ctx, 'build'))

    def resolve_product(self, args, ctx):
        """Resolve one executable without requiring an app bundle.
        Apple paths come from its build log; native paths come from SwiftPM.
        """
        s = ctx['selection']
        if self.apple_route(args):
            saved = read_json(ctx['data_dir'] / ('package-path-' + s['configuration'] + '.json'), {})
            path = saved.get('executable')
            if not path:
                return {'status': 'missing', 'executable': None, 'product': None}
        else:
            result = native._call(['swift', 'build', '--package-path', s['package'], '--configuration', s['configuration'].lower(), '--show-bin-path'], timeout=60)
            if result['status'] != 'success':
                return result
            path = str(Path(result['stdout'].strip()) / s['target'])
        return {'status': 'success' if Path(path).is_file() and os.access(path, os.X_OK) else 'missing',
                'executable': path, 'product': path, 'configuration': s['configuration']}

    def embedded_build(self, args):
        """Identify routes that build inside the launch request.
        Run preparation occurs once before Apple or Mobile package Run.
        """
        return self.apple_route(args) or self.kind == 'mobilebuildmcp'

    def launch(self, args, ctx, product):
        """Launch once through LLDB, Apple, or Mobile's package Run.
        Verify the returned process against the resolved executable.
        """
        if self.kind == 'native' or self.kind == 'apple' and not self.apple_route(args):
            return native.launch(args, ctx, product)
        debug = args.configuration == 'Debug' and not args.no_debugger
        if self.apple_route(args):
            self.setup(ctx)
            apple = self.bridge(ctx)
            value = apple.call(ctx, 'RunProject', {'attachDebugger': debug})
            ctx['session']['launch'] = value
            atomic_json(ctx['data_dir'] / 'session.json', ctx['session'])
            self.remember(ctx, value)
            early_product = self.resolve_product(args, ctx)
            early = capture_identity(value.get('processIdentifier')) if value.get('processIdentifier') else None
            if early and early_product.get('executable') and verify_identity(early, early_product['executable']):
                ctx['session']['app'] = early
                parent = capture_identity(early['parentPID']) if debug else None
                if parent and Path(parent['executable']).name == 'debugserver':
                    ctx['session']['dedicated'].append(parent)
                atomic_json(ctx['data_dir'] / 'session.json', ctx['session'])
            evidence = apple.call(ctx, 'GetBuildLog')
            self.remember(ctx, evidence)
            build = apple.build_evidence(evidence)
            pid = value.get('processIdentifier')
        else:
            values = self.mobile_values(ctx, 'swift_package_run', {'packagePath': ctx['selection']['package'],
                                'executableName': ctx['selection']['target'],
                                'arguments': ctx['selection'].get('arguments', []), 'background': True})
            value = self.base.tool(ctx, 'swift_package_run', values)
            build = value
            pid = value.get('envelope', {}).get('data', {}).get('artifacts', {}).get('processId')
        resolved = self.resolve_product(args, ctx)
        identity = capture_identity(pid) if pid else None
        verified = bool(identity and resolved.get('executable') and verify_identity(identity, resolved['executable']))
        dedicated = []
        if verified and debug:
            parent = capture_identity(identity['parentPID'])
            if parent and Path(parent['executable']).name == 'debugserver':
                dedicated.append(parent)
        state = self.base.debug_status(ctx) if debug and verified else None
        return {'status': 'success' if verified and build['status'] == 'success' and traced(pid) == debug else 'uncertain',
                'state': state.get('state') if state else 'running' if verified else 'uncertain',
                'app': identity if verified else None, 'debugger': debug, 'attachment_verified': verified and traced(pid) == debug,
                'dedicated': dedicated, 'build': build, 'launch': value}

    def stop(self, ctx):
        """Use the route that owns this package process.
        The Kill operation independently verifies disappearance and parents.
        """
        if self.kind == 'mobilebuildmcp' and not ctx['session']['debugger']:
            app = ctx['session'].get('app')
            if not app or not verify_identity(app):
                return {'status': 'uncertain', 'message': 'Package process identity is unavailable.'}
            return self.base.tool(ctx, 'swift_package_stop', {'pid': app['pid']})
        if self.kind == 'apple' and ctx['selection']['configuration'] == 'Release':
            return native.stop(ctx)
        return self.base.stop(ctx)

    def close(self, ctx):
        """Close only owned native children and backend connections.
        Release fallback children require native reaping as well.
        """
        if self.kind == 'apple' and ctx['selection']['configuration'] == 'Release':
            native.close(ctx)
        self.base.close(ctx)
