"""Kill operation ordering and uncertain-parent behavior with fake backends."""
from argparse import Namespace
from pathlib import Path
import sys
import unittest
from unittest.mock import patch

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from operations.kill import execute


class Backend:
    """Record backend termination and transport cleanup.
    Fake actions do not signal real application processes.
    """
    def __init__(self, calls):
        """Use the test's ordered call list.
        This records effects across backend and fallback operations.
        """
        # Shared call sequence used to verify app-first ordering.
        self.calls = calls

    def stop(self, ctx):
        """Record the owning backend's app termination request.
        Verification and fallback remain in the operation module.
        """
        self.calls.append('backend-stop')
        return {'status': 'success'}

    def close(self, ctx):
        """Record dedicated connection cleanup after the app step.
        No shared process is represented in this fixture.
        """
        self.calls.append('close')

    def debug_action(self, ctx, action, **values):
        """Record deletion of an owned session breakpoint.
        Unlisted debugger breakpoints remain outside this fake operation.
        """
        self.calls.append((action, values['id']))
        return {'status': 'success'}


class KillTests(unittest.TestCase):
    """Verify operation ordering and no automatic unrelated-parent kill.
    Patches replace only operating-system identity and signal effects.
    """
    def test_app_before_dedicated_cleanup(self):
        """Stop the app before closing dedicated debugger processes.
        Record app and helper outcomes separately.
        """
        calls = []
        app = {'pid': 200, 'parentPID': 300}
        helper = {'pid': 300}
        ctx = {'session': {'app': app, 'dedicated': [helper]}, 'backend': Backend(calls), 'runtime': {}}
        args = Namespace(_context=ctx)
        def terminate(value):
            """Record a fake verified termination.
            PID identifies the app or dedicated fixture helper.
            """
            calls.append(value['pid'])
            return {'status': 'success'}
        with patch('operations.kill.capture_identity', return_value=None), patch('operations.kill.terminate_identity', side_effect=terminate), patch('operations.kill.save_session') as save:
            result = execute(args, Path('/fixture'))
        self.assertEqual(calls, ['backend-stop', 200, 'close', 300])
        self.assertEqual(result['status'], 'success')
        save.assert_called_once_with(ctx, None)

    def test_zombie_unrelated_parent_requires_choice(self):
        """Keep an unverified parent alive when the app is a zombie.
        Return the parent identity so the user can choose the next action.
        """
        calls = []
        ctx = {'session': {'app': {'pid': 200, 'parentPID': 300}, 'dedicated': []},
               'backend': Backend(calls), 'runtime': {}}
        with patch('operations.kill.capture_identity', return_value={'pid': 300}), patch('operations.kill.terminate_identity', return_value={'status': 'zombie'}) as signal:
            result = execute(Namespace(_context=ctx), Path('/fixture'))
        self.assertEqual(result['status'], 'needs_user_input')
        self.assertEqual(signal.call_count, 1)
        self.assertEqual(calls, ['backend-stop'])

    def test_kill_clears_recorded_session_breakpoints(self):
        """Delete recorded breakpoints before the target becomes unavailable.
        App termination still precedes all dedicated process cleanup.
        """
        calls = []
        ctx = {'session': {'app': {'pid': 200, 'parentPID': 300}, 'dedicated': [],
                          'debugger': True, 'breakpoints': [{'id': 7}, {'id': 9}]},
               'backend': Backend(calls), 'runtime': {}}
        with patch('operations.kill.capture_identity', return_value=None), \
                patch('operations.kill.terminate_identity', return_value={'status': 'success'}), \
                patch('operations.kill.save_session') as save:
            result = execute(Namespace(_context=ctx), Path('/fixture'))
        self.assertEqual(calls, [('delete_breakpoint', 7), ('delete_breakpoint', 9), 'backend-stop', 'close'])
        self.assertEqual([item['id'] for item in result['breakpoints']], [7, 9])
        self.assertEqual(result['status'], 'success')
        save.assert_called_once_with(ctx, None)


if __name__ == '__main__':
    unittest.main()
