# Writing a Simple Bot

In this guide, we will learn how to write a simple bot that will play in bot royale.

## Start
Make sure you have Bot Royale installed correctly and create a new file in the *bots* folder, e.g. `mybot.py`.


Let's begin with this simple boilerplate:
```python
from api.bots import BaseBot
from api.actions import Idle


class MyBot(BaseBot):
    NAME = 'testing new bot'

    def poll_action(self, state):
        action = Idle()
        return action


BOT = MyBot
```

We should have a new bot that can join games. To test, we simply run the game and make sure to include our new bot ("testing new bot" is their name) by clicking on them in the main menu under "Include" and starting a new battle.

## Actions
Our new bot isn't doing anything - it is using the `botroyale.api.actions.Idle` action every time. The idle action ends our turn. Let's make our bot use the `api.actions.Move` action.

The `api.actions.Move` action takes a *target* parameter (of type `util.hexagon.Hexagon`). The *target* is where we want to move to. We also know that Move only allows moving 1 distance away. So we must find our target hex that is 1 distance away from us. This is done very easily with `botroyale.util.hexagon.Hexagon.neighbors`.

Let's adjust the code in `poll_action` (we need to import `api.actions.Move` and python's `random` for this to work):

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

Now our bot will move to a random direction every time. However it is also showing some glaring issues: it may kill itself by moving outside the ring of death or onto a pit, and it always ends it's turn with an illegal action.

> Illegal actions have no penalty except that they end the turn (as if `api.actions.Idle` was used).


## Inspecting the state object
Let's fix some of these issues. First we will avoid suicide by checking the ring of death and pits with a new `check_safe` function that we will write. Then we will avoid illegal moves by using the `logic.state.State.check_legal_action()` method. We will import `api.bots.center_distance` to check our distance from the center of the map.


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

- `logic.state.State` objects are used to represent the state of the game.
- `util.hexagon.Hexagon` objects are used to represent any sort of position or location.
- `api.actions` are the actions we can take on our turn.
- `api.bots` to learn about our Bot's base class.

> If the docs are confusing or wrong, *please* raise an issue on github.


# Common functions as examples

The following are some of the common functions that beginner bot developers first write.

### Find hex after push
```python
def hex_after_push(my_pos: Hexagon, enemy_pos: Hexagon) - > Hexagon:
    """Return the tile my enemy will land on after I push them."""
    assert enemy_pos in my_pos.neighbors
    after_push_pos = next(my_pos.straight_line(enemy_pos))
    return after_push_pos
```

### Find all moveable hexes on the map
```python
def moveable_tiles(state: State) -> set[Hexagon]:
    """Return a set of all tiles that can be legally moved to without dying."""
    map_center = api.bots.CENTER
    map_tiles = map_center.range(state.death_radius - 1)
    moveables = set(map_tiles) - state.pits - state.walls - set(state.positions)
    return moveables
```

### Find positions of live enemies
```python
def find_enemy_positions(state: State, my_id: int) -> list[Hexagon]:
    """Return a list of live enemy positions."""
    enemy_ids = [id for id in range(state.num_of_units) if id in state.alive_mask and id != my_id]
    enemy_pos = [state.positions[id] for id in enemy_ids]
    return enemy_pos
```
