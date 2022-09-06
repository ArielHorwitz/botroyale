# A Primer on Battles

In this document we describe how battles work from start to finish.


## Map features

- A **pit** kills any unit standing on it.
- A **wall** prevents units from standing on it.
- The **ring of death** kills any unit standing on it or outside of it. The so-called **_death radius_** contracts by 1 every round.


## Rounds and Turns

Every unit receives 50 AP (action points) per round. They may accumulate up to 100 AP. The order of turns in a round is determined by who used the least AP last round (coinflip if tied).

For example, let's imagine a round (with three units): Unit #1 uses 30 AP, then Unit #2 uses 20 AP, and then Unit #3 uses 30 AP. In this case, the turn order of the next round will be either `[2, 1, 3]` or `[2, 3, 1]`. Unit #2 will definitely go first since they used the least AP. Unit #1 and Unit #3 both used exactly 30 AP so they will coinflip to see who goes first.


## Turns and Steps

When a round begins and the turn order is prepared, each unit will have their turn. On their turn, the battle will repeatedly poll them for an action and apply it to the game (see: `api.actions`). These events are known as `steps`. After every step the battle will poll the unit again on the next step. If the action is an _idle_ action, it ends the turn and then next unit's turn will begin on the following step. If the action is illegal for any reason, it is as if an _idle_ action was played.


## Rules

The rules of the game can be summarized as follows:

- A unit standing on a pit or outside the ring of death will die.
- A unit may not use an action with insufficient AP.
- A unit may not share a tile with a wall or another unit (dead or alive).


## Win Condition (last bot standing)

A battle is over when 0 or 1 units remain alive. If 0 units remain alive it is a draw (e.g. when the last 2 surviving units both die on the same step by the ring of death contracting).

If a single unit remains alive it is the winner.
