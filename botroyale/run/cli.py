"""A command line utility for running functions that don't require the GUI.

Uses `input` and `print` to interface with the user.
"""
import argparse
from collections import Counter
from botroyale.api.time_test import timing_test
from botroyale.api.bots import BOTS, BotSelection
from botroyale.logic.maps import MAPS, get_map_state
from botroyale.logic.battle_manager import BattleManager


# Thresholds of bot calculation times for the competitive timing test
COMP_SAMPLE_SIZE = 10
COMP_MAX_MS = 10_000
COMP_MEAN_MS = 5_000
COMP_FAIL_CONDITIONS = (
    f"Fail conditions: mean > {COMP_MEAN_MS:,} ms ; max > {COMP_MAX_MS:,} ms"
)


def run_competitive_timing_test():
    """Run the competitive timing test, print the names of the bots that fail."""
    map_name = query_map_name()
    bot_names = query_bot_names()
    results = timing_test(
        bots=bot_names,
        battle_count=COMP_SAMPLE_SIZE,
        map_name=map_name,
        verbose_results=False,
        shuffle_bots=True,
        disable_logging=True,
    )
    fail_mean = [bn for bn, tr in results.items() if tr.mean > COMP_MEAN_MS]
    fail_max = [bn for bn, tr in results.items() if tr.max > COMP_MAX_MS]
    fail_names = set(fail_max) | set(fail_mean)
    print(f"\n\n{COMP_FAIL_CONDITIONS}\n")
    if fail_names:
        fail_names_str = "\n".join(f"- {f}" for f in fail_names)
        print(f"FAILED:\n{fail_names_str}")
    else:
        print("No fails.")
    print("\n")


def run_regular_timing_test():
    """Run a timing test.

    Continuously prints the results (mean and max calculation time) of each bot.
    """
    ucount = input("\nNumber of battles to play (leave blank for 10,000): ")
    battle_count = int(ucount) if ucount else 10_000
    assert battle_count > 0
    map_name = query_map_name()
    bots = query_bot_names()
    timing_test(bots, battle_count, map_name=map_name)


def run_winrates():
    """Plays many battles, and continuously prints the winrates of each bot."""

    def print_summary():
        print("\n")
        print("           ----------------------------------")
        print(f"               Winrates ({battles_played:,} battles total)")
        print("           ----------------------------------")
        if battles_played <= 0:
            print("Waiting for results of the first game...")
            return
        for bot, wins in counter.most_common():
            print(
                f'{bot:>20}: {f"{wins/battles_played*100:.2f}":>7} % '
                f"({str(wins):<4} wins)"
            )

    counter = Counter()
    battles_played = 0
    map_name = query_map_name()
    initial_state = get_map_state(map_name)
    bots = query_bot_names()
    while True:
        battle = BattleManager(
            initial_state=initial_state,
            bots=BotSelection(bots, all_play=True, keep_fair=True),
            description=f"winrates #{battles_played+1} @ {map_name}",
            enable_logging=False,
        )
        print_summary()
        print(f"\nPlaying battle : {battle.description}\n")
        winner, losers = play_complete(battle)
        print(battle.get_info_panel_text())
        counter[winner] += 1
        for loser in losers:
            counter[loser] += 0
        battles_played += 1
    print_summary()


def query_map_name() -> str:
    """Queries the user in console for a map name."""
    print(
        "\n".join(
            [
                "Available maps:",
                *(f"- {i}. {m}" for i, m in enumerate(MAPS)),
            ]
        )
    )
    while True:
        idx = input("Select map number: ")
        try:
            idx = int(idx)
            assert 0 <= idx < len(MAPS)
            break
        except (ValueError, AssertionError):
            print(f'"{idx}" is not an option.')
    map = MAPS[idx]
    print(f"Selected: {map}")
    return map


def _query_user(available_names, selected_names):
    names = []
    for i, bn in enumerate(available_names):
        in_prefix = "++" if bn in selected_names else "--"
        names.append(f"{str(i):>3}. {in_prefix} {bn}")
        names_str = "\n".join(names)
    print("Bots:\nLegend: -- available ++ selected")
    print(names_str)
    # print('Enter one of the following:')
    print("\nBot selection:")
    print(
        ">  leave blank to finish (if none selected, will select all "
        "non-testing bots)"
    )
    print(">  number to add/remove a bot by number")
    print('>  "a" to add all bots')
    print('>  "r" to remove all bots')
    r = input(">> ")
    print("")
    return r


def query_bot_names() -> list[str]:
    """Queries the user in console for bots. Returns a list of bot names."""
    bot_cls_list = [bot_cls for bot_cls in BOTS.values()]
    sorted_bots = sorted(bot_cls_list, key=lambda botcls: botcls.TESTING_ONLY)
    available_bots = [bot_cls.NAME for bot_cls in sorted_bots]
    available_bots_non_testing = [
        bot_cls.NAME for bot_cls in sorted_bots if not bot_cls.TESTING_ONLY
    ]
    selected_names = []

    # Collect bots
    while True:
        uinput = _query_user(available_bots, selected_names)
        if uinput == "":
            break
        if uinput == "a":  # Add all
            selected_names = [a for a in available_bots]
            continue
        if uinput == "r":  # Remove all
            selected_names = []
            continue
        # Convert to index
        try:
            bot_index = int(uinput)
            bot_name = available_bots[bot_index]
        except (ValueError, IndexError):
            continue
        # Add/remove index
        if bot_name not in selected_names:
            selected_names.append(bot_name)
        else:
            selected_names.remove(bot_name)

    # Fill with all bots if none selected
    if not selected_names:
        selected_names = available_bots_non_testing
    return selected_names


def play_complete(battle: BattleManager) -> tuple[str, list[str]]:
    """Play a battle to completion.

    Args:
        battle: The `botroyale.logic.battle_manager.BattleManager` instance.

    Returns:
        Tuple of (winner name, list of loser names).
    """
    battle.play_all(print_progress=True)
    assert battle.state.game_over
    winner_id = battle.state.winner
    winner = battle.bots[winner_id].name if winner_id is not None else "draw"
    losers = [battle.bots[loser_id].name for loser_id in battle.losers]
    return winner, losers


def entry_point_cli(args):
    """Entry point for the CLI utility."""
    parser = argparse.ArgumentParser(description="Run the CLI utility.")
    parser.parse_args(args)
    while True:
        print(
            "\n".join(
                [
                    "\n\n",
                    "Select operation:",
                    "1. Winrates",
                    "2. Bot timer tests",
                    "3. Bot timer tests for competition",
                    "q. Quit CLI",
                    "",
                ]
            )
        )
        selection = input("Enter selection: ")
        if selection == "q":
            return 0
        selection = int(selection)
        assert 1 <= selection <= 3
        if selection == 1:
            run_winrates()
        elif selection == 2:
            run_regular_timing_test()
        elif selection == 3:
            run_competitive_timing_test()
    return 0
