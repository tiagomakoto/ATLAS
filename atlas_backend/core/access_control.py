import os
import atexit
import signal

LOCK_FILE = "/tmp/atlas.lock"

def acquire_lock():
    if os.path.exists(LOCK_FILE):
        raise RuntimeError(
            "ATLAS_ALREADY_RUNNING — delete /tmp/atlas.lock se necessário"
        )

    with open(LOCK_FILE, "w") as f:
        f.write(str(os.getpid()))

    atexit.register(release_lock)

    signal.signal(signal.SIGTERM, lambda s, f: (release_lock(), exit(0)))

def release_lock():
    if os.path.exists(LOCK_FILE):
        os.remove(LOCK_FILE)