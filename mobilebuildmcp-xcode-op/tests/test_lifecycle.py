"""Behavioral checks for Build history and breakpoint ownership."""
import argparse
from datetime import datetime, timedelta
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import sys

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from lifecycle.state import clean_required, new_log, previous_build
from operations.build import prepare, invoked, finish
from operations.continue_session import execute as resume
from operations.debugger_command import execute as inspect


class FakeBackend:
    """Provide observable operation results without launching an app.
    Calls expose order and breakpoint deletion to the tests.
    """
    def __init__(self):
        """Create default successful Clean and paused debugger state.
        Each test changes only the result relevant to its case.
        """
        # Ordered operation calls used to check lifecycle effects.
        self.calls = []
        # Configurable prerequisite Clean outcome.
        self.clean_status = 'success'
        # Current debugger snapshot used for Continue preconditions.
        self.state = {'status': 'success', 'state': 'paused', 'stops': [{'breakpoints': [7]}]}

    def clean(self, args, ctx):
        """Record a Clean attempt and return its configured outcome.
        No Build is implied by this method.
        """
        self.calls.append('clean')
        return {'status': self.clean_status}

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
    Temporary logs and session records are removed after each case.
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

    def test_failed_clean_does_not_advance_history(self):
        """Check failed preparation and mandatory successful next Clean.
        Preparation logs must not count as invoked Build attempts.
        """
        self.adapter.clean_status = 'failure'
        self.assertEqual(prepare(self.args, self.ctx)['status'], 'needs_user_input')
        self.assertIsNone(previous_build(self.folder, 'fixture', 'Debug'))
        self.adapter.clean_status = 'success'
        self.assertEqual(prepare(self.args, self.ctx)['status'], 'success')
        invoked(self.ctx)
        self.assertEqual(previous_build(self.folder, 'fixture', 'Debug'), self.ctx['log'])
        self.assertEqual(self.adapter.calls, ['clean', 'clean'])

    def test_one_hour_boundary(self):
        """Check the strict age boundary using filename time.
        File modification time is irrelevant to the rule.
        """
        now = datetime.now().astimezone().replace(microsecond=0)
        name = 'log-fixture-Debug-' + (now - timedelta(hours=1)).strftime('%y-%m-%d-%H-%M-%S') + '.txt'
        self.assertFalse(clean_required(self.folder / name, now))
        self.assertTrue(clean_required(self.folder / name, now + timedelta(seconds=1)))

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
        self.assertEqual(result['response']['output'], 'tick = 4')
        self.assertEqual(result['current']['state'], 'paused')

    def test_continue_removes_responsible_only(self):
        """Resume an owned breakpoint stop.
        Unrelated breakpoints must survive.
        """
        result = resume(self.args, self.folder)
        self.assertEqual(result['removed'], [7])
        self.assertEqual(self.ctx['session']['breakpoints'], [{'id': 9}])
        self.assertEqual(self.adapter.calls[0], ('delete_breakpoint', {'id': 7}))

    def test_manual_pause_preserves_breakpoints(self):
        """Resume a manual pause without deleting breakpoints.
        The fake stop has no breakpoint cause.
        """
        self.adapter.state['stops'] = [{'breakpoints': []}]
        self.assertEqual(resume(self.args, self.folder)['removed'], [])
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

    def test_failed_build_cleans_once_and_waits(self):
        """Clean a failed invoked Build without another Build attempt.
        The failed invocation still advances Build history.
        """
        prepare(self.args, self.ctx)
        invoked(self.ctx)
        self.adapter.calls.clear()
        value = finish(self.args, self.ctx, {'status': 'failure', 'raw': 'compiler failed'})
        self.assertEqual(value['status'], 'needs_user_input')
        self.assertEqual(self.adapter.calls, ['clean'])
        self.assertEqual(previous_build(self.folder, 'fixture', 'Debug'), self.ctx['log'])

    def test_ambiguous_breakpoint_does_not_delete(self):
        """Ask when several owned breakpoints caused a stop.
        No arbitrary breakpoint may be deleted or resumed.
        """
        self.adapter.state['stops'] = [{'breakpoints': [7, 9]}]
        self.assertEqual(resume(self.args, self.folder)['status'], 'needs_user_input')
        self.assertEqual(self.adapter.calls, [])

    def test_project_history_is_separate(self):
        """Keep two projects in one containing folder separate.
        A sibling project's Build must not reset this project's timer.
        """
        self.ctx['selection']['owner_project'] = '/fixture/One.xcodeproj'
        prepare(self.args, self.ctx)
        invoked(self.ctx)
        self.assertIsNone(previous_build(self.folder, 'fixture', 'Debug', {'owner_project': '/fixture/Two.xcodeproj'}))


if __name__ == '__main__':
    unittest.main()
