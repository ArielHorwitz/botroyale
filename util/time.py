"""
Time utilities.
"""
__pdoc__ = {
    'RateCounter': False,
    'ratecounter': False,
}


from typing import Optional, Callable
import time
import contextlib
import numpy as np


def ping() -> float:
    """Generate a time value to be later used by `pong`."""
    return time.perf_counter() * 1000


def pong(ping_: float) -> float:
    """Return the time delta in ms from a value given by `ping`."""
    return (time.perf_counter() * 1000) - ping_


@contextlib.contextmanager
def pingpong(
        description: str='Pingpong',
        logger: Optional[Callable[[str], None]] = None,
        return_elapsed: Optional[Callable[[float], None]] = None
        ):
    """
    A context manager to print and record the elapsed time of execution of a code block.

    Args:
        description: Description to add to the logging callback.
        logger: Callback that takes a string with the pingpong result.
        return_elapsed: Callback that takes a float of the pingpong result.

    <u>__Example usage:__</u>
    ```
    with pingpong('Counting to a million', logger=print, return_elapsed=callback):
        count = 0
        for i in range(1_000_000):
            count += 1
    ```
    Will result in a console output:
    ```'Counting to a million elapsed in: 1.234 ms'```

    And will call `callback` with an argument `1.234`.
    """
    p = ping()
    yield p
    elapsed = pong(p)
    if callable(logger):
        logger(f'{description} elapsed in: {elapsed:.3f} ms')
    if callable(return_elapsed):
        return_elapsed(elapsed)


class RateCounter:
    """A simple rate counter (e.g. for FPS)"""

    def __init__(self, sample_size=120, starting_elapsed=1000):
        super().__init__()
        self.last_count = ping()
        self.__sample_size = sample_size
        self.sample = np.ones(self.sample_size, dtype=np.float64) * starting_elapsed
        self.__sample_index = 0

    @property
    def sample_size(self):
        return self.__sample_size

    def ping(self):
        self.last_count = ping()

    def pong(self):
        return self.tick()

    def start(self):
        self.last_count = ping()

    def tick(self):
        p = pong(self.last_count)
        self.last_count = ping()
        self.__sample_index = (self.__sample_index + 1) % self.sample_size
        self.sample[self.__sample_index] = p
        return p

    @property
    def rate(self):
        return 1000 / self.mean_elapsed_ms

    @property
    def rate_ms(self):
        return 1 / self.mean_elapsed_ms

    @property
    def mean_elapsed(self):
        return np.mean(self.sample) / 1000

    @property
    def mean_elapsed_ms(self):
        return np.mean(self.sample)

    @property
    def current_elapsed(self):
        return pong(self.last_count) / 1000

    @property
    def current_elapsed_ms(self):
        return pong(self.last_count)

    @property
    def last_elapsed(self):
        return self.sample[self.__sample_index] / 1000

    @property
    def last_elapsed_ms(self):
        return self.sample[self.__sample_index]

    @property
    def timed_block(self):
        return ratecounter(self)


@contextlib.contextmanager
def ratecounter(r: RateCounter):
    """A context manager to record elapsed time of execution of a code block, using a RateCounter object."""
    p = r.ping()
    yield p
    r.pong()
