# Bot Royale Documentation
A battle royale for bots. Write your own bots in Python and watch them play!

![Preview GIF](preview.gif)

## Install
It is recommended to use a [virtual environment](https://docs.python.org/3/tutorial/venv.html). Once activated, install using:
```noformat
pip install --upgrade botroyale
```

## Quickstart
It takes as few as ***5 lines of code*** to write your own bot and watch it play, from start to finish!

```python
import botroyale as br

class MyBot(br.BaseBot):
    NAME = 'mybot'

br.register_bot(MyBot)
br.run_gui()
```

## Guides
Browse the [guides](https://github.com/ArielHorwitz/botroyale/tree/dev/docs/guides) to learn more.

## Source code
See the source code on [GitHub](https://github.com/ArielHorwitz/botroyale).
