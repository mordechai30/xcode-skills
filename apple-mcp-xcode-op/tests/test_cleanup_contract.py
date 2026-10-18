"""Exercise the public cleanup command against isolated disposable artifacts.
No test launches an app or removes files outside its temporary directory.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

# Installed skill root whose public cleanup entrypoint is under test.
ROOT = Path(__file__).resolve().parents[1]


class CleanupContractTests(unittest.TestCase):
    """Verify explicit ownership selection and truthful cleanup results.
    Each scenario owns its paths and preserves representative unrelated files.
    """

    def invoke(self, path):
        """Invoke the packaged shell interface with one caller-supplied path.
        Capture the result so failures and no-op outcomes can be checked separately.
        """
        return subprocess.run(['bash', str(ROOT / 'scripts/cleanup.sh'), str(path)],
                              capture_output=True, text=True)

    def test_workspace_is_rejected_without_removing_neighbor_artifacts(self):
        """Reject a workspace whose folder cannot establish the selected app owner.
        A trailing slash must not bypass the same explicit input contract.
        """
        with tempfile.TemporaryDirectory() as folder:
            workspace = Path(folder) / 'Combined.xcworkspace'
            workspace.mkdir()
            artifact = Path(folder) / ROOT.name
            artifact.mkdir()
            sentinel = artifact / 'keep.txt'
            sentinel.write_text('unrelated to the selected owning project')
            for value in (str(workspace), str(workspace) + '/'):
                result = self.invoke(value)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('owning .xcodeproj', result.stdout)
                self.assertTrue(sentinel.exists())

    def test_owner_project_cleanup_preserves_logs_and_unrelated_files(self):
        """Clean the selected project artifacts without touching a sibling project.
        Preserve only regular top-level operation logs inside the artifact folder.
        """
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / 'Owner' / 'App.xcodeproj'
            project.mkdir(parents=True)
            data = project.parent / ROOT.name
            data.mkdir()
            log = data / 'log-fixture.txt'
            log.write_text('retained')
            (data / 'log-not-a-file.txt').mkdir()
            (data / 'session.json').write_text('{}')
            unrelated = Path(folder) / 'unrelated.txt'
            unrelated.write_text('retained')
            result = self.invoke(project)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(list(data.iterdir()), [log])
            self.assertTrue(project.exists())
            self.assertTrue(unrelated.exists())

    def test_package_folder_and_absent_artifacts(self):
        """Accept a package directory and distinguish an absent artifact folder.
        Missing input directories must fail instead of announcing successful cleanup.
        """
        with tempfile.TemporaryDirectory() as folder:
            package = Path(folder) / 'Package'
            package.mkdir()
            (package / 'Package.swift').write_text('// fixture')
            absent = self.invoke(package)
            self.assertEqual(absent.returncode, 0)
            self.assertIn('no artifacts found', absent.stdout)
            data = package / ROOT.name
            data.mkdir()
            (data / 'build-product').write_text('remove')
            self.assertEqual(self.invoke(package).returncode, 0)
            self.assertEqual(list(data.iterdir()), [])
            self.assertNotEqual(self.invoke(package / 'missing').returncode, 0)

    def test_symlink_artifact_folder_is_not_followed(self):
        """Reject an artifact-directory symlink rather than deleting its target.
        Keep the external target and its representative file intact.
        """
        with tempfile.TemporaryDirectory() as folder:
            owner = Path(folder) / 'Owner'
            owner.mkdir()
            elsewhere = Path(folder) / 'Elsewhere'
            elsewhere.mkdir()
            sentinel = elsewhere / 'keep.txt'
            sentinel.write_text('retained')
            (owner / ROOT.name).symlink_to(elsewhere, target_is_directory=True)
            self.assertNotEqual(self.invoke(owner).returncode, 0)
            self.assertTrue(sentinel.exists())


if __name__ == '__main__':
    unittest.main()
