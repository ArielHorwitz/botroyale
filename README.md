# Bot Royale
A battle royale for bots.

### Requirements
- [Python 3.9+](https://www.python.org/)
- [Kivy](https://pypi.org/project/Kivy/) for the GUI
- [numpy](https://pypi.org/project/numpy/) because of course
- [pdoc3](https://pypi.org/project/pdoc3/) to create the docs (optional)

It is recommended to use a [virtual environment](https://docs.python.org/3/tutorial/venv.html). Once activated, install the requirements:

`pip install -r requirements.txt`

<br>
### Run
The main script:

`python main.py`

will choose which module to import and run based on the first command line argument. The default is `gui`. To see other options:

`python main.py --list`

For example:

`python main.py cli`

<br>
### Writing bots
See the [guides](docs/guides/index.html).

<br>
### Making the docs from source
To simply view the docs locally, run:

`python main.py docs`

This will create the docs from source if missing, and then open them in the default browser. If you wish to force recreating the docs, run:

`python main.py makedocs`
