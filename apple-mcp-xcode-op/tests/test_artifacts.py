"""Artifact evidence and explicit cleanup behavior in temporary folders."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from lifecycle.state import atomic_json, read_json


class ArtifactTests(unittest.TestCase):
    """Check current product evidence and corrupt state handling.
    Each test owns all files it creates.
    """
    def test_corrupt_record_is_not_treated_as_absent(self):
        """Surface corrupt JSON state instead of choosing a new context.
        Atomic writes produce complete readable records.
        """
        with tempfile.TemporaryDirectory() as name:
            path = Path(name) / 'session.json'
            atomic_json(path, {'owned': True})
            self.assertEqual(read_json(path), {'owned': True})
            path.write_text('{broken')
            with self.assertRaises(RuntimeError):
                read_json(path)

    def test_cleanup_preserves_top_level_logs(self):
        """Run explicit cleanup on disposable artifacts only.
        Nested logs, state, and other content are removed.
        """
        script = location / 'scripts' / 'cleanup.sh'
        if not script.exists():
            self.skipTest('Cleanup script is generated in the assembled package.')
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            project = root / 'App.xcodeproj'
            project.mkdir()
            data = root / location.name
            data.mkdir()
            log = data / 'log-fixture-Debug-26-10-04-12-00-00.txt'
            log.write_text('retained')
            (data / 'session.json').write_text('{}')
            nested = data / 'nested'
            nested.mkdir()
            (nested / 'log-extra.txt').write_text('removed')
            subprocess.run(['bash', str(script), str(project)], check=True)
            self.assertEqual(list(data.iterdir()), [log])
            self.assertTrue(project.exists())


if __name__ == '__main__':
    unittest.main()
