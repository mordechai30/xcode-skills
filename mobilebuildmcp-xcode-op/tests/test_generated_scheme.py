"""Verify saved configurations for targets with only auto-generated schemes.
Use disposable project identities without opening Xcode.
"""
import plistlib
import sys
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts'))
from lifecycle.schemes import configured, launch_arguments


class GeneratedSchemeTests(unittest.TestCase):
    """Materialize the requested Run configuration and preserve target identity.
    Repeated selection must reuse the same persistent scheme.
    """
    def test_configurations_and_reuse(self):
        """Save independent Debug and Release schemes for the selected app.
        Use the actual product name and preserve the original default configuration.
        """
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / 'out' / 'Project.xcodeproj'
            project.mkdir(parents=True)
            original = plistlib.dumps({'rootObject': 'root-id', 'objects': {
                'root-id': {'isa': 'PBXProject', 'projectDirPath': folder},
                'app-id': {'isa': 'PBXNativeTarget', 'name': 'App', 'productReference': 'product-id',
                           'buildConfigurationList': 'configs-id'},
                'product-id': {'isa': 'PBXFileReference', 'path': 'DifferentProduct.app'},
                'configs-id': {'isa': 'XCConfigurationList', 'defaultConfigurationName': 'Debug'}}})
            (project / 'project.pbxproj').write_bytes(original)
            selection = {'owner_project': str(project), 'scheme': 'App', 'target': 'App'}
            for configuration in ('Release', 'Debug'):
                selection['configuration'] = configuration
                name = configured(selection, 'fixture')
                self.assertEqual(configured(selection, 'fixture'), name)
                path = project / 'xcshareddata' / 'xcschemes' / (name + '.xcscheme')
                tree = ET.parse(path)
                launch = tree.find('LaunchAction')
                self.assertEqual(launch.get('buildConfiguration'), configuration)
                for parent in (tree.find('BuildAction'), launch):
                    reference = next(parent.iter('BuildableReference'))
                    self.assertEqual(reference.get('BlueprintIdentifier'), 'app-id')
                    self.assertEqual(reference.get('BuildableName'), 'DifferentProduct.app')
                    self.assertEqual(reference.get('ReferencedContainer'), 'container:out/Project.xcodeproj')
                self.assertEqual(configured(selection | {'scheme': name}, 'fixture'), name)
                self.assertEqual(launch_arguments(selection | {'scheme': name}), [])
            self.assertEqual(len(list(project.rglob('*.xcscheme'))), 2)
            source = project / 'xcshareddata/xcschemes/App.xcscheme'
            self.assertEqual(ET.parse(source).find('LaunchAction').get('buildConfiguration'), 'Debug')
            self.assertEqual((project / 'project.pbxproj').read_bytes(), original)

    def test_missing_product_is_reported(self):
        """Reject a target whose app product cannot be established.
        Do not invent a product filename or save an incomplete scheme.
        """
        with tempfile.TemporaryDirectory() as folder:
            project = Path(folder) / 'Project.xcodeproj'
            project.mkdir()
            (project / 'project.pbxproj').write_bytes(plistlib.dumps({'objects': {
                'app-id': {'isa': 'PBXNativeTarget', 'name': 'App'}}}))
            selection = {'owner_project': str(project), 'scheme': 'App', 'target': 'App',
                         'configuration': 'Release'}
            with self.assertRaisesRegex(ValueError, 'product reference'):
                configured(selection, 'fixture')
            self.assertEqual(list(project.rglob('*.xcscheme')), [])
