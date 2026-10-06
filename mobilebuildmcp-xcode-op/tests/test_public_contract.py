"""Verify public inputs before backend preparation, and exact launch arguments."""
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import manager
from lifecycle.schemes import launch_arguments
from operations.common import context


class PublicContractTests(unittest.TestCase):
    def parse(self, *values):
        args = manager.parser().parse_args(values)
        manager.validate(args)
        return args

    def test_argument_replacement_and_empty(self):
        with tempfile.TemporaryDirectory() as name:
            project = Path(name) / 'App.xcodeproj'
            project.mkdir()
            (project / 'App.xcscheme').write_text('<Scheme><LaunchAction><CommandLineArguments><CommandLineArgument argument="saved" isEnabled="YES"/></CommandLineArguments></LaunchAction></Scheme>')
            for suffix, expected in (([], ['saved']), (['--arguments'], []), (['--arguments','--mode','test'], ['--mode','test'])):
                args = self.parse('run','--project',str(project),'--configuration','Debug',*suffix)
                with patch('operations.common.backend'):
                    ctx = context(args, Path('/tmp/direct-xcode-op'))
                ctx['selection'].update(owner_project=str(project), scheme='App')
                self.assertEqual(launch_arguments(ctx['selection']), expected)

    def test_aliases_and_irrelevant_inputs(self):
        self.assertEqual(self.parse('build','--package','/tmp/pkg','--configuration','Debug','--product','App').target,'App')
        with self.assertRaises(ValueError):
            self.parse('build','--package','/tmp/pkg','--configuration','Debug','--target','App')
        for values in (('status','--project','/tmp/App.xcodeproj'), ('pause','--configuration','Debug'), ('continue','--detail'), ('build','--package','/tmp/pkg','--configuration','Debug','--target','A','--product','B'), ('run','--package','/tmp/pkg','--configuration','Debug','--scheme','App')):
            with self.assertRaises(ValueError):
                self.parse(*values)

    def test_route_rejection_precedes_backend(self):
        with tempfile.TemporaryDirectory() as name:
            project = Path(name) / 'App.xcodeproj'
            project.mkdir()
            args = self.parse('run','--project',str(project),'--configuration','Debug','--arguments')
            with patch('operations.common.backend') as backend:
                for skill in ('apple-mcp-xcode-op','mobilebuildmcp-xcode-op'):
                    with self.assertRaisesRegex(ValueError, '--arguments'):
                        context(args, Path(name) / skill)
                backend.assert_not_called()

    def test_status_without_context(self):
        self.assertIn('status', manager.OPERATIONS)

if __name__ == '__main__':
    unittest.main()
