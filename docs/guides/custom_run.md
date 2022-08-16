## Running a custom script: step by step

In this guide, we will learn how to run a custom script in the project, allowing us to run our own battles programmatically.

This is particularly useful if you need to run many battles without the GUI (e.g. you are implementing a bot that will use machine learning).

*Updated for version 1.000*

### Start
Make sure you have Bot Royale installed correctly and create a new file in the *run* folder, e.g. `myscript.py`.

Let's begin with this simple boilerplate:
```python
def run():
    """This function will be called (without arguments) when the program starts."""
    print('='*50)
    print('Welcome to Bot Bootcamp.')
    print('='*50)
```

To run this script, run:

`python main.py myscript`

We should see "Welcome to Bot Bootcamp" printed in console.

### Playing a battle without the GUI
Let's make some bots play a couple of battles using the `logic.battle.Battle` class:
```python
from logic.battle import Battle


def play_battle() -> Battle:
    """Creates a battle and plays it. Returns the battle object."""
    b = Battle(enable_logging=False)
    b.play_all(print_progress=True)
    return b


def run():
    """This function will be called (without arguments) when the program starts."""
    print('='*50)
    print('Welcome to Bot Bootcamp.')
    print('='*50)
    battle_count = 2
    for i in range(battle_count):
        play_battle()
    print('='*50)
```

When we run this we should see a progress bar. But when the battles are over we see nothing. Let's see who's winning:
```python
...

def get_winner_name(battle: Battle) -> str:
    """Returns the battle winner's name (or "draw")."""
    assert battle.state.game_over
    # Winner can be None or 0 or 1, etc. Make sure to compare to None.
    if battle.winner is None:
        return 'draw'
    winning_bot = battle.bots[battle.winner]
    # A name alone is not enough, we want the id and name as a str
    formatted_name = winning_bot.gui_label
    return formatted_name


def run():
...
    for i in range(battle_count):
        battle = play_battle()
        winner = get_winner_name(battle)
        print(f'Battle #{i+1} winner: {winner}')

...
```

When running the script now, after each battle there should be printed "Battle #_ winner: ____" and either "draw" or the id and name of the bot that won.


### Selecting bots
We want only our bots to play so that we can train them. To manually choose the bots, let's get familiar with `bots.bot_getter`:
```python
...

from bots import bot_getter

MY_BOTS = ['random']

def play_battle() -> Battle:
    """Creates a battle and plays it. Returns the battle object."""
    bots = bot_getter(selection=MY_BOTS, include_testing=True)
    b = Battle(bot_classes_getter=bots, enable_logging=False)
    b.play_all(print_progress=True)
    return b

...
```

The `bots.bot_getter` function has many options, but we are only interested in the *selection* argument to select which bots play. In this example, we make sure to *include_testing* so that our bots are not filtered out.

When we run this script (with `random` bots selected), we should only ever see draws and `random` bots winning because they are the only ones playing. The battle will run very quickly because they are extremely simple bots (<0.1 ms calculation time per step). Depending on the bots, battles may take far, far longer.


### Selecting maps
Suppose we want to train our bots without walls or pits first. Let's select our map for the battle using `logic.maps.get_map_state`:

```python
...
from logic.maps import get_map_state

def play_battle() -> Battle:
    """Creates a battle and plays it. Returns the battle object."""
    initial_state = get_map_state('empty')
    bots = bot_getter(selection=MY_BOTS, include_testing=True)
    b = Battle(
        initial_state=initial_state,
        bot_classes_getter=bots,
        enable_logging=False)
    b.play_all(print_progress=True)
    return b

...
```

The battles are now being played on the `empty` map.


### Final notes
In this guide we learned how to run a custom script in the project in order to run battles without the GUI with our selected map and bots. It is highly recommended to study the `logic.battle.Battle` class for playing battles manually.

> If the docs are confusing or wrong, *please* raise an issue on github.

Our file `myscript.py` should look something like this:
```python
from logic.battle import Battle
from bots import bot_getter
from logic.maps import get_map_state


MY_BOTS = ['random']


def play_battle() -> Battle:
    """Creates a battle and plays it. Returns the battle object."""
    initial_state = get_map_state('empty')
    bots = bot_getter(selection=MY_BOTS, include_testing=True)
    b = Battle(
        initial_state=initial_state,
        bot_classes_getter=bots,
        enable_logging=False)
    b.play_all(print_progress=True)
    return b


def get_winner_name(battle: Battle) -> str:
   """Returns the battle winner's name (or "draw")."""
   assert battle.state.game_over
   # winner can be: None, 0, 1, etc. Make sure to compare to None.
   if battle.winner is None:
       return 'draw'
   winning_bot = battle.bots[battle.winner]
   # A name alone is not enough, we want the id and name as a str
   formatted_name = winning_bot.gui_label
   return formatted_name


def run():
    """This function will be called (without arguments) when the program starts."""
    print('='*50)
    print('Welcome to Bot Bootcamp.')
    print('='*50)
    battle_count = 2
    for i in range(battle_count):
        battle = play_battle()
        winner = get_winner_name(battle)
        print(f'Battle #{i+1} winner: {winner}')
    print('='*50)
```
