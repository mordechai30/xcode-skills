"""Route macOS executable packages through each skill's supported backend.
Reuse the existing debugger and process lifecycle operations.
"""
import os
from pathlib import Path
import re

from backend import native
from lifecycle.process import capture_identity, verify_identity, traced
from lifecycle.state import atomic_json, read_json


from backend.package_native import Adapter as NativePackage


class Adapter(NativePackage):
    """Use Apple package Debug and the approved native Release fallback.
    All debugging uses this skill's retained Apple connection.
    """
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
        Verify the actual Apple selection before Clean, Build, or Run.
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
        for line in log.read_text(errors='replace').splitlines():
            found = re.search(r'^\s*Ld (.+?) normal(?:\s|$)', line)
            if found:
                path = Path(found.group(1))
                if path.name == s['target'] and path.parent.name == s['configuration']:
                    atomic_json(ctx['data_dir'] / ('package-path-' + s['configuration'] + '.json'), {'executable': str(path)})

    def clean(self, args, ctx):
        """Clean the selected Apple package scheme or native Release package.
        Match the route that will perform Build.
        """
        if not self.apple_route(args):
            return super().clean(args, ctx)
        self.setup(ctx)
        workspace = str(Path(ctx['selection']['package']) / '.swiftpm/xcode/package.xcworkspace')
        return native._call(['xcrun', 'xcodebuild', '-workspace', workspace, '-scheme', ctx['selection']['scheme'],
                            '-configuration', args.configuration, '-destination', 'platform=macOS', 'clean'], timeout=60, ctx=ctx)

    def build(self, args, ctx):
        """Build through Apple for Debug or SwiftPM for Release.
        Retain the actual Apple linker path for subsequent product verification.
        """
        if not self.apple_route(args):
            return super().build(args, ctx)
        self.setup(ctx)
        apple = self.bridge(ctx)
        result = apple.call(ctx, 'BuildProject')
        self.remember(ctx, result)
        return apple.build_evidence(result)

    def resolve_product(self, args, ctx):
        """Verify Apple's actual linker path or native Release executable.
        Missing files remain distinct from a verified product.
        """
        if not self.apple_route(args):
            return super().resolve_product(args, ctx)
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
            return super().launch(args, ctx, product)
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
            evidence = apple.call(ctx, 'GetBuildLog')
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

