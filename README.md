# Bot Royale
A battle royale for bots. Write your own bots in Python and watch them play!

![Preview GIF](/botroyale/assets/preview.gif)

## Quickstart
```noformat
pip install botroyale
```
It takes as few as ***7 lines of code*** to [write your own bot](guides/bots/simple.html) and watch it play!

```python
# main.py -- Run this script with Python
import botroyale as br

class MyBot(br.BaseBot):
    NAME = 'mybot'

    def poll_action(self, state):
      return br.actions.Idle()

br.register_bot(MyBot)
br.run_gui()
```

## Guides and Documentation
Browse the [docs](https://ariel.ninja/botroyale/docs/) for guides and API reference to learn more.

## Community and Contributing
Join us in the community [discord server](https://discord.gg/ADss5FRyqG).
