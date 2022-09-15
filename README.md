# Bot Royale
A battle royale for bots. Write your own bots in Python and watch them play!

![Preview GIF](/botroyale/assets/preview.gif)

## Quickstart
It is recommended to use a [virtual environment](https://docs.python.org/3/tutorial/venv.html). Once activated, install using:
```noformat
pip install botroyale
```
It takes as few as ***7 lines of code*** to [write your own bot](https://ariel.ninja/botroyale/docs/guides/bots/simple.html) and watch it play:

```python
import botroyale as br

class MyBot(br.BaseBot):
    NAME = 'mybot'

    def poll_action(self, state):
      return br.Idle()  # Add bot logic here

br.register_bot(MyBot)
br.run_gui()
```

## Guides and Documentation
Browse the [docs](https://ariel.ninja/botroyale/docs/) for guides and API reference to learn more.

## Community
Join us in the [community discord server](https://discord.gg/ADss5FRyqG).

## Contributing
Browse the [contribution guide](https://ariel.ninja/botroyale/docs/guides/contributing.html).
