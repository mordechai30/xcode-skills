"""Persist active-session ownership and operation locks."""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import tempfile
import time
from typing import Any, Iterator


def read_json(path: Path, default: Any = None) -> Any:
    """Read JSON and distinguish corrupt records from absent optional records.

    Corrupt ownership state blocks lifecycle work until a person inspects it.
    """
    if not path.exists():
        return default
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as error:
        raise RuntimeError(f"State is unreadable at {path}: {error}") from error


def atomic_json(path: Path, value: Any) -> None:
    """Write one complete JSON record using a same-directory atomic rename.

    Keep mode private because state contains process identity and debugger connection data.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=".state-", dir=path.parent)
    try:
        os.fchmod(fd, 0o600)
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            json.dump(value, stream, indent=2, sort_keys=True)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


@contextmanager
def operation_lock(root: Path, deadline=None) -> Iterator[None]:
    """Serialize state-changing operations for one installed skill.

    The kernel releases this advisory lock if the manager exits unexpectedly.
    """
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".operation.lock").open("a+") as lock:
        if deadline is None:
            fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        else:
            while True:
                if time.monotonic() >= deadline:
                    raise TimeoutError('Pause expired while queued. Use Status.')
                try:
                    fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    time.sleep(min(.05, max(0, deadline - time.monotonic())))
        yield










def remove_closed_channels(folder):
    """Remove known owned channels after verified helper termination.
    Preserve regular files and symlinks that do not match their expected types.
    """
    import stat
    for name, check in (('d.sock', stat.S_ISSOCK), ('app-output.pipe', stat.S_ISFIFO), ('app-error.pipe', stat.S_ISFIFO)):
        path = Path(folder) / name
        try:
            if check(path.lstat().st_mode):
                path.unlink()
        except FileNotFoundError:
            pass
