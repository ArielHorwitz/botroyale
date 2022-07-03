import time

def file_load(file):
    with open(file, 'r') as f:
        d = f.read()
    return d


def file_dump(file, d, clear=True):
    with open(file, 'w' if clear else 'a') as f:
        f.write(d)


def ping():
    """Generate a time value to be later used by pong."""
    return time.time() * 1000


def pong(ping_, ms_rounding=3):
    """Returns the time delta in ms."""
    return round((time.time() * 1000) - ping_, ms_rounding)
