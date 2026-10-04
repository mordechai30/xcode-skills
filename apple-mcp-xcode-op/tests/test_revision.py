"""Exercise state persistence, durable output, and failed breakpoint cleanup."""
from argparse import Namespace
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from lifecycle.output import collect
from operations.common import observe
from operations.kill import execute, recover
from operations.set_breakpoint import execute as set_breakpoint
from lifecycle.state import atomic_json, new_log


class RevisionTests(unittest.TestCase):
    """Check revised outcomes with disposable records and fake backends.
    No live debugger or app process is created by these tests.
    """
    def test_same_second_log_waits_without_overwriting(self):
        """Advance to the next filename second after a collision.
        Preserve the first log's bytes and the exact filename format.
        """
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            start = datetime.now().astimezone().replace(microsecond=0)
            first = folder / ('log-fixture-Debug-' + start.strftime('%y-%m-%d-%H-%M-%S') + '.txt')
            first.write_text('preserved')
            with patch('lifecycle.state.datetime') as clock, patch('lifecycle.state.time.sleep'):
                clock.now.side_effect = [start, start + timedelta(seconds=1)]
                second, _ = new_log(folder, 'fixture', 'Debug')
            self.assertNotEqual(first, second)
            self.assertEqual(first.read_text(), 'preserved')
            self.assertEqual(second.name, 'log-fixture-Debug-' + (start + timedelta(seconds=1)).strftime('%y-%m-%d-%H-%M-%S') + '.txt')
    def test_durable_output_appends_only_new_bytes(self):
        """Retain app output after artifact removal.
        Repeated collection must not duplicate earlier output.
        """
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            output = folder / 'app-output.txt'
            log = folder / 'log.txt'
            ctx = {'log': log, 'data_dir': folder, 'runtime': {}}
            output.write_text('hello\n')
            collect(ctx)
            collect(ctx)
            output.write_text('hello\nworld\n')
            collect(ctx)
            output.unlink()
            self.assertEqual(log.read_text().count('hello'), 1)
            self.assertEqual(log.read_text().count('world'), 1)

    def test_resolution_is_not_a_hit(self):
        """Record actual paused breakpoint causes only.
        A later unrelated pause must preserve the earlier hit record.
        """
        ctx = {'session': {'breakpoints': [{'id': 7}, {'id': 9}]}}
        with patch('operations.common.save_session'):
            observe(ctx, {'status': 'success', 'state': 'running'})
            self.assertNotIn('hit', ctx['session']['breakpoints'][0])
            observe(ctx, {'status': 'success', 'state': 'paused', 'stops': [{'breakpoints': [7]}]})
        self.assertTrue(ctx['session']['breakpoints'][0]['hit'])
        self.assertNotIn('hit', ctx['session']['breakpoints'][1])

    def test_pending_and_relocated_breakpoints_keep_source_evidence(self):
        """Keep pending breakpoints and debugger-selected relocated lines.
        Neither creation result claims an actual hit.
        """
        for resolved, locations in ((0, []), (1, [{'line': 122, 'resolved': True}])):
            backend = Mock()
            backend.debug_action.return_value = {'status': 'success', 'id': 7, 'resolved': resolved, 'locations': locations}
            ctx = {'backend': backend, 'session': {'breakpoints': []}}
            args = Namespace(file=Path('/fixture/main.cpp'), line=120)
            with patch('operations.set_breakpoint.debug_context', return_value=(ctx, {'state': 'running'})), \
                    patch('operations.set_breakpoint.save_session'):
                result = set_breakpoint(args, Path('/fixture'))
            self.assertEqual(ctx['session']['breakpoints'][0]['line'], 120)
            self.assertEqual(ctx['session']['breakpoints'][0]['locations'], locations)
            self.assertEqual(result['status'], 'success' if resolved else 'needs_user_input')

    def test_failed_breakpoint_deletion_releases_cleaned_context_with_warning(self):
        """Complete process cleanup despite unavailable breakpoint deletion.
        Preserve the warning instead of claiming breakpoint removal.
        """
        backend = Mock()
        backend.debug_action.side_effect = RuntimeError('connection lost')
        backend.stop.return_value = {'status': 'failure'}
        ctx = {'backend': backend, 'session': {'app': {'pid': 200, 'parentPID': 300},
               'debugger': True, 'breakpoints': [{'id': 7}], 'dedicated': []}, 'runtime': {}}
        with patch('operations.kill.capture_identity', return_value=None), \
                patch('operations.kill.terminate_identity', return_value={'status': 'success'}), \
                patch('operations.kill.save_session') as save:
            result = execute(Namespace(_context=ctx), Path('/fixture'))
        self.assertEqual(result['status'], 'success')
        self.assertIn('may remain', result['warning'])
        save.assert_called_once_with(ctx, None)

    def test_recovery_accepts_verified_runtime_zombie_parent(self):
        """Treat the recorded owned runtime as a dedicated parent.
        Lost breakpoint cleanup remains a separate warning.
        """
        with tempfile.TemporaryDirectory() as directory:
            folder = Path(directory)
            session = {'app': {'pid': 200, 'parentPID': 300}, 'dedicated': [], 'breakpoints': [{'id': 7}]}
            atomic_json(folder / 'session.json', session)
            locator = {'data_dir': str(folder), 'runtime_identity': {'pid': 300}}
            calls = []
            def terminate(identity):
                """Record cleanup order without sending signals.
                The first app result represents a zombie pending parent reap.
                """
                calls.append(identity['pid'])
                return {'status': 'zombie' if identity['pid'] == 200 else 'success'}
            with patch('operations.kill.capture_identity', side_effect=[{'pid': 300}, None, None]), \
                    patch('operations.kill.verify_identity', return_value=True), \
                    patch('operations.kill.terminate_identity', side_effect=terminate):
                result = recover(folder, locator)
            self.assertEqual(calls, [200, 300])
            self.assertEqual(result['status'], 'success')
            self.assertIn('may remain', result['warning'])
