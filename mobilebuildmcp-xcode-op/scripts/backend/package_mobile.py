"""Route macOS executable packages through each skill's supported backend.
Reuse the existing debugger and process lifecycle operations.
"""
import os
from pathlib import Path

from backend import native
from lifecycle.state import append_log
import json
from lifecycle.process import capture_identity, verify_identity, traced


from backend.package_apple import Adapter as ApplePackage
from backend.package_native import Adapter as NativePackage


class Adapter(ApplePackage):
    """Use Mobile package tools and its Apple bridge for Debug Run.
    Retain the same owned server throughout the active session.
    """
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
        if ctx.get('log'):
            append_log(ctx['log'], 'Package defaults', raw.get('raw', json.dumps(raw)))
        response = decode(raw)
        if response.get('didError') or response.get('error'):
            raise RuntimeError('Mobile rejected package configuration defaults: ' + str(response))
        ctx['runtime']['package_defaults'] = configuration
        return values

    def clean(self, args, ctx):
        """Clean through the selected Mobile package route.
        Apple Debug uses the matching native scheme Clean fallback.
        """
        if self.apple_route(args):
            return super().clean(args, ctx)
        return self.base.tool(ctx, 'swift_package_clean', {'packagePath': ctx['selection']['package']})

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
        return super().resolve_product(args, ctx) if self.apple_route(args) else NativePackage.resolve_product(self, args, ctx)

    def embedded_build(self, args):
        """Prepare one Build attempt around Mobile package Run.
        Both the Apple Debug route and SwiftPM Run embed compilation.
        """
        return True

    def launch(self, args, ctx, product):
        """Launch through Mobile's Apple Debug or package Run tool once.
        Independently verify the returned executable and debugger absence.
        """
        if self.apple_route(args):
            return super().launch(args, ctx, product)
        values = self.mobile_values(ctx, 'swift_package_run', {'packagePath': ctx['selection']['package'],
                 'executableName': ctx['selection']['target'], 'arguments': ctx['selection'].get('arguments', []), 'background': True})
        value = self.base.tool(ctx, 'swift_package_run', values)
        pid = value.get('envelope', {}).get('data', {}).get('artifacts', {}).get('processId')
        resolved = self.resolve_product(args, ctx)
        identity = capture_identity(pid) if pid else None
        verified = bool(identity and resolved.get('executable') and verify_identity(identity, resolved['executable']))
        return {'status': 'success' if verified and value['status'] == 'success' and traced(pid) is False else 'uncertain',
                'state': 'running' if verified else 'uncertain', 'app': identity if verified else None,
                'debugger': False, 'dedicated': [], 'build': value}

    def stop(self, ctx):
        """Stop through Apple Debug or a verified Mobile package PID.
        No process-name termination is used.
        """
        if ctx['session']['debugger']:
            return self.base.stop(ctx)
        app = ctx['session'].get('app')
        if not app or not verify_identity(app):
            return {'status': 'uncertain', 'message': 'Package process identity is unavailable.'}
        return self.base.tool(ctx, 'swift_package_stop', {'pid': app['pid']})

    def close(self, ctx):
        """Close only the owned Mobile server and bridge.
        This route creates no native launcher child.
        """
        self.base.close(ctx)

