"""Check saved launch arguments without running a debugger."""
from pathlib import Path
import sys
import tempfile
import unittest

# Resolve imports in the source tree and in each independent package.
location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from lifecycle.schemes import launch_arguments


class LaunchArgumentTests(unittest.TestCase):
    """Check enabled argument values and ambiguous saved schemes.
    The parser must preserve spaces within a single argument.
    """
    def test_enabled_arguments_preserve_values(self):
        """Pass enabled values exactly and omit disabled arguments.
        No shell tokenization or command substitution is used.
        """
        with tempfile.TemporaryDirectory() as name:
            project = Path(name) / 'App.xcodeproj'
            project.mkdir()
            (project / 'App.xcscheme').write_text('<Scheme><LaunchAction><CommandLineArguments>'
                '<CommandLineArgument argument="--stay-alive" isEnabled="YES"/>'
                '<CommandLineArgument argument="two words" isEnabled="YES"/>'
                '<CommandLineArgument argument="disabled" isEnabled="NO"/>'
                '</CommandLineArguments></LaunchAction></Scheme>')
            selection = {'owner_project': str(project), 'scheme': 'App'}
            self.assertEqual(launch_arguments(selection), ['--stay-alive', 'two words'])
            (project / 'nested').mkdir()
            (project / 'nested/App.xcscheme').write_text('<Scheme/>')
            with self.assertRaises(ValueError):
                launch_arguments(selection)
