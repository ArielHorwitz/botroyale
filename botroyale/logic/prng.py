"""LCG (linear congruential generator).

https://en.wikipedia.org/wiki/Linear_congruential_generator

We implement a very transparent and simple pseudo-rng, so that other
implementations may easily mimic it. It is designed for state logic and
should not be used directly.
"""
from typing import Optional
import random


# Parameters mimicing those from glibc
MOD = 2**31
MUL = 1103515245
INC = 12345


# Assumptions of the LCG algorithm
assert isinstance(MOD, int)
assert isinstance(MUL, int)
assert isinstance(INC, int)
assert 0 < MOD
assert 0 < MUL < MOD
assert 0 <= INC < MOD


# Pseudo Random Number Generator
class PRNG:
    """A simple implementation of LCG as a python Generator.

    LCG is an algorithm for generating a pseudo-random value from a given value.
    As such, an infinitely iterable PRNG can be made by simply stringing a
    previous value as the "seed" for the next value.

    LCG uses integers, however we are interested in providing normalized
    values. When iterating, a new integer value is derived and stored, and it
    is returned as a float between 0 and 1.

    This is why we expect an integer for the seed when initializing the object,
    but return floats when iterating. Passing None as a seed argument will
    generate a random seed value.


    <u>__Example usage:__</u>
    ```python
    # Create a PRNG generator with a random seed
    rng = PRNG()
    # Make a copy
    rng_copy = rng.copy()  # equivalent to: rng_copy = PRNG(rng.seed)
    # Make an unrelated generator (new random seed)
    rng_other = PRNG()
    # Generate a list of values and save them
    a, b = rng.generate_list(2)
    # Iterate values and save the last one
    b_ = rng_copy.iterate(2)
    # The following two assersions will pass
    assert b == b_
    assert rng_other.iterate(2) != rng.value
    assert next(rng) == next(rng_copy)
    ```
    """

    def __init__(self, seed: Optional[int] = None):
        """Initialize the class."""
        if seed is None:
            seed = self.get_random_seed()
        assert isinstance(seed, int)
        assert 0 <= seed < MOD
        self.__current_seed: int = seed
        self.__current_value: float = seed / MOD

    def iterate(self, count: int) -> float:
        """Iterates a number of times and returns the last value."""
        while count > 0:
            next(self)
            count -= 1
        return self.__current_value

    def generate_list(self, size: int) -> list[float]:
        """Generates a list of values."""
        return [next(self) for i in range(size)]

    @property
    def seed(self) -> int:
        """The current seed."""
        return self.__current_seed

    @property
    def value(self) -> float:
        """The last value that was generated."""
        return self.__current_value

    @staticmethod
    def get_random_seed() -> int:
        """A random seed that is valid as `PRNG.seed`."""
        return random.randint(0, MOD - 1)

    def copy(self) -> "PRNG":
        """A copy of *self* with the same `PRNG.seed`."""
        return self._do_copy(self)

    @classmethod
    def _do_copy(cls, original: "PRNG") -> "PRNG":
        return cls(original.seed)

    # Python generator protocol
    def __iter__(self) -> "PRNG":
        """Iter."""
        return self

    def __next__(self) -> float:
        """Next."""
        self.__current_seed = (self.__current_seed * MUL + INC) % MOD
        self.__current_value = self.__current_seed / MOD
        return self.__current_value
