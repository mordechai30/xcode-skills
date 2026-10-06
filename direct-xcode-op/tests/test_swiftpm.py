"""Check package selection and backend routing without live processes.
Use manifest and log fixtures rather than production project defaults.
"""
from argparse import Namespace
import json
import importlib.util
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from backend.package_selected import Adapter
from backend import native
from operations.run import execute


class PackageTests(unittest.TestCase):
    """Verify package operations preserve the selected executable and lifecycle.
    All backend calls are fake and no app is launched.
    """
    def test_manifest_selection_excludes_libraries(self):
        """Offer executable products and exclude library products.
        A selected executable resolves both target and scheme choices.
        """
        data = {'products': [{'name': 'One', 'type': {'executable': None}},
                             {'name': 'Lib', 'type': {'library': ['automatic']}},
                             {'name': 'Two', 'type': {'executable': None}}]}
        ctx = {'selection': {'package': '/fixture/With Space', 'target': 'Two', 'scheme': None}}
        with patch.object(native, '_call', return_value={'status': 'success', 'stdout': json.dumps(data)}):
            result = Adapter(native).discover(Namespace(), ctx)
        self.assertEqual(result['choices']['target'], ['Two'])
        self.assertEqual(result['choices']['scheme'], ['Two'])

    def test_native_build_marks_invocation_and_does_not_launch(self):
        """Build exactly the selected product and configuration.
        Keep a package path containing spaces as one command argument.
        """
        ctx = {'selection': {'package': '/fixture/With Space', 'target': 'App', 'configuration': 'Release'}}
        with patch.object(native, '_call', return_value={'status': 'success'}) as call:
            Adapter(native).build(Namespace(configuration='Release'), ctx)
        self.assertEqual(call.call_args.args[0], ['swift', 'build', '--package-path', '/fixture/With Space', '--configuration', 'release', '--product', 'App'])

    @unittest.skip("Route is not installed in this skill.")
    def test_apple_release_uses_authorized_native_fallback(self):
        """Use native SwiftPM for Apple Release packages.
        Keep Apple MCP for the verified Debug route.
        """
        adapter = Adapter(SimpleNamespace(__name__='backend.apple'))
        self.assertFalse(adapter.apple_route(Namespace(configuration='Release', operation='run', no_debugger=False)))
        self.assertTrue(adapter.apple_route(Namespace(configuration='Debug', operation='run', no_debugger=False)))

    @unittest.skip("Route is not installed in this skill.")
    def test_mobile_run_is_embedded_in_only_for_debugger(self):
        """Prepare one Build attempt around Mobile package Run.
        Debug uses the Apple bridge; Release builds then launches directly.
        """
        adapter = Adapter(SimpleNamespace(__name__='backend.mobilebuildmcp'))
        for configuration in ('Debug', 'Release'):
            self.assertTrue(adapter.embedded_build(Namespace(configuration=configuration, operation='run', no_debugger=False)))

    @unittest.skip("Route is not installed in this skill.")
    def test_apple_destination_mismatch_blocks_operation(self):
        """Check Apple's actual destination selection before execution.
        A different destination must not permit Build or launch.
        """
        adapter = Adapter(SimpleNamespace(__name__='backend.apple'))
        bridge = Mock()
        bridge.call.return_value = {'activeDestinationDisplayTitle': 'Other Mac'}
        with patch.object(adapter, 'bridge', return_value=bridge):
            with self.assertRaises(RuntimeError):
                adapter.setup({'selection': {'destination': 'My Mac'}})

    @unittest.skipUnless(importlib.util.find_spec('backend.apple'), 'Remote adapter is not packaged in the native skill.')
    @unittest.skip("Route is not installed in this skill.")
    def test_mobile_configuration_uses_live_session_defaults(self):
        """Set configuration through defaults when MCP omits that field.
        Do not forward CLI-only arguments to the live tool schema.
        """
        connection = Mock()
        connection.tools = [{'name': 'swift_package_build', 'inputSchema': {'properties': {'packagePath': {}}}}]
        connection.call.return_value = {'structured': {'didError': False}}
        base = SimpleNamespace(__name__='backend.mobilebuildmcp', server=Mock(return_value=connection))
        values = Adapter(base).mobile_values({'selection': {'configuration': 'Release'}}, 'swift_package_build', {'packagePath': '/package'})
        self.assertNotIn('configuration', values)
        connection.call.assert_called_once_with('session_set_defaults', {'configuration': 'Release', 'persist': False}, timeout=60)

    @unittest.skip("Route is not installed in this skill.")
    def test_apple_link_path_must_match_product_and_configuration(self):
        """Retain only the selected executable's actual linker path.
        Reject another product and another configuration.
        """
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder)
            log = path / 'build.txt'
            log.write_text('Ld /custom/Release/App normal\nLd /custom/Debug/Other normal\nLd /custom/Debug/App normal\n')
            ctx = {'selection': {'target': 'App', 'configuration': 'Debug'}, 'data_dir': path}
            Adapter(native).remember(ctx, {'fullLogPath': str(log)})
            self.assertEqual(json.loads((path / 'package-path-Debug.json').read_text())['executable'], '/custom/Debug/App')

    def test_run_builds_even_when_product_exists(self):
        """Apply the user's simple rebuild-on-Run choice.
        Existing products must not require reusable-history evidence.
        """
        backend = Mock()
        backend.resolve_product.return_value = {'status': 'success', 'executable': '/fixture/App'}
        backend.embedded_build.return_value = False
        backend.select_run_route = None
        backend.launch.return_value = {'status': 'success', 'state': 'not_launched'}
        ctx = {'backend': backend, 'discovery': True, 'session': None, 'runtime': {}, 'data_dir': Path('/fixture')}
        args = Namespace(configuration='Debug')
        with patch('operations.run.context', return_value=ctx), \
             patch('operations.run.perform', return_value={'status': 'success'}) as build, \
             patch('operations.run.finish', return_value={'status': 'success'}), \
             patch('operations.run.resolve_selection', return_value={'status': 'success'}), patch('operations.run.pending'), patch('operations.run.save_session'):
            result = execute(args, Path('/fixture'))
        build.assert_called_once()
        self.assertEqual(result['status'], 'success')


if __name__ == '__main__':
    unittest.main()
