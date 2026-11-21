"""POSIX advisory lock: hold across checkpoint read, work, and save.

All cooperating writers must use this lock. Never unlink the lock file:
removal could allow two processes to lock different inodes for the same path.
"""
from contextlib import contextmanager
from pathlib import Path
import fcntl


@contextmanager
def checkpoint_lock(path):
    lock_path = Path(str(Path(path).resolve()) + '.lock')
    with lock_path.open('a') as handle:
        fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
