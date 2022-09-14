# Writing a Simple Bot

In this guide, we will learn how to write a simple bot that will play in bot royale.

See also: [A primer on rules and mechanics](mechanics_primer.html) and  [Using the GUI app](../ui/gui.html)

## Setting Up
[Install Bot Royale](../install.html) and create your python script (e.g. `main.py`). Let's begin with this simple boilerplate:
```python
# main.py
import botroyale as br


class MyBot(br.BaseBot):
    NAME = 'testing new bot'

    def poll_action(self, state):
        return br.Idle()


br.register_bot(MyBot)
br.run_gui()
```

When we run this script it creates a bot that always idles, registers it, and then runs the app. In the main menu, we can select our new bot ("testing new bot" is their name) and start a new battle.

## Actions
Our new bot isn't doing anything - it is using the `botroyale.api.actions.Idle` action every time. The idle action ends our turn. Let's make our bot use the `botroyale.api.actions.Move` action.

The `botroyale.api.actions.Move` action takes a *target* parameter (of type `botroyale.util.hexagon.Hexagon`). The *target* is where we want to move to. We also know that Move only allows moving 1 distance away. So we must find our target hex that is 1 distance away from us. This is done very easily with `botroyale.util.hexagon.Hexagon.neighbors`.

Let's adjust the code in `poll_action`:

```python
# main.py
import random
import botroyale as br


class MyBot(br.BaseBot):
    NAME = 'testing new bot'

    def poll_action(self, state):
        """Called by the battle as long as it is our turn. Returns an Action."""
        my_pos = state.positions[self.id]  # Find our position
        move_targets = my_pos.neighbors  # Find our possible targets
        target = random.choice(move_targets)  # Choose a neighbor at random
        return br.Move(target)


br.register_bot(MyBot)
br.run_gui()
```

Now our bot will move to a random direction every time. However it is also showing some glaring issues: it may kill itself by moving outside the ring of death or onto a pit, it may make an illegal action by bumping into other units or walls, and it always ends it's turn with an illegal action (because of missing AP).

> **Note:** If for any reason the code causes a crash, the bot will be killed instead (showing a death icon with a red background). If this happens, you know the code has an error that is logged; see console output. Illegal actions have no penalty except that they end the turn (as if `botroyale.api.actions.Idle` was used).

## Inspecting the state object
Let's fix some of these issues. First we will avoid suicide by checking the ring of death and pits with a new `check_safe` function that we will write. Then we will avoid illegal moves by using the `botroyale.logic.state.State.check_legal_action()` method. We will use `botroyale.api.bots.center_distance` to check our distance from the center of the map.


```python
# main.py
import random
import botroyale as br
from botroyale.api.bots import center_distance


class MyBot(br.BaseBot):
    NAME = 'testing new bot'

    def poll_action(self, state):
        """Called by the battle as long as it is our turn. Returns an Action."""
        my_pos = state.positions[self.id]  # Find our position
        move_targets = my_pos.neighbors  # Find our possible targets
        # Filter out targets that are not safe
        safe_targets = [hex for hex in move_targets if self.check_safe(state, hex)]
        random.shuffle(safe_targets)  # Randomizing for demo purposes
        # Look for a legal action with our safe targets
        while safe_targets:
            next_target = safe_targets.pop(0)
            action = br.Move(next_target)
            if state.check_legal_action(action=action):
                return action
        # No move targets were safe and legal, let's finish our turn
        return br.Idle()

    def check_safe(self, state, hex):
        """Check if it is safe to move to a tile."""
        if center_distance(hex) >= state.death_radius - 1:
            # This hex is outside or threatened by the ring of death
            return False
        if hex in state.pits:
            # This hex has a pit
            return False
        return True


br.register_bot(MyBot)
br.run_gui()
```

Now when we run the game, our bot doesn't suicide and does legal actions only. I see you're getting the hang of this, so I'll let you continue from here :)

## Final notes
In this guide we learned how to write a simple bot that can play and is aware of the game state. It is highly recommended to study the [bot developer API](../../api/index.html#api-for-bot-developers).
