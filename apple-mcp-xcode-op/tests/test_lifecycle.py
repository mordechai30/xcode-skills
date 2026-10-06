"""Behavioral checks for breakpoint ownership."""
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from operations.build import finish
from operations.continue_session import execute as resume
from operations.debugger_command import execute as inspect


class FakeBackend:
    """Provide observable operation results without launching an app.
    Calls expose order and breakpoint deletion to the tests.
    """
    def __init__(self):
        """Create a paused debugger state.
        Each test changes only the result relevant to its case.
        """
        # Ordered operation calls used to check lifecycle effects.
        self.calls = []
        # Current debugger snapshot used for Continue preconditions.
        self.state = {'status': 'success', 'state': 'paused', 'stops': [{'breakpoints': [7]}]}


    def debug_status(self, ctx):
        """Return current debugger state.
        Continue changes it to running for verification.
        """
        return self.state

    def debug_action(self, ctx, action, **values):
        """Record explicit debugger mutations.
        Only Continue changes the fake execution state.
        """
        self.calls.append((action, values))
        if action == 'continue':
            self.state = {'status': 'success', 'state': 'running', 'stops': []}
        return {'status': 'success'}


class LifecycleTests(unittest.TestCase):
    """Test behavior independently of backend protocols.
    Temporary session records are removed after each case.
    """
    def setUp(self):
        """Create one isolated project context.
        No fixture project path enters production code.
        """
        # Isolated artifact storage removed after each test.
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        # Project folder used by fake lifecycle records.
        self.folder = Path(self.temp.name)
        # Observable backend with configurable operation results.
        self.adapter = FakeBackend()
        # Retained session supplied to operation modules.
        self.ctx = {'data_dir': self.folder, 'root': self.folder, 'skill': 'fixture',
                    'selection': {'configuration': 'Debug'}, 'discovery': {}, 'backend': self.adapter,
                    'runtime': {}, 'active_path': self.folder / '.active.json',
                    'session': {'debugger': True, 'breakpoints': [{'id': 7}, {'id': 9}]}}
        # User inputs for the current operation test.
        self.args = argparse.Namespace(configuration='Debug', keep_breakpoint=False, _context=self.ctx)



    def test_partial_inspection_queries_state_without_repeating(self):
        """Keep partial output and refresh the same debugger's state.
        The original command executes once, even when completion is uncertain.
        """
        self.args.command = 'frame variable tick'
        partial = {'status': 'uncertain', 'response': {'isWaitingForMore': True, 'output': 'tick = 4'}}
        with patch.object(self.adapter, 'debug_action', return_value=partial) as action, \
                patch.object(self.adapter, 'debug_status', return_value=self.adapter.state) as state:
            result = inspect(self.args, self.folder)
        action.assert_called_once_with(self.ctx, 'command', command='frame variable tick')
        self.assertEqual(state.call_count, 2)
        self.assertEqual(result['output'], 'tick = 4')
        self.assertEqual(result['state'], 'paused')

    def test_continue_removes_responsible_only(self):
        """Resume an owned breakpoint stop.
        Unrelated breakpoints must survive.
        """
        result = resume(self.args, self.folder)
        self.assertEqual(result['removed'], 7)
        self.assertEqual(self.ctx['session']['breakpoints'], [{'id': 9}])
        self.assertEqual(self.adapter.calls[0], ('delete_breakpoint', {'id': 7}))

    def test_manual_pause_preserves_breakpoints(self):
        """Resume a manual pause without deleting breakpoints.
        The fake stop has no breakpoint cause.
        """
        self.adapter.state['stops'] = [{'breakpoints': []}]
        self.assertEqual(resume(self.args, self.folder).get('removed'), None)
        self.assertEqual(self.adapter.calls, [('continue', {})])

    def test_retention_watches_without_deletion(self):
        """Resume with explicit retention and watching.
        The responsible breakpoint remains owned by the session.
        """
        self.args.keep_breakpoint = True
        self.assertTrue(resume(self.args, self.folder)['watch'])
        self.assertEqual(self.adapter.calls, [('continue', {})])

    def test_continue_running_is_rejected(self):
        """Reject Continue on running execution.
        No debugger mutation may occur.
        """
        self.adapter.state['state'] = 'running'
        self.assertEqual(resume(self.args, self.folder)['status'], 'needs_user_input')
        self.assertEqual(self.adapter.calls, [])


    def test_ambiguous_breakpoint_does_not_delete(self):
        """Ask when several owned breakpoints caused a stop.
        No arbitrary breakpoint may be deleted or resumed.
        """
        self.adapter.state['stops'] = [{'breakpoints': [7, 9]}]
        self.assertEqual(resume(self.args, self.folder)['status'], 'needs_user_input')
        self.assertEqual(self.adapter.calls, [])



if __name__ == '__main__':
    unittest.main()
