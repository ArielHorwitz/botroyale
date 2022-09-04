"""An example custom script (see source code).

Copy this file to: "run/my_script.py"

To run the script, supply the module name ("my_script") in the main program
arguments (see "main.py --help"). If found, it will be imported. If it is
imported and it has a callable attribute `run`, then it will be called without
arguments.
"""
from typing import Optional
from logic.battle import Battle
from logic.maps import get_map_state
from bots.random_bot import SleeperBot


def play_battle(map_name: Optional[str] = None) -> Battle:
    """Example of playing a battle without the GUI."""
    b = Battle(
        initial_state=get_map_state(map_name),
        enable_logging=False,
        bot_classes_getter=lambda n: [SleeperBot] * n,
    )
    b.play_all(print_progress=True)
    return b


def play_many(battle_count: int = 1):
    """Example of playing many battles automatically."""
    SleeperBot.sleep_time = 0.1  # For demo purposes, not important
    for i in range(battle_count):
        game_over = play_battle("empty")
        if game_over.winner is not None:
            winner_name = game_over.bots[game_over.winner].gui_label
        else:
            winner_name = "Draw!"
        print(
            f"Game #{str(i+1):>3}/{str(battle_count):>3} played, "
            f"winner: {winner_name}"
        )
        print(f"Longest survivors: {list(reversed(game_over.state.death_order))}")
    print(f"Finished running {battle_count} battles.")


def run():
    """Called without parameters after the module is imported."""
    # Add code here for playing battles, training bots, etc.
    play_many(3)
