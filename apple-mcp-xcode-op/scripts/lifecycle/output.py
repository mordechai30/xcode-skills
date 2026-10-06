"""Copy available session diagnostics into the retained top-level log."""
from lifecycle.state import append_log


def collect(ctx):
    """Append new output bytes without repeating earlier content.
    Artifact offsets and MCP diagnostic positions live in the owned runtime.
    """
    if not ctx.get('log') or not ctx.get('data_dir'):
        return
    offsets = ctx['runtime'].setdefault('output_offsets', {})
    for name in ('launcher-output.txt', 'app-output.txt', 'app-error.txt', 'lldb-events.txt'):
        path = ctx['data_dir'] / name
        if not path.is_file():
            continue
        with path.open('rb') as stream:
            position = offsets.get(name, 0)
            if path.stat().st_size < position:
                position = 0
            stream.seek(position)
            content = stream.read()
            offsets[name] = stream.tell()
        if content:
            append_log(ctx['log'], name, content.decode('utf-8', errors='replace'))
    for name in ('bridge', 'mobile_server'):
        connection = ctx['runtime'].get(name)
        lines = getattr(connection, 'stderr_lines', [])
        position = offsets.get(name, 0)
        content = ''.join(lines[position:])
        offsets[name] = len(lines)
        if content:
            append_log(ctx['log'], name + ' stderr', content)
