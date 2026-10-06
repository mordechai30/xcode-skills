"""Copy available session diagnostics into the retained top-level log."""
from lifecycle.state import append_log
from lifecycle.diagnostics import diagnostics, StreamDiagnostics
import codecs
import sys
import os
import re
from pathlib import Path
import threading


def collect(ctx):
    """Consume pending server diagnostics without retaining transcripts.
    App and native command streams are drained when they are received.
    """
    if not ctx.get('log') or not ctx.get('data_dir'):
        return
    for name in ('bridge', 'mobile_server'):
        connection = ctx['runtime'].get(name)
        take = getattr(connection, 'take_diagnostics', None)
        content = take() if take else ''
        detail = diagnostics(content)
        if detail:
            append_log(ctx['log'], name + ' diagnostics', detail)


def drain(stream, ctx, title):
    """Consume a pipe promptly and append only diagnostic blocks.
    A background reader never retains ordinary app or launcher output.
    """
    parser = StreamDiagnostics()
    decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
    with stream:
        while True:
            chunk = os.read(stream.fileno(), 4096)
            if not chunk:
                detail = parser.feed(decoder.decode(b'', final=True), final=True)
                record_detail(ctx, title, detail)
                break
            detail = parser.feed(decoder.decode(chunk))
            record_detail(ctx, title, detail)


def capture_process(process, ctx, title):
    """Drain both owned process pipes while the app runs or is paused.
    The OS closes the streams after verified process cleanup.
    """
    for stream in (process.stdout, process.stderr):
        thread = threading.Thread(target=drain, args=(stream, ctx, title), daemon=True)
        thread.start()
        ctx.setdefault('runtime', {}).setdefault('stream_readers', []).append(thread)


def capture_fifo(path, log):
    """Provide LLDB with a pipe destination instead of a raw app archive.
    The reader removes the request-owned FIFO after the writer closes.
    """
    path = Path(path)
    os.mkfifo(path, 0o600)
    def read():
        try:
            drain(path.open('rb', buffering=0), {'forward':True}, 'App diagnostics')
        finally:
            path.unlink(missing_ok=True)
    threading.Thread(target=read, daemon=True).start()
    return str(path)


def record_detail(ctx, title, detail):
    """Keep a useful failure cause and record one diagnostic block.
    Startup evidence is held only until the operation log is available.
    """
    if not detail:
        return
    if ctx.get('forward'):
        sys.stdout.write(detail+'\n')
        sys.stdout.flush()
        return
    cause = next((line for line in detail.splitlines() if re.search(r'\b(?:error|fatal error)\s*:|\bfailed with exit code\b|^\s*(?:failure|failed):|Undefined symbols|duplicate symbol', line, re.I)), None)
    if cause:
        ctx.setdefault('last_diagnostic', cause[:500])
    for kind in ('warning','error'):
        line = next((line for line in detail.splitlines() if re.search(r'\b'+kind+r'\s*:',line,re.I)),None)
        if line:
            count = ctx.get('public_'+kind+'_count',0)+1
            ctx['public_'+kind+'_count'] = count
            old = ctx.get('public_'+kind)
            if not old or old.startswith('--- xcodebuild:') and not line.startswith('--- xcodebuild:'):
                ctx['public_'+kind] = line[:500]
    if ctx.get('log'):
        append_log(ctx['log'], title, detail)
    else:
        ctx.setdefault('evidence', []).append(title + '\n' + detail)
