"""Installation erst nach Freigabe der eigenen Dienst-/Relais-Sperren."""
import fcntl
import os
from pathlib import Path
import time

root = Path('/run/RelayScheduler')
deadline = time.monotonic() + 12
while True:
    handles = []
    try:
        for path in sorted(root.glob('*.lock')):
            fd = os.open(str(path), os.O_RDWR | os.O_NOFOLLOW)
            handles.append(fd)
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        break
    except BlockingIOError:
        if time.monotonic() >= deadline:
            raise SystemExit('Eigene Relais-Sperre weiterhin belegt')
        time.sleep(.2)
    finally:
        for fd in handles: os.close(fd)
