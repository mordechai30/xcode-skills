"""Explicit local SwiftPM routes. No inherited backend fallback chains."""
import json
import os
from pathlib import Path
import re
from backend import native
from lifecycle.process import capture_identity, verify_identity, traced
from lifecycle.state import atomic_json, read_json
from lifecycle.diagnostics import record


class Adapter:
    def __init__(self, base):
        """Store the independently packaged backend module.
        Follow-up debugger operations delegate to this retained backend.
        """
        # Backend module supplying its owned transport and debugger.
        self.base = base


    def discover(self, args, ctx):
        """Read executable products from the actual package manifest.
        Libraries and test targets are not runnable selections.
        """
        path = ctx['selection']['package']
        result = native._call(['swift', 'package', '--package-path', path, 'describe', '--type', 'json'], timeout=60, ctx=ctx)
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
                'owners': {p: path for p in products}}


    def native_resolve_product(self, args, ctx):
        """Resolve one executable without requiring an app bundle.
        Apple paths come from its build log; native paths come from SwiftPM.
        """
        s = ctx['selection']
        path = ctx.setdefault('runtime', {}).get('package_executable')
        if not path:
            result = native._call(['swift', 'build', '--package-path', s['package'], '--configuration', s['configuration'].lower(), '--show-bin-path'], timeout=60, ctx=ctx)
            if result['status'] != 'success':
                return result
            path = str(Path(result['stdout'].strip()) / s['target'])
            ctx['runtime']['package_executable'] = path
        return {'status': 'success' if Path(path).is_file() and os.access(path, os.X_OK) else 'missing',
                'executable': path, 'product': path, 'configuration': s['configuration']}


    def bridge(self, ctx):
        """Use Mobile's persistent Apple bridge without another controller.
        The owning Mobile server performs final transport cleanup.
        """
        from backend import apple
        self.base.use_bridge(ctx)
        return apple


    def apple_route(self, args):
        """Use Apple's debugger only for debugger-enabled Debug Run.
        Other package requests use Mobile's SwiftPM tools.
        """
        return args.operation == 'run' and args.configuration == 'Debug' and not args.no_debugger


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
        Verify the actual Apple selection before Build or Run.
        """
        if ctx.setdefault('runtime', {}).get('package_destination'):
            return
        title = ctx['selection']['destination']
        chosen = self.bridge(ctx).call(ctx, 'XcodeSwitchRunDestination', {'displayTitle': title})
        if chosen.get('activeDestinationDisplayTitle') != title:
            raise RuntimeError('Apple selected a different package destination.')
        ctx['runtime']['package_destination'] = title


    def remember(self, ctx, value):
        """Resolve the selected Apple executable from its actual linker log.
        Retain verified paths for builds that are already up to date.
        """
        log = Path(value.get('fullLogPath', ''))
        if not log.is_file():
            return
        s = ctx['selection']
        with log.open(errors='replace') as stream:
            for line in stream:
                found = re.search(r'^\s*Ld (.+?) normal(?:\s|$)', line)
                if found:
                    path = Path(found.group(1))
                    if path.name == s['target'] and path.parent.name == s['configuration']:
                        atomic_json(ctx['data_dir'] / ('package-path-' + s['configuration'] + '.json'), {'executable': str(path)})




    def build(self, args, ctx):
        """Build through Mobile's package operation without launch.
        Supply configuration through live fields or supported defaults.
        """
        values = self.mobile_values(ctx, 'swift_package_build', {'packagePath': ctx['selection']['package']})
        return self.base.tool(ctx, 'swift_package_build', values)


    def resolve_product(self, args, ctx):
        """Use Apple linker evidence for Debug or SwiftPM's bin path.
        Resolve the chosen executable rather than a directory search.
        """
        return self.apple_resolve_product(args, ctx) if self.apple_route(args) else self.native_resolve_product(args, ctx)


    def embedded_build(self, args):
        """Prepare one Build attempt around Mobile package Run.
        Only the Apple debugger route embeds compilation.
        """
        return self.apple_route(args)


    def launch(self, args, ctx, product):
        """Launch through Apple Debug or the selected executable once.
        Independently verify the returned executable and debugger absence.
        """
        if self.apple_route(args):
            return self.apple_launch(args, ctx, product)
        return native.launch(args,ctx,product)


    def stop(self, ctx):
        """Stop through Apple Debug or the owned direct child.
        No process-name termination is used.
        """
        if ctx['session']['debugger']:
            return self.base.stop(ctx)
        return native.stop(ctx)


    def close(self, ctx):
        """Close only the owned Mobile server and bridge.
        This route creates no native launcher child.
        """
        native.close(ctx)
        self.base.close(ctx)


    def debug_status(self, ctx):
        """Query the debugger retained by the selected package route.
        Release uses no debugger and is handled by process Status.
        """
        return self.bridge(ctx).debug_status(ctx)

    def debug_action(self, ctx, action, **values):
        """Use the retained Apple helper for package Debug actions.
        No fallback debugger is started.
        """
        return self.bridge(ctx).debug_action(ctx, action, **values)



    def apple_resolve_product(self, args, ctx):
        """Verify Apple's actual linker path or native Release executable.
        Missing files remain distinct from a verified product.
        """
        if not self.apple_route(args):
            return self.native_resolve_product(args, ctx)
        s = ctx['selection']
        saved = read_json(ctx['data_dir'] / ('package-path-' + s['configuration'] + '.json'), {})
        path = saved.get('executable')
        return {'status': 'success' if path and Path(path).is_file() and os.access(path, os.X_OK) else 'missing',
                'executable': path, 'product': path, 'configuration': s['configuration']}


    def apple_launch(self, args, ctx, product):
        """Launch once through LLDB, Apple, or Mobile's package Run.
        Verify the returned process against the resolved executable.
        """
        debug = args.configuration == 'Debug' and not args.no_debugger
        if self.apple_route(args):
            self.setup(ctx)
            apple = self.bridge(ctx)
            value = apple.call(ctx, 'RunProject', {'attachDebugger': debug})
            self.remember(ctx, value)
            early_product = self.resolve_product(args, ctx)
            early = capture_identity(value.get('processIdentifier')) if value.get('processIdentifier') else None
            if early and early_product.get('executable') and verify_identity(early, early_product['executable']):
                ctx['session']['app'] = early
                parent = capture_identity(early['parentPID']) if debug else None
                if parent and Path(parent['executable']).name == 'debugserver':
                    ctx['session']['dedicated'].append(parent)
                atomic_json(ctx['data_dir'] / 'session.json', ctx['session'])
            evidence = apple.call(ctx, 'GetBuildLog', {'severity':'warning'})
            self.remember(ctx, evidence)
            build = apple.build_evidence(evidence)
            pid = value.get('processIdentifier')
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


    def mobile_values(self, ctx, tool, values):
        """Supply configuration using live fields or in-memory defaults.
        Reuse unchanged defaults within this owned server connection.
        """
        connection = self.base.server(ctx)
        schema = next(item for item in connection.tools if item['name'] == tool)
        configuration = ctx['selection']['configuration']
        if 'configuration' in schema['inputSchema'].get('properties', {}):
            return values | {'configuration': configuration}
        if ctx.setdefault('runtime', {}).get('package_defaults') == configuration:
            return values
        from backend.apple import decode
        raw = connection.call('session_set_defaults', {'configuration': configuration, 'persist': False}, timeout=60)
        record(ctx, 'Package defaults', raw)
        response = decode(raw)
        if response.get('didError') or response.get('error'):
            raise RuntimeError('Mobile rejected package configuration defaults: ' + str(response))
        ctx['runtime']['package_defaults'] = configuration
        return values

