"""Time utilities."""
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
    description: str = "Pingpong",
    logger: Optional[Callable[[str], None]] = None,
    return_elapsed: Optional[Callable[[float], None]] = None,
):
    """A context manager to record the elapsed time of execution of a code block.

    Args:
        description: Description to add to the logging callback.
        logger: Callback that takes a string with the pingpong result.
        return_elapsed: Callback that takes a float of the pingpong result.

    <u>__Example usage:__</u>
    ```python
    with pingpong('Counting to a million', logger=print, return_elapsed=callback):
        count = 0
        for i in range(1_000_000):
            count += 1
    ```
    Will result in a console output: `'Counting to a million elapsed in: 1.234 ms'`

    And will call `callback` with an argument `1.234`.
    """
    p = ping()
    yield p
    elapsed = pong(p)
    if callable(logger):
        logger(f"{description} elapsed in: {elapsed:.3f} ms")
    if callable(return_elapsed):
        return_elapsed(elapsed)


class RateCounter:
    """A simple rate counter (e.g. for FPS)."""

    def __init__(self, sample_size=120, starting_elapsed=1000):
        """Initialize the class.

        Args:
            sample_size: Size of sample of times.
            starting_elapsed: Initial value for all times in sample.
        """
        super().__init__()
        self.last_count = ping()
        self.__sample_size = sample_size
        self.sample = np.ones(self.sample_size, dtype=np.float64) * starting_elapsed
        self.__sample_index = 0

    @property
    def sample_size(self):
        """Size of sample of times."""
        return self.__sample_size

    def ping(self):
        """Start measuring a new time sample."""
        self.last_count = ping()

    def pong(self):
        """Alias for `RateCounter.tick`."""
        return self.tick()

    def start(self):
        """Alias for `RateCounter.ping`."""
        self.last_count = ping()

    def tick(self):
        """Finish measuring a time sample."""
        p = pong(self.last_count)
        self.last_count = ping()
        self.__sample_index = (self.__sample_index + 1) % self.sample_size
        self.sample[self.__sample_index] = p
        return p

    @property
    def rate(self):
        """Mean rate per second."""
        return 1000 / self.mean_elapsed_ms

    @property
    def rate_ms(self):
        """Mean rate per millisecond."""
        return 1 / self.mean_elapsed_ms

    @property
    def mean_elapsed(self):
        """Mean time of samples in seconds."""
        return np.mean(self.sample) / 1000

    @property
    def mean_elapsed_ms(self):
        """Mean time of samples in milliseconds."""
        return np.mean(self.sample)

    @property
    def current_elapsed(self):
        """Elapsed time of current sample in seconds."""
        return pong(self.last_count) / 1000

    @property
    def current_elapsed_ms(self):
        """Elapsed time of current sample in milliseconds."""
        return pong(self.last_count)

    @property
    def last_elapsed(self):
        """Elapsed time of last sample in seconds."""
        return self.sample[self.__sample_index] / 1000

    @property
    def last_elapsed_ms(self):
        """Elapsed time of last sample in milliseconds."""
        return self.sample[self.__sample_index]

    @property
    def timed_block(self):
        """Record a new sample using a context manager.

        Example usage:

        ```python
        r = RateCounter()
        with r.timed_block:
            # Code that requires measuring here
        print(r.mean_elapsed_ms)
        ```
        """
        return ratecounter(self)


@contextlib.contextmanager
def ratecounter(r: RateCounter):
    """A context manager to record execution of a code block to a `RateCounter`.

    See also: `RateCounter.timed_block`.

    Args:
        r: The `RateCounter` object to record to.
    """
    p = r.ping()
    yield p
    r.pong()


__pdoc__ = {
    "RateCounter": False,
    "ratecounter": False,
}
