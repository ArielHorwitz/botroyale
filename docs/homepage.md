# Bot Royale Documentation
A battle royale for bots. Write your own bots in Python and watch them play!

## Install
```noformat
pip install --upgrade botroyale
```

See the [install guide](guides/install.html) for more details.

## Quickstart
It takes as few as ***7 lines of code*** to [write your own bot](guides/bots/simple.html) and watch it play:

```python
import botroyale as br

class MyBot(br.BaseBot):
    NAME = 'mybot'

    def poll_action(self, state):
      return br.Idle()  # Add bot logic here

br.register_bot(MyBot)
br.run_gui()
```

> **Note:** Bot Royale is still in early development and the API is likely to change somewhat when upgrading to newer versions.

## Resources
- Browse the [guides](guides/index.html) to learn more
- Browse the [API reference](#header-submodules)
- Browse the [source code](https://github.com/ArielHorwitz/botroyale) on GitHub
- Join the [community discord server](https://discord.gg/ADss5FRyqG)


![Preview GIF](preview.gif)
