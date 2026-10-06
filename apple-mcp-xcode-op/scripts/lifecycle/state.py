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
def operation_lock(root: Path) -> Iterator[None]:
    """Serialize state-changing operations for one installed skill.

    The kernel releases this advisory lock if the manager exits unexpectedly.
    """
    root.mkdir(parents=True, exist_ok=True)
    with (root / ".operation.lock").open("a+") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
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
    path.write_text(f"Started: {now.isoformat()}\nTimezone: {now.tzname()}\n", encoding="utf-8")
    return path, now


def previous_build(project_data: Path, skill: str, configuration: str, selection=None) -> Path | None:
    """Find the newest invoked Build for this project and configuration.
    Preparation-only logs and sibling projects do not advance history.
    """
    prefix = f"log-{skill}-{configuration}-"
    files = []
    for path in project_data.glob(prefix + '*.txt'):
        text = path.read_text(encoding='utf-8')
        if 'BUILD_INVOKED\n' not in text:
            continue
        if selection:
            contexts = [json.loads(line[len('BUILD_CONTEXT='):]) for line in text.splitlines() if line.startswith('BUILD_CONTEXT=')]
            if not contexts or contexts[0].get('owner_project') != selection.get('owner_project'):
                continue
        files.append(path)
    return max(files, key=lambda path: path.name, default=None)


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
    with path.open("a", encoding="utf-8") as stream:
        stream.write(f"\n[{datetime.now().astimezone().isoformat()}] {title}\n")
        stream.write(content)
        if not content.endswith("\n"):
            stream.write("\n")
