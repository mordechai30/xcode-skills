"""Check remote evidence without invoking an application backend."""
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from backend.apple import build_evidence, decode, discover_destinations, client, launch, build, ToolError
import tempfile


class AppleResultTests(unittest.TestCase):
    """Distinguish actual Build evidence from empty errors or wrapper success.
    Fixtures retain only fields relevant to the result being tested.
    """
    def test_known_build_error_remains_failure(self):
        """Preserve explicit Build failure inside a remote error envelope.
        A generic transport error must remain uncertain.
        """
        response = {'isError': True, 'raw': 'failed', 'structured': {'buildResult': 'Build failed'}}
        with patch('backend.apple.settings'), patch('backend.apple.call', side_effect=ToolError(response)):
            self.assertEqual(build(None, {})['status'], 'failure')
        with patch('backend.apple.settings'), patch('backend.apple.call', side_effect=TimeoutError('deadline')):
            self.assertEqual(build(None, {})['status'], 'uncertain')

    def test_launch_identity_saved_before_build_log_query(self):
        """Keep a verified launch record when a later query times out.
        No second launch is performed while ownership remains recorded.
        """
        from argparse import Namespace
        identity = {'pid': 200, 'parentPID': 300}
        with tempfile.TemporaryDirectory() as directory:
            ctx = {'session': {'dedicated': []}, 'data_dir': Path(directory)}
            with patch('backend.apple.settings'), \
                    patch('backend.apple.call', side_effect=[{'processIdentifier': 200}, TimeoutError('build log')]), \
                    patch('backend.apple.capture_identity', side_effect=[identity, None]), \
                    patch('backend.apple.verify_identity', return_value=True):
                with self.assertRaises(TimeoutError):
                    launch(Namespace(configuration='Debug', no_debugger=False), ctx, {'executable': '/fixture/app'})
            import json
            saved = json.loads((Path(directory) / 'session.json').read_text())
            self.assertEqual(saved['app'], identity)
            self.assertEqual(saved['launch']['processIdentifier'], 200)
    def test_empty_errors_are_not_success(self):
        """Reject an empty error array as standalone success evidence.
        The tool must supply a result or completed Build log.
        """
        self.assertEqual(build_evidence({'buildErrors': []})['status'], 'uncertain')

    def test_explicit_success_and_failure(self):
        """Use explicit Build results and actual error classifications.
        Warnings do not become errors.
        """
        self.assertEqual(build_evidence({'buildResult': 'Build succeeded', 'errors': [{'classification': 'warning'}]})['status'], 'success')
        self.assertEqual(build_evidence({'buildResult': 'Build failed'})['status'], 'failure')
        self.assertEqual(build_evidence({'buildErrors': [{'classification': 'error'}]})['status'], 'failure')

    def test_remote_error_is_not_a_successful_reply(self):
        """Reject a remote error even when stdout contains JSON.
        Preserve its raw response in the raised explanation.
        """
        with self.assertRaisesRegex(RuntimeError, 'remote failed'):
            decode({'isError': True, 'raw': 'remote failed'})

    def test_new_scheme_discovery_waits_for_xcode(self):
        """Wait for asynchronous discovery before selecting a saved copy.
        Repeated read queries must not trigger a Build or launch.
        """
        ctx = {'skill': 'fixture', 'selection': {'project': '/fixture/App.xcodeproj', 'workspace': None}, 'runtime': {}}
        responses = [{'workspaceIdentifier': 'owned'}, {'schemes': []}, {'schemes': [{'name': 'App-Release'}]},
                     {'activeSchemeName': 'App-Release'}, {'destinations': [{'displayTitle': 'My Mac',
                       'isEligible': True, 'platformIdentifier': 'com.apple.platform.macosx'}]}]
        with patch('backend.apple.configured', return_value='App-Release'), \
                patch('backend.apple.call', side_effect=responses) as call, patch('backend.apple.time.sleep'):
            result = discover_destinations(None, ctx)
        self.assertEqual(result, ['My Mac'])
        self.assertEqual([entry.args[1] for entry in call.call_args_list],
                         ['XcodeOpenWorkspace', 'XcodeListSchemes', 'XcodeListSchemes', 'XcodeSwitchScheme', 'XcodeListRunDestinations'])

    def test_closed_connection_is_not_replaced(self):
        """Reject follow-up access after owned connection cleanup.
        A retained context must not create a replacement Apple bridge.
        """
        with patch('backend.apple.MCPClient') as factory:
            with self.assertRaisesRegex(RuntimeError, 'No replacement'):
                client({'runtime': {'bridge_closed': True}})
        factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
