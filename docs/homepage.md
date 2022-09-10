# Bot Royale Documentation
A battle royale for bots. Write your own bots in Python and watch them play!

## Install
```noformat
pip install --upgrade botroyale
```

See the [install guide](guides/install.html) for more details.

## Quickstart
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

See the guide on [writing your first bot](guides/bots/simple.html).

## Resources
- Browse the [guides](guides/index.html) to learn more.
- Browse the [API reference](#header-submodules).
- Browse the [source code](https://github.com/ArielHorwitz/botroyale) on GitHub.

![Preview GIF](preview.gif)
