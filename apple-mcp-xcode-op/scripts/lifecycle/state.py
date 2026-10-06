"""Persist active-session ownership, operation locks, and append-only logs."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timedelta
import fcntl
import json
import os
from pathlib import Path
import re
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


def new_log(project_data: Path, skill: str, configuration: str) -> tuple[Path, datetime]:
    """Create a unique local-time log for one Build attempt.

    Build age is derived from this filename, never from later append activity.
    """
    now = datetime.now().astimezone()
    stamp = now.strftime("%y-%m-%d-%H-%M-%S")
    base = project_data / f"log-{skill}-{configuration}-{stamp}.txt"
    path = base
    while True:
        try:
            path.touch(mode=0o600, exist_ok=False)
            break
        except FileExistsError:
            time.sleep(0.05)
            now = datetime.now().astimezone()
            path = project_data / f"log-{skill}-{configuration}-{now.strftime('%y-%m-%d-%H-%M-%S')}.txt"

    return path, now


def previous_build(project_data: Path, skill: str, configuration: str, selection=None) -> Path | None:
    """Find the newest invoked Build for this project and configuration.
    Preparation-only logs and sibling projects do not advance history.
    """
    for path in sorted(project_data.glob(f'log-{skill}-{configuration}-*.txt'), reverse=True):
        with path.open(encoding='utf-8') as stream:
            if any(line in ('Build invoked.\n','BUILD_INVOKED\n') for line in stream):
                return path
    return None


def clean_required(previous: Path | None, now: datetime) -> bool:
    """Apply the first-attempt and strictly-over-one-hour Clean rule.
    Parse filename time so later session output does not reset age.
    """
    if previous is None:
        return True
    match = re.search(r"(\d{2}-\d{2}-\d{2}-\d{2}-\d{2}-\d{2})\.txt$", previous.name)
    if not match:
        raise RuntimeError(f"Build log timestamp is invalid: {previous.name}")
    try:
        attempted = datetime.strptime(match.group(1), "%y-%m-%d-%H-%M-%S").replace(tzinfo=now.tzinfo)
    except ValueError as error:
        raise RuntimeError(f"Build log timestamp is invalid: {previous.name}") from error
    return now - attempted > timedelta(hours=1)


def append_log(path: Path, title: str, content: str) -> None:
    """Append a timestamped operation result to its Build log.
    Preserve the original filename and all previous output.
    """
    if title == 'Public response':
        text = content
    elif title in ('Clean result','Prerequisite Clean','Failed Build Clean'):
        text = 'Clean '+({'success':'succeeded','failure':'failed','uncertain':'incomplete'}.get(content,content))+'.\n'
    else:
        from lifecycle.diagnostics import diagnostics
        text = diagnostics(content)
        if not text:
            return
    with path.open('a',encoding='utf-8') as stream:
        stream.write(text)
        if not text.endswith('\n'):
            stream.write('\n')


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
