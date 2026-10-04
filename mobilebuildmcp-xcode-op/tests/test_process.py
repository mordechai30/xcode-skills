"""Exercise verified process termination with disposable child processes."""
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from lifecycle.process import capture_identity, terminate_identity, verify_identity


class ProcessTests(unittest.TestCase):
    """Check actual signals and stale identity rejection.
    Tests own and reap each disposable child.
    """
    def child(self):
        """Start a sleeping Python child and register cleanup.
        This process is never shared with another session.
        """
        process = subprocess.Popen([sys.executable, '-c', 'import time; print("ready", flush=True); time.sleep(60)'],
                                   stdout=subprocess.PIPE, text=True)
        self.assertEqual(process.stdout.readline().strip(), 'ready')
        self.addCleanup(self.reap, process)
        return process

    def reap(self, process):
        """Terminate and reap a disposable fixture if it remains alive.
        Only the directly owned Popen handle is used.
        """
        if process.poll() is None:
            process.kill()
        process.wait(timeout=5)
        process.stdout.close()

    def test_matching_identity_can_be_terminated(self):
        """Signal a freshly verified owned child.
        A short timeout allows a zombie result until the test parent reaps it.
        """
        process = self.child()
        identity = capture_identity(process.pid)
        self.assertTrue(verify_identity(identity))
        value = terminate_identity(identity, timeout=.5)
        self.assertIn(value['status'], ('success', 'zombie'))
        process.wait(timeout=5)
        self.assertIsNone(capture_identity(process.pid))

    def test_reused_identity_blocks_signals(self):
        """Reject a record whose start identity differs from the live child.
        The live process must remain running.
        """
        process = self.child()
        identity = capture_identity(process.pid) | {'start': 'different start'}
        self.assertEqual(terminate_identity(identity)['status'], 'failure')
        self.assertIsNone(process.poll())

    def test_parent_is_protected(self):
        """Reject termination of the test runner itself.
        Caller ancestors remain protected regardless of saved identity.
        """
        import os
        self.assertEqual(terminate_identity(capture_identity(os.getpid()))['reason'], 'protected process')

    def test_exit_during_verification_needs_no_signal(self):
        """Report an exit that occurs between two identity snapshots.
        A missing second snapshot must not be called a reused PID.
        """
        import os
        saved = {'pid': 200, 'uid': os.getuid(), 'state': 'S'}
        with patch('lifecycle.process._protected', return_value=False), \
                patch('lifecycle.process.capture_identity', side_effect=[saved, None]), \
                patch('lifecycle.process.verify_identity', return_value=False), \
                patch('lifecycle.process.os.kill') as signal:
            result = terminate_identity(saved)
        self.assertEqual(result['status'], 'success')
        signal.assert_not_called()


if __name__ == '__main__':
    unittest.main()
