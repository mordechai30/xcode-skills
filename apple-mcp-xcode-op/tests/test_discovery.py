"""Discovery and scheme-copy behavior using isolated Xcode fixtures."""
from argparse import Namespace
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from backend import native


class DiscoveryTests(unittest.TestCase):
    """Test selection evidence without performing Build or Run.
    Fake command results retain the installed CLI's output shape.
    """
    def test_workspace_app_owner_validates_configuration(self):
        """Validate a workspace configuration through the selected app project.
        The settings query alone cannot establish configuration support.
        """
        args, ctx, values = self.fixture()
        ctx['selection'] = {'project': None, 'workspace': '/fixture/App.xcworkspace'}
        values[0] = {'workspace': {'schemes': ['App']}}
        values.append({'project': {'configurations': ['Release']}})
        replies = [{'status': 'success', 'stdout': json.dumps(value) if not isinstance(value, str) else value,
                    'raw': json.dumps(value) if not isinstance(value, str) else value} for value in values]
        with patch.object(native, '_call', side_effect=replies) as calls:
            with self.assertRaisesRegex(ValueError, 'not supported'):
                native.discover(args, ctx)
        self.assertEqual(calls.call_args_list[-1].args[0][2:4], ['-project', '/fixture/With Space/App.xcodeproj'])

    def test_workspace_multiple_apps_return_selection_choices(self):
        """Ask for the app target before validating its project configuration.
        No arbitrary workspace app becomes the selected product.
        """
        args, ctx, values = self.fixture()
        args.target = None
        values[0] = {'workspace': {'schemes': ['App']}}
        values[2].append({'target': 'Other', 'buildSettings': {'PRODUCT_TYPE': 'com.apple.product-type.application',
                           'PLATFORM_NAME': 'macosx', 'PROJECT_FILE_PATH': '/fixture/Other.xcodeproj'}})
        ctx['selection'] = {'project': None, 'workspace': '/fixture/App.xcworkspace'}
        replies = [{'status': 'success', 'stdout': json.dumps(value) if not isinstance(value, str) else value,
                    'raw': json.dumps(value) if not isinstance(value, str) else value} for value in values]
        with patch.object(native, '_call', side_effect=replies):
            result = native.discover(args, ctx)
        self.assertEqual(result['choices']['target'], ['App', 'Other'])
    def fixture(self, configs=None, schemes=None):
        """Create arguments and native command responses.
        Project paths with spaces stay separate arguments.
        """
        args = Namespace(configuration='Debug', scheme='App', target='App')
        ctx = {'selection': {'project': '/fixture/With Space/App.xcodeproj', 'workspace': None}}
        responses = [
            {'project': {'configurations': configs or ['Debug', 'Release'], 'schemes': schemes or ['App']}},
            'Destinations compatible with the "App" scheme:\n{ platform:macOS, arch:arm64e, id:host, name:My Mac }\nDestinations incompatible:\n{ platform:iOS, name:iPhone }',
            [{'target': 'App', 'buildSettings': {'PRODUCT_TYPE': 'com.apple.product-type.application',
                                               'PLATFORM_NAME': 'macosx', 'PROJECT_FILE_PATH': '/fixture/With Space/App.xcodeproj'}}]]
        return args, ctx, responses

    def test_destination_spacing_and_project_owner(self):
        """Discover actual compatible destinations despite whitespace differences.
        Preserve project ownership for workspace artifact placement.
        """
        args, ctx, values = self.fixture()
        replies = [{'status': 'success', 'stdout': json.dumps(v) if not isinstance(v, str) else v,
                    'raw': json.dumps(v) if not isinstance(v, str) else v} for v in values]
        with patch.object(native, '_call', side_effect=replies) as calls:
            found = native.discover(args, ctx)
        self.assertEqual(found['choices']['destination'], ['platform=macOS,id=host,arch=arm64e'])
        self.assertEqual(found['owners']['App'], '/fixture/With Space/App.xcodeproj')
        self.assertIn('/fixture/With Space/App.xcodeproj', calls.call_args_list[0].args[0])

    def test_invalid_configuration_blocks_settings_query(self):
        """Reject a configuration absent from project discovery.
        A later settings query must not grant configuration support.
        """
        args, ctx, values = self.fixture(configs=['Release'])
        reply = {'status': 'success', 'stdout': json.dumps(values[0]), 'raw': json.dumps(values[0])}
        with patch.object(native, '_call', return_value=reply) as calls:
            with self.assertRaises(RuntimeError):
                native.discover(args, ctx)
        self.assertEqual(calls.call_count, 1)


if __name__ == '__main__':
    unittest.main()
