"""Check saved scheme copies without opening Xcode."""
from pathlib import Path
import plistlib
import sys
import tempfile
import unittest

# Resolve imports within each independent package.
location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from lifecycle.schemes import configured


class SavedSchemeTests(unittest.TestCase):
    """Check original preservation, reusable copies, and numbered conflicts.
    Temporary project data supplies one unambiguous native target.
    """
    def test_copy_reuse_and_conflicting_name(self):
        """Copy only the selected launch configuration and retain arguments.
        An unsuitable name collision receives a numbered suffix.
        """
        with tempfile.TemporaryDirectory() as name:
            project = Path(name) / 'App.xcodeproj'
            project.mkdir()
            (project / 'project.pbxproj').write_bytes(plistlib.dumps({'objects': {'target': {'isa': 'PBXNativeTarget', 'name': 'App'}}}))
            source = project / 'App.xcscheme'
            original = b'<Scheme><LaunchAction buildConfiguration="Debug" custom="keep"><BuildableProductRunnable><BuildableReference BlueprintName="App"/></BuildableProductRunnable><CommandLineArguments><CommandLineArgument argument="--stay-alive" isEnabled="YES"/></CommandLineArguments></LaunchAction><ProfileAction buildConfiguration="Release" unrelated="keep"/></Scheme>'
            source.write_bytes(original)
            selection = {'owner_project': str(project), 'scheme': 'App', 'target': 'App', 'configuration': 'Debug'}
            self.assertEqual(configured(selection, 'fixture'), 'App')
            selection['configuration'] = 'Release'
            (project / 'App-fixture-Release.xcscheme').write_bytes(original)
            self.assertEqual(configured(selection, 'fixture'), 'App-fixture-Release-2')
            self.assertEqual(configured(selection, 'fixture'), 'App-fixture-Release-2')
            copied = (project / 'App-fixture-Release-2.xcscheme').read_text()
            self.assertIn('buildConfiguration="Release"', copied)
            self.assertIn('custom="keep"', copied)
            self.assertIn('--stay-alive', copied)
            self.assertIn('unrelated="keep"', copied)
            self.assertEqual(source.read_bytes(), original)

    def test_generated_scheme_needs_no_saved_source(self):
        """Use a discovered generated scheme without creating a copy.
        The backend must verify its live configuration.
        """
        with tempfile.TemporaryDirectory() as name:
            project = Path(name) / 'App.xcodeproj'
            project.mkdir()
            selection = {'owner_project': str(project), 'scheme': 'App'}
            self.assertEqual(configured(selection, 'fixture'), 'App')
            self.assertTrue(selection['generated_scheme'])
            self.assertEqual(list(project.iterdir()), [])
