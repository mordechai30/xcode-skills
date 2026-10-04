"""Capture process identity and signal only a matching owned process."""
from __future__ import annotations

import ctypes
from ctypes.util import find_library
import os
import signal
import subprocess
import time


def executable_path(pid: int) -> str | None:
    """Resolve a process executable through macOS libproc.
    Use ps only when the native process-path API cannot return a path.
    """
    library = find_library("proc")
    if library:
        try:
            proc = ctypes.CDLL(library)
            buffer = ctypes.create_string_buffer(4096)
            if proc.proc_pidpath(pid, buffer, len(buffer)) > 0:
                return os.fsdecode(buffer.value)
        except (OSError, AttributeError):
            pass
    result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "comm="], capture_output=True, text=True)
    value = result.stdout.strip()
    return value or None


def capture_identity(pid: int) -> dict | None:
    """Capture process identity, owner, parent, state, and executable.
    Keep zombie records even when their executable path is unavailable.
    """
    if pid <= 1:
        return None
    result = subprocess.run(["/bin/ps", "-p", str(pid), "-o", "uid=,ppid=,stat=,lstart="],
                            capture_output=True, text=True)
    if result.returncode:
        return None
    fields = result.stdout.strip().split(None, 6)
    if len(fields) < 6:
        return None
    executable = executable_path(pid)
    if not executable and 'Z' not in fields[2]:
        return None
    return {"pid": pid, "uid": int(fields[0]), "parentPID": int(fields[1]),
            "state": fields[2], "start": " ".join(fields[3:]), "executable": executable}


def verify_identity(saved: dict, expected_executable: str | None = None) -> bool:
    """Compare a saved identity with a fresh snapshot before action.
    Optional executable evidence must match for a live process.
    """
    fresh = capture_identity(int(saved.get("pid", -1)))
    if fresh is None:
        return False
    zombie = 'Z' in fresh['state']
    keys = ('pid', 'uid', 'start') if zombie else ('pid', 'uid', 'start', 'executable')
    same = all(fresh.get(key) == saved.get(key) for key in keys)
    if expected_executable and not zombie:
        same = same and os.path.realpath(fresh["executable"]) == os.path.realpath(expected_executable)
    return same


def _protected(pid: int) -> bool:
    """Protect PID 1, the manager, and its ancestors.
    Walk current parent identities before permitting a signal.
    """
    current = os.getpid()
    while current > 1:
        if pid == current:
            return True
        identity = capture_identity(current)
        if identity is None:
            return False
        current = identity["parentPID"]
    return pid == 1


def terminate_identity(saved: dict, timeout: float = 5.0) -> dict:
    """Terminate a process only while its saved identity still matches.
    Apply TERM then KILL; report zombies separately for parent handling.
    """
    pid = int(saved.get("pid", -1))
    if pid <= 1 or _protected(pid) or saved.get('uid') != os.getuid():
        return {"status": "failure", "reason": "protected process"}
    fresh = capture_identity(pid)
    if fresh is None:
        return {"status": "success", "reason": "already exited"}
    if not verify_identity(saved):
        if capture_identity(pid) is None:
            return {"status": "success", "reason": "exited during identity verification"}
        return {"status": "failure", "reason": "process identity changed"}
    if "Z" in fresh["state"]:
        return {"status": "zombie", "identity": fresh}
    for number in (signal.SIGTERM, signal.SIGKILL):
        fresh = capture_identity(pid)
        if fresh is None:
            return {"status": "success", "reason": "process exited"}
        if "Z" in fresh["state"]:
            return {"status": "zombie", "identity": fresh}
        if not verify_identity(saved):
            if capture_identity(pid) is None:
                return {"status": "success", "reason": "exited before signal"}
            return {"status": "failure", "reason": "process identity changed before signal"}
        try:
            os.kill(pid, number)
        except ProcessLookupError:
            return {"status": "success", "reason": "exited before signal"}
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            fresh = capture_identity(pid)
            if fresh is None:
                return {"status": "success", "reason": signal.Signals(number).name}
            if "Z" in fresh["state"]:
                return {"status": "zombie", "identity": fresh}
            time.sleep(0.1)
    return {"status": "failure", "reason": "process survived SIGKILL"}


def traced(pid):
    """Read macOS P_TRACED evidence for debugger attachment.
    Return None when the process no longer exists or flags cannot be read.
    """
    result = subprocess.run(['/bin/ps', '-p', str(pid), '-o', 'flags='], capture_output=True, text=True)
    if result.returncode or not result.stdout.strip():
        return None
    return bool(int(result.stdout.strip(), 16) & 0x800)


def matching_processes(executable):
    """Find live processes by verified full executable path.
    This is identity inspection, never process-name termination.
    """
    listing = subprocess.run(['/bin/ps', '-axo', 'pid='], text=True, capture_output=True, check=True)
    expected = os.path.realpath(executable)
    found = []
    for value in listing.stdout.split():
        pid = int(value)
        path = executable_path(pid)
        if path and os.path.realpath(path) == expected:
            identity = capture_identity(pid)
            if identity:
                found.append(identity)
    return found
