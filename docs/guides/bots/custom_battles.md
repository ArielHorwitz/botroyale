# Playing Battles Without the GUI

In this guide, we will learn how to run our own battles programmatically. This is particularly useful if you need to run many battles without the GUI (e.g. you are implementing a bot that will use machine learning).

## Start
[Install Bot Royale](../install.html) and create your python script (e.g. `main.py`). Let's make some bots play a couple of battles using the `botroyale.logic.battle.Battle` class:
```python
# main.py
import botroyale as br
from botroyale.logic.battle import Battle


def play_battle() -> Battle:
    """Creates a battle and plays it. Returns the battle object."""
    b = Battle(enable_logging=False)
    b.play_all(print_progress=True)
    return b


def run(battle_count: int = 2):
    for i in range(battle_count):
        play_battle()


if __name__ == "__main__":
    run()
```

When we run this we should see a progress bar. But when the battles are over we see nothing. Let's see who's winning using `botroyale.logic.battle.Battle.winner` and `botroyale.api.bots.BaseBot.gui_label`:
```python
...

def get_winner_name(battle: Battle) -> str:
    """Returns the battle winner's name (or "draw")."""
    assert battle.state.game_over
    # Winner can be None or 0 or 1, etc. Make sure to compare to None.
    if battle.winner is None:
        return 'draw'
    winning_bot = battle.bots[battle.winner]
    # A name alone is not enough since there may be many bots per battle with
    # the same name, let's find the ID and the name (as shown in the GUI).
    full_name = winning_bot.gui_label  # string of "#ID. BOTNAME"
    return full_name


def run(battle_count: int = 2):
    for i in range(battle_count):
        battle = play_battle()
        winner = get_winner_name(battle)
        print(f'Battle #{i+1} winner: {winner}')

...
```

When running the script now, after each battle there should be printed `"Battle #_ winner: ____"` and either `"draw"` or the id and name of the bot that won.


## Selecting bots
We want only our bots to play so that we can train them. To manually choose the bots, let's get familiar with `botroyale.api.bots.bot_getter`:
```python
...

from botroyale.api.bots import bot_getter

MY_BOTS = ['random']

def play_battle() -> Battle:
    """Creates a battle and plays it. Returns the battle object."""
    bots = bot_getter(selection=MY_BOTS, include_testing=True)
    b = Battle(
        bot_classes_getter=bots,
        enable_logging=False,
    )
    b.play_all(print_progress=True)
    return b

...
```

The `botroyale.api.bots.bot_getter` function has many options, but we are only interested in the *selection* argument to select which bots play. We also set *include_testing* to true so that no bots will get filtered.

When running the script now (with only the `"random"` bot selected), we should only ever see draws and `"random"` bots winning because they are the only ones playing. The battle will run very quickly because they are extremely simple bots (<0.1 ms calculation time per step). Depending on the map and the bots, battles may take far, far longer.


## Selecting maps
Suppose we want to train our bots without walls or pits first. Let's select our map for the battle using `botroyale.logic.maps.get_map_state`:

```python
...

from botroyale.api.bots import bot_getter
from botroyale.logic.maps import get_map_state

INITIAL_STATE = get_map_state('classic')
MY_BOTS = ['random']

def play_battle() -> Battle:
    """Creates a battle and plays it. Returns the battle object."""
    bots = bot_getter(selection=MY_BOTS, include_testing=True)
    b = Battle(
        initial_state=INITIAL_STATE,
        bot_classes_getter=bots,
        enable_logging=False,
    )
    b.play_all(print_progress=True)
    return b

...
```

The battles are now being played on the `classic` map.


## Final notes
In this guide we learned how to run a custom script in the project in order to run battles without the GUI with our selected map and bots. It is highly recommended to study the `botroyale.logic.battle.Battle` class for playing battles manually.

> If the docs are confusing or wrong, *please* raise an issue on github.

Our script `main.py` should look something like this:
```python
# main.py
import botroyale as br
from botroyale.logic.battle import Battle
from botroyale.api.bots import bot_getter
from botroyale.logic.maps import get_map_state


INITIAL_STATE = get_map_state('classic')
MY_BOTS = ['random']


def play_battle() -> Battle:
    """Creates a battle and plays it. Returns the battle object."""
    bots = bot_getter(selection=MY_BOTS, include_testing=True)
    b = Battle(
        initial_state=INITIAL_STATE,
        bot_classes_getter=bots,
        enable_logging=False,
    )
    b.play_all(print_progress=True)
    return b


def get_winner_name(battle: Battle) -> str:
    """Returns the battle winner's name (or "draw")."""
    assert battle.state.game_over
    # Winner can be None or 0 or 1, etc. Make sure to compare to None.
    if battle.winner is None:
        return 'draw'
    winning_bot = battle.bots[battle.winner]
    # A name alone is not enough since there may be many bots per battle with
    # the same name, let's find the ID and the name (as shown in the GUI).
    full_name = winning_bot.gui_label  # string of "#ID. BOTNAME"
    return full_name


def run(battle_count: int = 2):
    for i in range(battle_count):
        battle = play_battle()
        winner = get_winner_name(battle)
        print(f'Battle #{i+1} winner: {winner}')


if __name__ == "__main__":
    run()
```
