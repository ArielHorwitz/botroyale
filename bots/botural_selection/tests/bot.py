import numpy as np
from typing import List

from bots.botural_selection.base import EvolvingBot
from bots.botural_selection.selection import WorkerArgs
from api.actions import Idle


class MockBot(EvolvingBot):

    PARAMETER_SHAPE = ((3,), (1,))

    @classmethod
    def _get_action(cls, state, parameters):
        return Idle

    @classmethod
    def _get_mutation(cls, parameters):
        mutation_rate = parameters[1].item()
        p1 = parameters[0] + np.random.normal(
            0, mutation_rate, size=cls.PARAMETER_SHAPE[0]
        )
        p2 = np.abs(parameters[1] + np.random.normal(0, mutation_rate))
        return (p1, p2)

    @classmethod
    def _get_mating_result(cls, parameters1, parameters2):
        return cls._get_mutation((parameters1 + parameters2) / 2)

    @classmethod
    def get_random_bot(cls):
        return MockBot(parameters=(np.random.random(3), np.random.random(size=(1,))))

    @classmethod
    def get_random_bot_list(cls, size) -> List[EvolvingBot]:
        return [MockBot.get_random_bot() for _ in range(size)]


def mock_getter():
    return np.random.normal(size=(3,))


def mock_battle(bots, target=mock_getter):
    bot_params = np.stack([bot.parameters[0] for bot in bots])
    return 1 / (np.linalg.norm(bot_params - target(), axis=1))


def mock_map_getter_fixed():
    return np.array([2, -7, 18])


def mock_worker_args_getter(config, bot_pool) -> WorkerArgs:
    n_games = 1
    n_bots_per_game = 10
    elimination_ratio = 0.3
    battle_func = mock_battle
    return (
        config,
        n_games,
        n_bots_per_game,
        elimination_ratio,
        mock_map_getter_fixed,
        bot_pool,
        battle_func,
    )
