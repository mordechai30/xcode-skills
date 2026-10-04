"""Evidence that a verified Build produced the selected executable."""
from pathlib import Path
from lifecycle.state import atomic_json, read_json


def signature(executable):
    """Capture file identity for reusable-product evidence.
    A later replacement or modification makes old evidence stale.
    """
    value = Path(executable).stat()
    return {'inode': value.st_ino, 'size': value.st_size, 'modified_ns': value.st_mtime_ns,
            'changed_ns': value.st_ctime_ns}


def record(ctx, product):
    """Save the selected app, configuration, and verified executable identity.
    Each package stores this evidence in its own project folder.
    """
    path = ctx['data_dir'] / ('product-' + ctx['selection']['configuration'] + '.json')
    atomic_json(path, {'selection': ctx['selection'], 'executable': product['executable'],
                       'signature': signature(product['executable']), 'log': str(ctx['log'])})


def reusable(ctx, product):
    """Check whether saved Build evidence still matches the selected app.
    Stale or missing evidence is reported, not treated as a valid build.
    """
    value = read_json(ctx['data_dir'] / ('product-' + ctx['selection']['configuration'] + '.json'))
    if not value:
        return False
    return (all(value['selection'].get(key) == ctx['selection'].get(key)
                for key in ('owner_project', 'configuration', 'target', 'architecture')) and
            value['executable'] == product['executable'] and value['signature'] == signature(product['executable']))
