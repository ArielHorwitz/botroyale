from dataclasses import dataclass
import multiprocessing as mp
from typing import List, Callable, Tuple, Any, Iterable
import random
import numpy as np

from bots.botural_selection.base import EvolvingBot

bot_pool_lock = mp.Lock()  # this needs to be in the global scope


@dataclass
class EvolutionConfig:
    # map_getter: Callable
    # bot_getter: Callable
    # n_bots: int
    # out_path: str
    n_processes: int = 2
    max_time: int = 30
    max_rounds: int = 10_000
    # existing_pool: str
    elimination_factor: float = 1.2
    reproduction_factor: float = 1.2


MapGetter = Callable[[], Any]
BattleFunc = Callable[[List[EvolvingBot], MapGetter], np.ndarray]
WorkerArgs = Tuple[
    EvolutionConfig, int, int, float, Callable, List[EvolvingBot], BattleFunc
]
WorkerArgsGetter = Callable[[EvolutionConfig, List[EvolvingBot]], WorkerArgs]


def run_battle(bots: List[EvolvingBot], map_getter) -> np.ndarray:
    # TODO run the battle, and return the scores/ranking
    ...


def rank_bots(
    bots: List[EvolvingBot],
    n_games: int,
    map_getter: MapGetter,
    battle_func: BattleFunc = run_battle,
) -> np.ndarray:
    scores = np.stack([battle_func(bots, map_getter) for _ in range(n_games)])
    scores = np.mean(scores, axis=0)
    return scores


def eliminate_by_ranking(
    bots: List[EvolvingBot],
    scores: np.ndarray,
    n_eliminate: int,
    elimination_factor: float,
) -> Iterable[int]:
    # assuming that scores[i] is the number of rounds bots[i] survived:
    elimination_probabilities = 1 / np.power(scores, elimination_factor)
    elimination_probabilities /= sum(elimination_probabilities)
    eliminated_bots = np.random.choice(
        len(bots), size=n_eliminate, p=elimination_probabilities, replace=False
    )
    return eliminated_bots


def generate_offspring_by_ranking(
    survivors: List[EvolvingBot],
    scores: np.ndarray,
    n_offspring: int,
    reproduction_factor: float,
) -> List[EvolvingBot]:
    reproduction_probabilities = np.power(scores, reproduction_factor)
    reproduction_probabilities /= sum(reproduction_probabilities)
    offspring = [
        survivors[i].mutate()
        for i in np.random.choice(
            len(survivors), p=reproduction_probabilities, size=n_offspring
        )
    ]
    return offspring


def worker(
    config, n_games, n_bots, elimination_ratio, map_getter, bot_pool, battle_func
):
    bots = select_from_bot_pool(n_bots, bot_pool)
    n_eliminate = int(elimination_ratio * len(bots))
    if n_eliminate == 0:
        add_to_bot_pool(bots, bot_pool)
        return
    scores = rank_bots(bots, n_games, map_getter, battle_func)
    eliminated_indices = eliminate_by_ranking(
        bots, scores, n_eliminate, config.elimination_factor
    )
    survivors, scores = zip(
        *[
            (bot, score)
            for i, (bot, score) in enumerate(zip(bots, scores))
            if i not in eliminated_indices
        ]
    )
    replacements = generate_offspring_by_ranking(
        list(survivors), np.array(scores), n_eliminate, config.reproduction_factor
    )
    add_to_bot_pool(list(survivors) + list(replacements), bot_pool)


def select_from_bot_pool(n_bots, bot_pool):
    # TODO: maybe keep bots in file instead of memory? Or I could save to disk every X minutes
    with bot_pool_lock:
        random.shuffle(bot_pool)
        selection = [bot_pool.pop() for _ in range(min(n_bots, len(bot_pool)))]
    return selection


def add_to_bot_pool(new_bots, bot_pool):
    with bot_pool_lock:
        bot_pool += new_bots
        if check_backup_condition():
            backup_to_disk(bot_pool)


def backup_to_disk(bot_pool):
    ...


def check_backup_condition() -> bool:
    # TODO
    return False


def get_worker_args(config, bot_pool: Iterable[EvolvingBot]) -> WorkerArgs:
    # get args to a worker from Config
    ...


def run_evolution(
    config: EvolutionConfig,
    bot_pool: List[EvolvingBot],
    worker_args_getter: WorkerArgsGetter = get_worker_args,
):
    if config.n_processes is None:
        config.n_processes = mp.cpu_count() - 2
    shared_bot_pool = mp.Manager().list(bot_pool)
    with mp.Pool(config.n_processes) as pool:
        r = pool.starmap_async(
            worker,
            [
                worker_args_getter(config, shared_bot_pool)
                for _ in range(config.max_rounds)
            ],
        )
        try:
            r.get(timeout=config.max_time)
        except mp.context.TimeoutError:
            # TODO maybe log something
            pass
    return list(shared_bot_pool)


def parse_args():
    ...


def get_config(args) -> EvolutionConfig:
    ...


if __name__ == "__main__":
    args = parse_args()
