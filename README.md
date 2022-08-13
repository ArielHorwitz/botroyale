# Bot Royale
A battle royale for bots.

### Requirements
- [Python 3.9+](https://www.python.org/)
- [Kivy](https://pypi.org/project/Kivy/) for the GUI
- [numpy](https://pypi.org/project/numpy/) because of course
- [pdoc3](https://pypi.org/project/pdoc3/) to create the docs (optional)

It is recommended to use a [virtual environment](https://docs.python.org/3/tutorial/venv.html). Once activated, install the requirements:

`pip install -r requirements.txt`


### Run
The main script:

`python main.py`

will choose which module to import and run based on the first command line argument. The default is `gui`. To see other options:

`python main.py --list`

For example:

`python main.py cli`


### Writing bots
To write a bot it is recommended to start with the [guides](https://github.com/ArielHorwitz/bot-royale/wiki). Starting is as simple as copying an existing bot with a new name.


### Building the docs
To (re)build the docs from source, run:

`python main.py docs`
