import numpy as np
from bots.botural_selection import selection
from bots.botural_selection.tests.bot import (
    MockBot,
    mock_battle,
    mock_getter,
    mock_map_getter_fixed,
    mock_worker_args_getter,
)


def test_eliminate_by_ranking_results_in_less_but_the_same_bots():
    n_bots = np.random.randint(10, 100)
    bots = MockBot.get_random_bot_list(n_bots)
    ranking = mock_battle(bots)
    n_eliminate = np.random.randint(0, n_bots)
    eliminated = selection.eliminate_by_ranking(bots, ranking, n_eliminate, 1.2)
    survivors = [bot for i, bot in enumerate(bots) if i not in eliminated]
    survivors_set = set(survivors)
    assert len(survivors) == n_bots - n_eliminate
    assert survivors_set <= set(bots)
    assert len(survivors) == len(survivors_set)


def test_create_mock_bots_and_battle():
    bots = MockBot.get_random_bot_list(10)
    result = mock_battle(bots, target=lambda: np.zeros(3))
    for score, bot in zip(result, bots):
        assert score == 1 / np.linalg.norm(bot.parameters[0])


def test_rank_bots():
    bots = MockBot.get_random_bot_list(10)
    selection.rank_bots(bots, 10, mock_getter, mock_battle)


def test_rank_and_replace():
    n_eliminate = 20
    n_bots = 50
    n_games = 10
    bots = MockBot.get_random_bot_list(n_bots)
    scores = selection.rank_bots(bots, n_games, mock_getter, mock_battle)
    eliminated_indices = selection.eliminate_by_ranking(bots, scores, n_eliminate, 1.2)
    survivors, scores = zip(
        *[
            (bot, score)
            for i, (bot, score) in enumerate(zip(bots, scores))
            if i not in eliminated_indices
        ]
    )
    replacements = selection.generate_offspring_by_ranking(
        list(survivors), np.array(scores), n_eliminate, 1.2
    )
    assert len(list(survivors) + replacements) == n_bots


def test_evolution_increases_score():
    config = selection.EvolutionConfig(n_processes=2, max_time=5, max_rounds=500)
    bot_pool = MockBot.get_random_bot_list(20)
    initial_ranking = np.mean(
        selection.rank_bots(bot_pool, 1, mock_map_getter_fixed, mock_battle)
    )
    bot_pool = selection.run_evolution(config, bot_pool, mock_worker_args_getter)
    assert len(bot_pool) == 20
    final_ranking = np.mean(
        selection.rank_bots(bot_pool, 1, mock_map_getter_fixed, mock_battle)
    )
    print(f"{initial_ranking=}, {final_ranking=}")
    assert final_ranking > initial_ranking
