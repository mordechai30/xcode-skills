"""Validate Mobile domain errors and returned operation identity."""
from pathlib import Path
import sys
import unittest
from unittest.mock import Mock, patch

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from backend.mobilebuildmcp import tool, server, AppleBridge


class Server:
    """Return a configured MCP response without performing a tool operation.
    The fixture preserves structuredContent and the remote error flag.
    """
    def __init__(self, response):
        """Keep the response used by the parser test.
        Calls return it without mutation.
        """
        # Complete MCP tool response for the current case.
        self.response = response

    def call(self, name, values, before_send=None, timeout=None):
        """Return the configured response to a requested tool.
        This fixture creates no application or backend process.
        """
        if before_send:
            before_send()
        return self.response


class MobileResultTests(unittest.TestCase):
    """Exercise domain evidence beyond the MCP wrapper result.
    Schema versions remain variable while operation identity is checked.
    """
    def test_bridge_timeout_never_exceeds_sixty_seconds(self):
        """Cap requested bridge waits and respect smaller live-schema limits.
        Rejected fake operations create no app or debugger session.
        """
        bridge = AppleBridge.__new__(AppleBridge)
        bridge.ctx = {}
        bridge.tools = [{'name': 'RunProject', 'inputSchema': {'properties': {}}}]
        for maximum, expected in ((120000, 60000), (10000, 10000)):
            connection = Mock()
            connection.tools = [{'name': 'xcode_ide_call_tool', 'inputSchema': {'properties': {'timeoutMs': {'maximum': maximum}}}}]
            with patch('backend.mobilebuildmcp.server', return_value=connection), \
                    patch('backend.mobilebuildmcp.tool', return_value={'status': 'failure'}) as called:
                with self.assertRaises(RuntimeError):
                    bridge.call('RunProject', {}, timeout=180)
            self.assertEqual(called.call_args.args[2]['timeoutMs'], expected)

    def test_transport_caps_override_and_initial_timeout(self):
        """Apply the sixty-second cap at the actual MCP transport.
        Use a disposable stdio fixture instead of a live Mobile server.
        """
        from backend.apple_mcp import MCPClient
        with MCPClient(command=[sys.executable, str(Path(__file__).with_name('fake_mcp.py')), 'ok'], timeout=180) as connection:
            self.assertEqual(connection.timeout, 60)
            with patch.object(connection, 'request', side_effect=lambda method, values: {'structuredContent': {'timeout': connection.timeout}}):
                response = connection.call('Echo', {'value': 'x'}, timeout=300)
            self.assertEqual(response['structured']['timeout'], 60)
    def result(self, schema='mobilebuildmcp.output.build-result', status='SUCCEEDED', error=False):
        """Call the parser with an isolated server response.
        The future-version value checks that versions are not hard-coded.
        """
        envelope = {'schema': schema, 'schemaVersion': 'future-compatible', 'didError': error,
                    'error': 'compiler failed' if error else None,
                    'data': {'summary': {'status': status}}}
        response = {'structured': envelope, 'isError': error, 'raw': 'fixture'}
        invoked = Mock()
        ctx = {'runtime': {'mobile_server': Server(response)}, 'selection': {'scheme': 'App', 'configuration': 'Debug'},
               'mark_build': invoked}
        result = tool(ctx, 'build_macos', {})
        invoked.assert_called_once_with()
        return result

    def test_domain_failure_survives_wrapper(self):
        """Return actual Build failure to the Clean procedure.
        An MCP isError response must not bypass failed-Build handling.
        """
        self.assertEqual(self.result(status='FAILED', error=True)['status'], 'failure')

    def test_compatible_schema_names_are_not_hard_coded(self):
        """Use actual operation fields rather than a reference schema-name table.
        A compatible renamed schema must not reject verified outcome fields.
        """
        self.assertEqual(self.result(schema='future.operation')['status'], 'success')

    def test_operation_fields_and_variable_versions(self):
        """Require actual successful operation fields.
        Compatible returned versions are recorded without a fixed version list.
        """
        self.assertEqual(self.result()['status'], 'success')
        self.assertEqual(self.result(status='UNKNOWN')['status'], 'uncertain')

    def test_closed_server_is_not_replaced(self):
        """Reject follow-up access after the owned server closes.
        Failed cleanup must not create another backend connection.
        """
        with patch('backend.mobilebuildmcp.MCPClient') as factory:
            with self.assertRaisesRegex(RuntimeError, 'No replacement'):
                server({'runtime': {'mobile_closed': True}})
        factory.assert_not_called()


if __name__ == '__main__':
    unittest.main()
