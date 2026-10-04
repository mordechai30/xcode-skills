"""LLDB-owned request server loaded by the installed xcrun lldb.
The server uses SB state and events, and never resumes without a request.
"""
import json
import os
import socket
import threading
import lldb


def snapshot(process):
    """Return debugger state, stop causes, and selected frame.
    Breakpoint stop data contains breakpoint and location ID pairs.
    """
    state = process.GetState()
    label = ('paused' if state in (lldb.eStateStopped, lldb.eStateCrashed, lldb.eStateSuspended)
             else 'running' if state in (lldb.eStateRunning, lldb.eStateStepping)
             else 'exited' if state in (lldb.eStateExited, lldb.eStateDetached, lldb.eStateInvalid)
             else 'uncertain')
    stops = []
    for thread in process if label == 'paused' else []:
        reason = thread.GetStopReason()
        if reason == lldb.eStopReasonNone:
            continue
        frame = thread.GetFrameAtIndex(0)
        entry = frame.GetLineEntry()
        ids = [thread.GetStopReasonDataAtIndex(i) for i in range(0, thread.GetStopReasonDataCount(), 2)] if reason == lldb.eStopReasonBreakpoint else []
        stops.append({'thread': thread.GetThreadID(), 'reason': reason,
                      'description': thread.GetStopDescription(4096), 'breakpoints': ids,
                      'frame': str(frame), 'file': str(entry.GetFileSpec()), 'line': entry.GetLine()})
    return {'status': 'success', 'state': label, 'lldb_state': state,
            'pid': process.GetProcessID(), 'stops': stops, 'exit_status': process.GetExitStatus()}


def handle(debugger, request, owned):
    """Perform one explicit debugger request against the owned target.
    State-changing operations are selected by operation modules.
    """
    action = request['action']
    target = debugger.GetSelectedTarget()
    process = target.GetProcess() if target.IsValid() else lldb.SBProcess()
    if action == 'launch':
        target = debugger.CreateTarget(request['executable'])
        if not target.IsValid():
            raise RuntimeError('LLDB could not create the selected target.')
        launch = lldb.SBLaunchInfo(request.get('arguments', []))
        launch.SetWorkingDirectory(request['working_directory'])
        launch.AddOpenFileAction(1, os.path.abspath('app-output.txt'), False, True)
        launch.AddOpenFileAction(2, os.path.abspath('app-error.txt'), False, True)
        error = lldb.SBError()
        process = target.Launch(launch, error)
        if error.Fail():
            raise RuntimeError(error.GetCString())
        owned['process'] = process
        return snapshot(process)
    if action == 'status':
        return snapshot(process)
    if action == 'set_breakpoint':
        bp = target.BreakpointCreateByLocation(request['file'], request['line'])
        locations = []
        for location in bp:
            entry = location.GetAddress().GetLineEntry()
            locations.append({'file': str(entry.GetFileSpec()), 'line': entry.GetLine(), 'resolved': location.IsResolved()})
        return {'status': 'success', 'id': bp.GetID(), 'locations': locations,
                'resolved': bp.GetNumResolvedLocations()}
    if action == 'delete_breakpoint':
        bp = target.FindBreakpointByID(request['id'])
        if not bp.IsValid():
            return {'status': 'success', 'already_removed': True}
        return {'status': 'success' if target.BreakpointDelete(request['id']) else 'failure'}
    if action in ('pause', 'continue', 'kill'):
        error = {'pause': process.Stop, 'continue': process.Continue, 'kill': process.Kill}[action]()
        return {'status': 'success' if error.Success() else 'failure', 'error': error.GetCString(),
                'current': snapshot(process)}
    if action == 'command':
        result = lldb.SBCommandReturnObject()
        debugger.GetCommandInterpreter().HandleCommand(request['command'], result)
        return {'status': 'success' if result.Succeeded() else 'failure',
                'output': result.GetOutput(), 'error': result.GetError(), 'current': snapshot(process)}
    raise ValueError('Unsupported controller action: ' + action)


def event_reader(listener, output, stopped):
    """Retain native LLDB events without holding command locks.
    Event watching does not make lifecycle decisions.
    """
    while not stopped.is_set():
        event = lldb.SBEvent()
        if listener.WaitForEvent(1, event):
            with open(output, 'a') as stream:
                stream.write(str(event) + '\n')


def serve(debugger, command, result, internal_dict):
    """Keep one debugger available through a short relative socket.
    LLDB runs this command until explicit final cleanup.
    """
    debugger.SetAsync(True)
    owned = {}
    stopped = threading.Event()
    listener = debugger.GetListener()
    thread = threading.Thread(target=event_reader, args=(listener, 'lldb-events.txt', stopped), daemon=True)
    thread.start()
    with socket.socket(socket.AF_UNIX) as server:
        server.bind('d.sock')
        os.chmod('d.sock', 0o600)
        server.listen(4)
        while True:
            channel, _ = server.accept()
            with channel:
                with channel.makefile('r') as stream:
                    request = json.loads(stream.readline())
                try:
                    value = {'status': 'success'} if request['action'] == 'close' else handle(debugger, request, owned)
                except Exception as error:
                    value = {'status': 'failure', 'message': str(error)}
                try:
                    channel.sendall((json.dumps(value) + '\n').encode())
                except (BrokenPipeError, ConnectionResetError):
                    with open('lldb-events.txt', 'a') as stream:
                        stream.write('Client disconnected; debugger remains available.\n')
            if request['action'] == 'close':
                break
    stopped.set()
    os.unlink('d.sock')


def __lldb_init_module(debugger, internal_dict):
    """Register the retained controller command in LLDB.
    The manager invokes this once in its owned debugger process.
    """
    debugger.HandleCommand('command script add -f lldb_controller.serve skill_controller')
