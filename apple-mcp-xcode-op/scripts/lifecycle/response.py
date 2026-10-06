"""Render only operation results, requested inspection, and useful diagnostics."""
import sys
import re


def shorten(text, allowance):
    """Limit text at a UTF-8 boundary and mark omitted content.
    The returned value includes no recovery path or hidden field dump.
    """
    if len(text.encode()) <= allowance:
        return text
    marker = ' …'
    prefix = text.encode()[:max(0, allowance-len(marker.encode()))].decode('utf-8', errors='ignore')
    boundary = max(prefix.rfind('\n'), prefix.rfind(' '))
    if boundary > len(prefix)//2:
        prefix = prefix[:boundary]
    return prefix.rstrip()+marker


def render(value, operation=''):
    """Emit a short result with requested output and surfaced diagnostics.
    Count every byte, including the final newline, within 200 or 500 bytes.
    """
    limit = 500 if value.get('status') in ('failure','uncertain') or value.get('_detail') else 200
    label = {'set-breakpoint':'Breakpoint','debugger-command':'Inspect','continue':'Continue'}.get(operation, operation.capitalize() or 'Request')
    status = value.get('status','uncertain')
    state = value.get('state')
    outcome = {'success':'succeeded','failure':'failed','uncertain':'incomplete','needs_user_input':'needs input'}.get(status,'incomplete')
    if value.get('_interrupted'):
        head = label+' watch interrupted; app '+str(state or 'unknown')+'.'
    elif operation == 'status':
        head = 'Status: '+{'none':'no app','uncertain':'unknown'}.get(state,state or 'unknown')+'.'
    elif operation == 'set-breakpoint' and status == 'success':
        head = ('Breakpoint hit' if value.get('_hit') else 'Breakpoint set; app stopped' if value.get('watch') and state=='paused' else 'Breakpoint set')+(': '+value['location'] if value.get('location') and (value.get('_hit') or value.get('watch') and state=='paused') else '')+'.'
    elif operation == 'continue' and status == 'success' and state == 'paused':
        head = 'Continue succeeded; stopped'+(': '+value['location'] if value.get('location') else '')+'.'
    elif operation == 'run' and status == 'success' and state in ('exited','paused'):
        head = 'Run succeeded; app '+state+'.'
    else:
        head = label+' '+outcome+'.'
    if operation in ('set-breakpoint','continue') and value.get('watch') and state=='exited' and status=='success':
        head = label+' completed; app exited.'
    if status=='failure' and value.get('stage') in ('build','launch') and operation=='run':
        head = 'Run failed during '+value['stage'].capitalize()+'.'
    # Routine bookkeeping is private. Only relevant diagnostics follow the result.
    details = []
    for key, prefix in (('error','Error: '),('warning','Warning: ')):
        if value.get(key):
            text = str(value[key]).strip()
            details.append(text if re.search(r'\b'+key+r'\s*:',text,re.I) else prefix+text)
    if status != 'success' and value.get('message'):
        message = str(value['message']).strip()
        cause = str(value.get('error') or '').split(' (')[0]
        if not cause or cause not in message:
            details.append(message)
    if operation == 'set-breakpoint' and value.get('relocated'):
        details.append('Moved to '+str(value.get('location','another source line'))+'.')
    if value.get('choices'):
        details.append('Choose: '+', '.join(map(str,value['choices'])))
    head = shorten(head, min(100,limit-1))
    diagnostic = '\n'.join(details)
    if diagnostic:
        diagnostic = shorten(diagnostic, min(160 if value.get('output') else limit-len(head.encode())-2,limit-len(head.encode())-2))
    pieces = [head]+([diagnostic] if diagnostic else [])
    if operation == 'debugger-command' and value.get('output'):
        remaining = limit-len(('\n'.join(pieces)+'\n').encode())-1
        output = str(value['output']).rstrip()
        pieces.append(shorten(output,max(0,remaining)))
    return '\n'.join(pieces)+'\n'


def emit(value, operation=''):
    """Write a rendered response once without stderr chatter.
    No diagnostic archive is created.
    """
    sys.stdout.write(value if isinstance(value,str) else render(value,operation))
    sys.stdout.flush()
