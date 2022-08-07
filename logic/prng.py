"""
LCG (linear congruential generator)
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
    """
    def __init__(self, seed: Optional[int] = None):
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
        """Returns the current seed."""
        return self.__current_seed

    @property
    def value(self) -> float:
        """Returns the last value that was generated."""
        return self.__current_value

    @staticmethod
    def get_random_seed() -> int:
        return random.randint(0, MOD-1)

    def copy(self) -> 'PRNG':
        return self._do_copy(self)

    @classmethod
    def _do_copy(cls, original: 'PRNG') -> 'PRNG':
        return cls(original.seed)

    # Python generator protocol
    def __iter__(self) -> 'PRNG':
        return self

    def __next__(self) -> float:
        self.__current_seed = (self.__current_seed * MUL + INC) % MOD
        self.__current_value = self.__current_seed / MOD
        return self.__current_value
