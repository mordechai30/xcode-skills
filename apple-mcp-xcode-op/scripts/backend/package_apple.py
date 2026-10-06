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


    def command(self, ctx):
        """Create one SwiftPM command using the selected package context.
        Build uses the chosen executable product and configuration.
        """
        s = ctx['selection']
        return ['swift', 'build', '--package-path', s['package'], '--configuration', s['configuration'].lower(),
                '--product', s['target']]




    def native_build(self, args, ctx):
        """Build the selected executable and configuration.
        Surface compiler diagnostics without retaining transcripts.
        """
        return native._call(self.command(ctx), ctx=ctx)


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


    def native_launch(self, args, ctx, product):
        """Launch through owned LLDB or directly without a debugger.
        Use the executable resolved from SwiftPM.
        """
        return native.launch(args, ctx, product)


    def bridge(self, ctx):
        """Use the Apple backend owned by this package.
        Follow-up debugger commands share the same connection.
        """
        return self.base


    def apple_route(self, args):
        """Select Apple for Debug and native SwiftPM for Release.
        Generated schemes do not expose Release configuration selection.
        """
        return args.configuration == 'Debug' 


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
        """Build through Apple for Debug or SwiftPM for Release.
        Retain the actual Apple linker path for subsequent product verification.
        """
        if not self.apple_route(args):
            return self.native_build(args, ctx)
        self.setup(ctx)
        apple = self.bridge(ctx)
        result = apple.call(ctx, 'BuildProject')
        self.remember(ctx, result)
        evidence = apple.build_evidence(result)
        reported = apple.call(ctx, 'GetBuildLog', {'severity':'warning'})
        self.remember(ctx, reported)
        diagnostic_evidence = apple.build_evidence(reported)
        return diagnostic_evidence if diagnostic_evidence['status'] == 'failure' else evidence


    def resolve_product(self, args, ctx):
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


    def embedded_build(self, args):
        """Apply Build preparation once around Apple Debug RunProject.
        Release builds separately through native SwiftPM.
        """
        return self.apple_route(args)


    def launch(self, args, ctx, product):
        """Launch once through LLDB, Apple, or Mobile's package Run.
        Verify the returned process against the resolved executable.
        """
        if not self.apple_route(args):
            return self.native_launch(args, ctx, product)
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


    def stop(self, ctx):
        """Terminate using the route that launched the package.
        Kill independently verifies the app and dedicated processes.
        """
        return native.stop(ctx) if ctx['selection']['configuration'] == 'Release' else self.base.stop(ctx)


    def close(self, ctx):
        """Close native Release children and the owned Apple transport.
        Shared IDE services remain untouched.
        """
        if ctx['selection']['configuration'] == 'Release':
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
