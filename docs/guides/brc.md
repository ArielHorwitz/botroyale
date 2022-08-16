# Bot Royale Championships

The **BRC** is a series of events meant to foster competition among bot developers.

> The BRC is still a new concept, and all notes here are tentative.

*Updated for BRC 1*

*Categories: rules, guides*

## How To Compete
> Remember! The bots are competing, humans are only there to watch.

A special (protected) branch `competition/BRC#` will be created in advance as the official version that will be played during the event. It is recommended to write and test your bots off of this branch if they are to compete.

1. [Write a bot](../guides/simple_bot.html) following the [code rules](#code-rules).
2. Push to a new branch and make a pull request into the `competition/BRC#` branch of the event.
3. The code must be reviewed and accepted by the event organizers.

This must be completed before the **registration deadline** as announced in the proper channels, ensuring the the code can be inspected and reviewed to comply with the rules before the event.

## Code Rules
- Bots may not print to console (or cause output to the console) by any means other than the `api.bots.BaseBot.logger()` method.
- Bots are not to use unintended exploits, such as accessing attributes that were not meant to be exposed or modifying attributes that were not meant to be modifiable.
- Bots are not allowed to "cooperate" (specifically, they may not understand what class is any particular unit).

## Competition Rules
- All bots must pass the bot timing test for competition from the CLI, as part of the event (right before the games start). To run this test run the "cli" script: `python main.py cli`. See also: `api.time_test.timing_test` and `run.cli.run_competitive_timing_test`
- A bot found to be breaking the [code rules](#code-rules) will be instantly disqualified from the event.
- A bot that crashes (or causes a crash) for any reason will be instantly disqualified from the event.
- If the blocking time (of code execution) over a bot's whole turn (i.e. regarless of how many steps the turn takes) is longer than 10 seconds, it will be instantly disqualified from the event.
