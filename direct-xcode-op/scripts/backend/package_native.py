"""Route macOS executable packages through each skill's supported backend.
Reuse the existing debugger and process lifecycle operations.
"""
import json
import os
from pathlib import Path

from backend import native


class Adapter:
    """Use native SwiftPM for one executable package.
    Debug requests reuse the owned native LLDB connection.
    """
    def __init__(self, base):
        """Store the independently packaged backend module.
        Follow-up debugger operations delegate to this retained backend.
        """
        # Backend module supplying its owned transport and debugger.
        self.base = base

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

    def command(self, ctx, action):
        """Create one SwiftPM command using the selected package context.
        Build uses the chosen executable product and configuration.
        """
        s = ctx['selection']
        if action == 'clean':
            return ['swift', 'package', '--package-path', s['package'], 'clean']
        return ['swift', 'build', '--package-path', s['package'], '--configuration', s['configuration'].lower(),
                '--product', s['target']]

    def discover_destinations(self, args, ctx):
        """Use the current host for native package operations.
        SwiftPM does not require an Xcode destination identifier.
        """
        return ['macOS']

    def clean(self, args, ctx):
        """Clean this package without launching.
        Preserve the native command output in the attempt log.
        """
        return native._call(self.command(ctx, 'clean'), timeout=60, ctx=ctx)

    def build(self, args, ctx):
        """Build the selected executable and configuration.
        Mark history immediately before invoking SwiftPM.
        """
        ctx['mark_build']()
        return native._call(self.command(ctx, 'build'), ctx=ctx)

    def resolve_product(self, args, ctx):
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

    def embedded_build(self, args):
        """Build separately before a native package launch.
        No launch occurs inside SwiftPM Build.
        """
        return False

    def launch(self, args, ctx, product):
        """Launch through owned LLDB or directly without a debugger.
        Use the executable resolved from SwiftPM.
        """
        return native.launch(args, ctx, product)

