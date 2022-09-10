# A Primer on Game Mechanics

In this document we describe the game rules and how battles work from start to finish.


## Rules Overview

- Last unit standing wins (may end in a draw).
- A unit standing on a pit or outside the ring of death will die.
- A unit that fails to return an action will die.
- A unit that returns an illegal action will idle.
- A unit may not share a tile with a wall or another unit (dead or alive).


## Rounds and Turns

#### Round order
The order of turns in a round is determined by who used the least AP last round (see below). On the first round and any time two units use the same amount of AP, a coinflip determines who goes first.

#### Turns and AP
Every unit receives 50 AP (action points) per round, and may accumulate up to 100 AP. These action points are used to perform actions in turn. A unit can perform as many legal actions on their turn as they wish. If they idle or try an illegal action, their turn ends.

> **Note:** If a bot fails to return an action, it is killed.


## Map Features

#### Ring of death
The *ring of death* kills any unit standing on it or outside of it. The so-called *death radius* contracts by 1 every round.

#### Common features
A *pit* kills any unit standing on it.

A *wall* prevents units from standing on it or being pushed into it.

#### Advanced features
A *pressure plate* is an advanced mechanic used by some maps. We will discuss this in another guide.


## Winning (last bot standing)

A battle is over when no more than one unit remains alive. If a single unit remains alive it is the winner.

> If no units remain alive it is a draw (e.g. when the last 2 surviving units both die on the same step by the ring of death contracting).
