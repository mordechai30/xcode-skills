"""Select saved schemes or create persistent configuration copies."""
from pathlib import Path
import json
import subprocess
import xml.etree.ElementTree as ET


def launch_arguments(selection):
    """Read enabled arguments from the selected saved launch scheme.
    Saved schemes supply arguments; generated schemes use explicit arguments or none.
    """
    if selection.get('arguments') is not None:
        return selection['arguments']
    if selection.get('package'):
        return []
    containers = [Path(selection['owner_project'])]
    if selection.get('workspace'):
        containers.append(Path(selection['workspace']))
    sources = [file for container in containers for file in container.rglob('*.xcscheme')
               if file.stem == selection['scheme']]
    if not sources:
        return selection.get('arguments') or []
    if len(sources) != 1:
        raise ValueError('Several saved launch schemes match the selection.')
    launch = ET.parse(sources[0]).find('LaunchAction')
    if launch is None:
        raise ValueError('Selected saved scheme has no LaunchAction.')
    return [item.get('argument', '') for item in launch.findall('CommandLineArguments/CommandLineArgument')
            if item.get('isEnabled') == 'YES']


def target_identifier(project, target):
    """Resolve the saved scheme blueprint from project target names.
    This reads target identity, not build settings.
    """
    result = subprocess.run(['plutil', '-convert', 'json', '-o', '-', str(Path(project) / 'project.pbxproj')],
                            capture_output=True, text=True)
    if result.returncode:
        raise RuntimeError('Could not read saved target identity: ' + result.stderr)
    objects = json.loads(result.stdout)['objects']
    matches = [key for key, value in objects.items() if value.get('isa') == 'PBXNativeTarget' and value.get('name') == target]
    if len(matches) != 1:
        raise ValueError('Select one saved native target identity.')
    return matches[0]


def suitable(path, target, configuration, identifier=None):
    """Check the app target and launch configuration in a saved scheme.
    Buildable references avoid choosing an unrelated target.
    """
    tree = ET.parse(path)
    launch = tree.find('LaunchAction')
    runnable = launch.find('BuildableProductRunnable') if launch is not None else None
    return bool(launch is not None and runnable is not None and launch.get('buildConfiguration') == configuration and
                any(ref.get('BlueprintName') == target or identifier and ref.get('BlueprintIdentifier') == identifier
                    for ref in runnable.iter('BuildableReference')))


def configured(selection, skill):
    """Use an existing scheme; copy a saved scheme only for configuration changes.
    Live backend settings verify generated schemes; saved originals remain unchanged.
    """
    project = Path(selection['owner_project'])
    containers = [project]
    if selection.get('workspace'):
        containers.append(Path(selection['workspace']))
    sources = [file for container in containers for file in container.rglob('*.xcscheme')
               if file.stem == selection['scheme']]
    if not sources:
        selection['generated_scheme'] = True
        return selection['scheme']
    if len(sources) != 1:
        raise ValueError('Several saved source schemes match the selection.')
    source = sources[0]
    identifier = target_identifier(project, selection['target'])
    if suitable(source, selection['target'], selection['configuration'], identifier):
        return source.stem
    parsed = ET.parse(source)
    launch = parsed.find('LaunchAction')
    runnable = launch.find('BuildableProductRunnable') if launch is not None else None
    if launch is None or runnable is None or not any(ref.get('BlueprintName') == selection['target'] or ref.get('BlueprintIdentifier') == identifier
                                 for ref in runnable.iter('BuildableReference')):
        raise ValueError('Saved scheme does not launch the selected app target.')
    base = source.stem + '-' + skill + '-' + selection['configuration']
    number = 1
    while True:
        name = base if number == 1 else base + '-' + str(number)
        copy = source.with_name(name + '.xcscheme')
        if not copy.exists():
            launch.set('buildConfiguration', selection['configuration'])
            with copy.open('xb') as stream:
                parsed.write(stream, encoding='UTF-8', xml_declaration=True)
            return name
        if suitable(copy, selection['target'], selection['configuration'], identifier):
            return name
        number += 1
