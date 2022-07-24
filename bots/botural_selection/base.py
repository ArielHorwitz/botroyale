from typing import Tuple, Optional
from abc import ABC, abstractclassmethod
import numpy as np
import uuid

from api.bots import BaseBot

BotID = uuid.UUID
ParameterShapeType = Tuple[int, ...]


class EvolvingBot(BaseBot, ABC):

    PARAMETER_SHAPE: Tuple[ParameterShapeType, ...] = NotImplemented

    def __init__(
        self,
        parameters: Optional[Tuple[np.ndarray, ...]] = None,
        parameters_path: Optional[str] = None,
    ):
        if parameters is None:
            if parameters_path is None:
                raise ValueError(
                    "either parameters must be passed, or a path to a parameters file"
                )
            with open(parameters_path, "rb") as f:
                parameters_npz = np.load(f)
                parameters = tuple(
                    (parameters_npz[arr] for arr in parameters_npz.files)
                )
        parameters_shape = tuple(p.shape for p in parameters)
        if parameters_shape != self.__class__.PARAMETER_SHAPE:
            raise ValueError(
                f"{self.__class__.__name__} was instantiated with parameters of the wrong shape."
                f"\nExpected: {self.__class__.PARAMETER_SHAPE},\nGot: {parameters_shape}"
            )

        self.parameters: Tuple[np.ndarray, ...] = parameters
        self.id: BotID = uuid.uuid1()

    def __eq__(self, other):
        if other.__class__ == self.__class__:
            return self.id == other.id
        return False

    @abstractclassmethod
    def _get_action(cls, state, parameters):
        raise NotImplementedError

    @abstractclassmethod
    def _get_mutation(cls, parameters):
        """Get a new set of parameters which are a random mutation of the input parameters"""
        raise NotImplementedError

    @abstractclassmethod
    def _get_mating_result(cls, parameters1, parameters2):
        """Get a new set of parameters which are the offspring of two other sets of parameters"""

    def poll_action(self, state):
        return self.__class__._get_action(state, self.parameters)

    def mutate(self):
        mutated = self.__class__._get_mutation(self.parameters)
        return self.__class__(mutated)

    def __hash__(self):
        return self.id.__hash__()
