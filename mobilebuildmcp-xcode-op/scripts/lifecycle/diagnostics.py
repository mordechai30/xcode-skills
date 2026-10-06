"""Extract useful diagnostics for bounded public responses.
Successful backend payloads and ordinary app output are discarded.
"""
import re
# Match diagnostic labels, not build-setting names such as WARNINGS_AS_ERRORS.
LABEL = re.compile(r'\b(?:warning|error|fatal error)\b\s*[:\-]|\b(?:failed|failure)\b\s*:|\*\* .*FAILED|^\s*(?:Error|Warning):|\bfailed with exit code\b|^\s*Build failed\b|Undefined symbols|duplicate symbol', re.I)


def diagnostics(value):
    """Read known diagnostic fields, not arbitrary backend object trees.
    Native strings are filtered by diagnostic labels and adjacent source context.
    """
    if isinstance(value,str):
        return '\n'.join(native_lines(value.splitlines()))
    if isinstance(value,list):
        return '\n'.join(filter(None,(diagnostics(item) for item in value)))
    if not isinstance(value,dict):
        return ''
    structured = value.get('structured',value.get('structuredContent'))
    if isinstance(structured,(dict,list)):
        return diagnostics(structured)
    if value.get('isEligible') is False:
        return ''
    found = []
    severity = str(value.get('classification',value.get('severity',''))).lower()
    if severity in ('error','warning','failure','fatal'):
        message = value.get('message') or value.get('description') or severity
        location = value.get('filePath') or value.get('file') or value.get('path')
        line = value.get('lineNumber',value.get('line'))
        source = str(location)+(':'+str(line) if line else '')+': ' if location else ''
        return source+('warning' if severity=='warning' else 'error')+': '+str(message)
    for key in ('errors','warnings','buildErrors','buildWarnings'):
        items = value.get(key) or []
        if not isinstance(items,list):
            items = [items]
        for item in items:
            kind = 'warning' if 'warning' in key.lower() else 'error'
            if isinstance(item,dict):
                found.append(diagnostics({'severity':kind,**item}))
            elif item:
                found.append(kind+': '+str(item))
    # Domain schemas use these fixed containers; other metadata is discarded.
    for key in ('data','payload','diagnostics','summary'):
        if isinstance(value.get(key),(dict,list)):
            found.append(diagnostics(value[key]))
    output = value.get('output')
    if isinstance(output,dict):
        for key in ('stdout','stderr'):
            text = output.get(key) or ''
            found.append(diagnostics('\n'.join(text) if isinstance(text,list) else text))
    elif isinstance(output,str):
        found.append(diagnostics(output))
    if value.get('stderr'):
        found.append(diagnostics(value['stderr']))
    failed = value.get('isError') or value.get('didError') or value.get('status')=='failure'
    for key in ('error','message'):
        if value.get(key):
            detail = diagnostics(str(value[key]))
            if key=='error' or failed:
                detail = detail or 'error: '+str(value[key]).splitlines()[0]
            found.append(detail)
    if not structured:
        for block in value.get('content',[]):
            if block.get('type','text')=='text':
                text = block.get('text','')
                detail = diagnostics(text)
                if failed and not detail:
                    detail = 'error: '+next((line for line in text.splitlines() if line.strip()),'Backend request failed.')
                found.append(detail)
    return '\n'.join(filter(None,found))


def record(ctx, stage, value):
    """Extract useful diagnostics once and discard the backend envelope.
    Backend setup stages are not public operation status.
    """
    detail = diagnostics(value)
    if detail:
        from lifecycle.output import record_detail
        record_detail(ctx,'Diagnostics',detail)


def build_summary(line):
    """Identify repeated build command summaries without diagnostic content.
    Compiler source, caret, notes, and linker details remain eligible.
    """
    return bool(re.match(r'^\s*(?:The following build commands failed:|CompileC |CompileSwift |SwiftCompile |SwiftEmitModule |Building project |Building workspace )', line))


def native_lines(lines):
    """Keep diagnostic labels with their source, caret, and related notes.
    Preserve repeated occurrences; only ordinary output is discarded.
    """
    active = False
    for line in lines:
        if build_summary(line):
            active = False
            continue
        labeled = bool(LABEL.search(line)) and not line.lstrip().startswith('{ platform:')
        context = active and (bool(re.search(r'\bnote:', line)) or bool(re.match(r'^\s*(?:\d+\s*\||\||[~^]|\s+\S)', line)))
        if labeled or context:
            yield line
        active = labeled or context


class StreamDiagnostics:
    """Carry incomplete lines between reads and preserve diagnostic context.
    EOF flushes the final incomplete line without archiving the input stream.
    """
    def __init__(self):
        self.pending = ''
        self.active = False

    def feed(self, text, final=False):
        text = self.pending + text
        lines = text.splitlines(keepends=True)
        self.pending = ''
        if lines and not lines[-1].endswith(('\n','\r')) and not final:
            self.pending = lines.pop()
            if not self.active and not LABEL.search(self.pending):
                # Keep only a short suffix of an ordinary incomplete line.
                self.pending = self.pending[-4096:]
        result = []
        for raw in lines:
            line = raw.rstrip('\r\n')
            if build_summary(line):
                self.active = False
                continue
            labeled = bool(LABEL.search(line)) and not line.lstrip().startswith('{ platform:')
            context = self.active and (bool(re.search(r'\bnote:', line)) or bool(re.match(r'^\s*(?:\d+\s*\||\||[~^]|\s+\S)', line)))
            if labeled or context:
                result.append(line)
            self.active = labeled or context
        return '\n'.join(result)
