# Installing Bot Royale

It is recommended to use a [virtual environment](https://docs.python.org/3/tutorial/venv.html). Once activated, install using:

```noformat
pip install --upgrade botroyale
```

That's it! You now have Bot Royale installed in Python. See the guide on [writing your first bot](bots/simple.html).

<br>

---
<br>

## Install from source
Some advanced use cases require installing from source (e.g. to set up an environment for core developers). Assuming we have cloned the repo, `cd`'d into the project directory, and activated our virtual environment; we can install the project in `editable` mode from source with the `dev` extras:
```noformat
pip install --upgrade --editable .[dev]
```

> **Note:** We should rerun this command any time the project metadata or requirements change (see the `pyproject.toml` file).

This essentially installs the project itself as a library in the project's environment. The `.` represents the path to the current directory (we run the command from within the project directory). We install it as `editable` so that local changes to our code may reflect on the installed library. The `dev` extras are extra library requirements that core developers use such as for code formatting and linting, building the documentation, etc.

You should now have access to the developer options in the [CLI utilities](ui/cli.html#developer-options), which include tests.
