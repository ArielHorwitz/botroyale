# Writing a Simple Bot

In this guide, we will learn how to write a simple bot that will play in bot royale.

See also: [A primer on rules and mechanics](../mechanics_primer.html) and  [Using the GUI app](../ui/gui.html)

## Setting Up
[Install Bot Royale](../install.html) and create your python script (e.g. `main.py`). Let's begin with this simple boilerplate:
```python
# main.py
import botroyale as br


class MyBot(br.BaseBot):
    NAME = 'testing new bot'

    def poll_action(self, state):
        action = br.actions.Idle()
        return action

br.register_bot(MyBot)
br.run_gui()
```

When we run this script it creates a bot that always idles, registers it, and then runs the app. In the main menu, we can select our new bot ("testing new bot" is their name) and start a new battle.

## Actions
Our new bot isn't doing anything - it is using the `botroyale.api.actions.Idle` action every time. The idle action ends our turn. Let's make our bot use the `botroyale.api.actions.Move` action.

The `botroyale.api.actions.Move` action takes a *target* parameter (of type `botroyale.util.hexagon.Hexagon`). The *target* is where we want to move to. We also know that Move only allows moving 1 distance away. So we must find our target hex that is 1 distance away from us. This is done very easily with `botroyale.util.hexagon.Hexagon.neighbors`.

Let's adjust the code in `poll_action` (we need to import `botroyale.api.actions.Move` and python's `random` for this to work):

```python
def poll_action(self, state):
    """Called by the battle as long as it is our turn. Returns an Action."""
    # Find our position
    my_pos = state.positions[self.id]
    # Find our possible targets
    move_targets = my_pos.neighbors
    # Choose a neighbor at random
    target = random.choice(move_targets)
    return Move(target)
```

Now our bot will move to a random direction every time. However it is also showing some glaring issues: it may kill itself by moving outside the ring of death or onto a pit, it may make an illegal action by bumping into other units or walls, and it always ends it's turn with an illegal action (because of missing AP).

> Illegal actions have no penalty except that they end the turn (as if `botroyale.api.actions.Idle` was used).


## Inspecting the state object
Let's fix some of these issues. First we will avoid suicide by checking the ring of death and pits with a new `check_safe` function that we will write. Then we will avoid illegal moves by using the `botroyale.logic.state.State.check_legal_action()` method. We will import `botroyale.api.bots.center_distance` to check our distance from the center of the map.


```python
def poll_action(self, state):
    """Called by the battle as long as it is our turn. Returns an Action."""
    # Find our position
    my_pos = state.positions[self.id]
    # Find our possible targets
    move_targets = my_pos.neighbors
    # Filter out targets that are not safe
    safe_targets = [hex for hex in move_targets if self.check_safe(state, hex)]
    random.shuffle(safe_targets)  # Randomizing for demo purposes
    # Look for a legal action with our safe targets
    while safe_targets:
        next_target = safe_targets.pop(0)
        action = Move(next_target)
        if state.check_legal_action(action=action):
            return action
    # No move targets were safe and legal, let's finish our turn.
    return Idle()

def check_safe(self, state, hex):
    """Check if it is safe to move to a tile."""
    if center_distance(hex) >= state.death_radius:
        # This hex is outside the ring of death
        return False
    if hex in state.pits:
        # This hex has a pit
        return False
    return True
```

Now when we run the game, our bot doesn't suicide and does legal actions only. I see you're getting the hang of this, so I'll let you continue from here :)

## Final notes
In this guide we learned how to write a simple bot that can play and is aware of the game state. It is highly recommended to study the following docs for developing bots:

- `botroyale.logic.state.State` objects are used to represent the state of the game.
- `botroyale.util.hexagon.Hexagon` objects are used to represent any sort of position or location.
- `botroyale.api.actions` are the actions we can take on our turn.
- `botroyale.api.bots` to learn about our Bot's base class.

> If the docs are confusing or wrong, *please* raise an issue on github.
