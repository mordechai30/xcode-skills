"""Test actual stdio transport behavior against disposable fixtures."""
from pathlib import Path
import sys
import unittest

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from backend.apple_mcp import MCPClient


class TransportTests(unittest.TestCase):
    """Exercise protocol handling without contacting Xcode.
    Every fixture server is owned and reaped by its test.
    """
    def client(self, mode='ok'):
        """Start one disposable fixture server.
        Use the same Python interpreter as the test runner.
        """
        value = MCPClient(command=[sys.executable, str(Path(__file__).with_name('fake_mcp.py')), mode], timeout=.3)
        self.addCleanup(value.close)
        return value

    def test_pagination_notification_and_ids(self):
        """Read all schema pages and ignore notifications as replies.
        Tool results must match the current request ID.
        """
        client = self.client()
        self.assertEqual([item['name'] for item in client.tools], ['Echo'])
        result = client.call('Echo', {'value': 'hello'})
        self.assertEqual(result['structured'], {'value': 'hello'})
        self.assertFalse(hasattr(client, 'messages'))

    def test_unknown_and_missing_fields(self):
        """Reject unsupported arguments before a tool call.
        Required fields are taken from the live fixture schema.
        """
        client = self.client()
        with self.assertRaises(RuntimeError):
            client.call('Echo', {'wrong': 'x'})
        with self.assertRaises(RuntimeError):
            client.call('Echo', {})

    def test_live_validation_precedes_tool_request(self):
        """Reject invalid fields before issuing a tool request.
        A valid request is sent once without history callbacks.
        """
        from unittest.mock import patch
        client = self.client()
        with patch.object(client, 'request', wraps=client.request) as request:
            with self.assertRaises(RuntimeError):
                client.call('Echo', {'wrong': 'x'})
            request.assert_not_called()
            client.call('Echo', {'value': 'x'})
            request.assert_called_once()

    def test_remote_error(self):
        """Surface remote JSON-RPC errors.
        A transport reply is not sufficient success evidence.
        """
        with self.assertRaisesRegex(RuntimeError, 'fixture error'):
            self.client('error').call('Echo', {'value': 'x'})

    def test_eof(self):
        """Report EOF before a matching response.
        The connection is not recreated automatically.
        """
        with self.assertRaisesRegex(RuntimeError, 'closed stdout'):
            self.client('eof').call('Echo', {'value': 'x'})

    def test_deadline(self):
        """Bound a request that never receives a reply.
        Cleanup terminates and reaps the fixture afterward.
        """
        with self.assertRaises(TimeoutError):
            self.client('timeout').call('Echo', {'value': 'x'})


if __name__ == '__main__':
    unittest.main()
