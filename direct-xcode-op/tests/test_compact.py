"""Verify public byte budgets, selection reuse, and local references.
Use fake backends and disposable files rather than launching apps.
"""
from argparse import Namespace
import contextlib
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
from unittest.mock import Mock

location = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(location / 'scripts' if (location / 'scripts').exists() else location))
from lifecycle.response import render, emit
from operations.common import resolve_selection, save_session


class CompactTests(unittest.TestCase):
    """Check observable response and context behavior.
    Large fixture envelopes must never escape the public emitter.
    """
    def test_normal_utf8_budget_and_text(self):
        """Bound successful responses despite huge internal evidence.
        Include Unicode and long paths in otherwise valid outcomes.
        """
        for op in ('build', 'run', 'kill', 'pause', 'continue', 'set-breakpoint'):
            value = {'status': 'success', 'raw': 'x' * 1000000, 'message': '界😀' * 10000,
                     'app': {'pid': 1234}, 'debugger': True, 'state': 'running', 'log': '/long/' + 'x' * 500 + '.txt'}
            text = render(value, op)
            self.assertLessEqual(len(text.encode()), 200)
            self.assertTrue('succeeded' in text or 'Breakpoint set.' in text)
            self.assertNotIn('/long/',text)

    def test_errors_help_and_requested_inspection(self):
        """Keep exceptional output and its newline within 500 bytes.
        Inspection must retain values rather than substitute the stop cause.
        """
        for message in ('界😀' * 10000, '\\"\n' * 10000):
            text = render({'status': 'failure', 'message': message})
            self.assertLessEqual(len(text.encode()), 500)
            self.assertIn('…',text)
        value = {'status': 'success', 'output': 'tick = 123\n' * 1000,
                 'current': {'state': 'paused', 'stops': [{'description': 'breakpoint'}]}}
        text = render(value, 'debugger-command')
        self.assertLessEqual(len(text.encode()), 500)
        self.assertIn('tick = 123',text)
        stream = io.StringIO()
        with contextlib.redirect_stdout(stream), contextlib.redirect_stderr(stream):
            emit({'status': 'success', 'message': 'ok'})
        self.assertEqual(stream.getvalue().count('\n'), 1)

    def test_cli_help_and_argument_errors_are_bounded(self):
        """Exercise the actual public CLI without an app session.
        Help and oversized invalid arguments produce one text response.
        """
        import subprocess
        manager = location / 'scripts/manager.py'
        if not manager.exists():
            self.skipTest('Run against the assembled manager.')
        for arguments, limit in ((['--help'], 200), (['build', '--unknown-' + 'x' * 20000], 500)):
            process = subprocess.run([sys.executable, str(manager), *arguments], capture_output=True)
            self.assertLessEqual(len(process.stdout) + len(process.stderr), limit)
            self.assertFalse(process.stderr)
            self.assertTrue(process.stdout.decode().strip())


    def test_cached_discovery_and_destination(self):
        """Reuse initial discovery and select the reported local Mac.
        Neither repeat resolution nor native preflight creates a remote connection.
        """
        with tempfile.TemporaryDirectory() as folder:
            backend = Mock()
            backend.discover_destinations.return_value = ['Any Mac', 'My Mac']
            ctx = {'backend': backend, 'skill': 'fixture', 'selection': {},
                   'discovery': {'owners': {'App': str(Path(folder) / 'App.xcodeproj')},
                                 'choices': {'scheme': ['App'], 'target': ['App']}}}
            args = Namespace(operation='run')
            self.assertEqual(resolve_selection(ctx, args, False)['status'], 'success')
            backend.discover_destinations.assert_not_called()
            self.assertEqual(resolve_selection(ctx, args)['status'], 'success')
            self.assertEqual(ctx['selection']['destination'], 'My Mac')
            resolve_selection(ctx, args)
            backend.discover.assert_not_called()
            backend.discover_destinations.assert_called_once()

    def test_any_mac_run_rejected(self):
        """Reject generic execution before any Build attempt.
        Preserve the explicitly requested choice instead of replacing it.
        """
        with tempfile.TemporaryDirectory() as folder:
            backend = Mock()
            backend.discover_destinations.return_value = ['Any Mac', 'My Mac']
            ctx = {'backend': backend, 'skill': 'fixture', 'selection': {'destination': 'Any Mac'},
                   'discovery': {'owners': {'App': str(Path(folder) / 'App.xcodeproj')},
                                 'choices': {'scheme': ['App'], 'target': ['App']}}}
            self.assertEqual(resolve_selection(ctx, Namespace(operation='run'))['status'], 'needs_user_input')
            backend.build.assert_not_called()

    def test_session_has_no_diagnostic_envelopes(self):
        """Persist process ownership without raw launch/build responses.
        The log retains diagnostics separately from recovery state.
        """
        with tempfile.TemporaryDirectory() as folder:
            ctx = {'data_dir': Path(folder), 'active_path': Path(folder) / 'active.json', 'selection': {}}
            save_session(ctx, {'state': 'running', 'app': {'pid': 1234}, 'build': {'raw': 'huge'}, 'launch': {'raw': 'huge'}})
            saved = json.loads((Path(folder) / 'session.json').read_text())
            self.assertNotIn('build', saved)
            self.assertNotIn('launch', saved)

    def test_bundled_links_and_heading_anchors(self):
        """Resolve all installed document links within the package.
        Supporting documents never link through a reference chain.
        """
        if not (location / 'SKILL.md').exists():
            self.skipTest('Run against an assembled independent package.')
        docs = [location / 'SKILL.md', *sorted((location / 'references').glob('*.md'))]
        self.assertEqual(len(docs), 3)
        for doc in docs:
            for target in re.findall(r'\]\(([^)]+)\)', doc.read_text()):
                self.assertFalse(target.startswith(('/', 'http:', 'https:')))
                path, _, anchor = target.partition('#')
                resolved = (location / path).resolve()
                self.assertTrue(resolved.is_relative_to(location.resolve()))
                self.assertTrue(resolved.is_file())
                self.assertEqual(doc.name, 'SKILL.md')
                if anchor:
                    headings = re.findall(r'^#+ (.+)$', resolved.read_text(), re.M)
                    anchors = [re.sub(r'[^\w -]', '', h.lower()).replace(' ', '-') for h in headings]
                    self.assertIn(anchor, anchors)


if __name__ == '__main__':
    unittest.main()
