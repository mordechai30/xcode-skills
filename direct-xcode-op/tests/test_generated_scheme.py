"""Verify generated schemes do not require a saved XML file.
Live backend configuration checks remain responsible for suitability.
"""
import sys
import tempfile
import unittest
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lifecycle.schemes import configured, launch_arguments

class GeneratedSchemeTests(unittest.TestCase):
    """Use a discovered generated scheme without changing its project.
    Saved scheme behavior remains covered by lifecycle tests.
    """
    def test_existing_generated_scheme(self):
        """Accept a discovered scheme with no saved launch XML.
        Explicit arguments remain available and no file is created.
        """
        with tempfile.TemporaryDirectory() as folder:
            selection = {'owner_project': folder, 'scheme': 'App', 'target': 'App', 'configuration': 'Debug'}
            self.assertEqual(configured(selection, 'test'), 'App')
            self.assertEqual(launch_arguments(selection), [])
            selection['arguments'] = ['--test']
            self.assertEqual(launch_arguments(selection), ['--test'])
            self.assertEqual(list(Path(folder).iterdir()), [])
