# Contributing to Bot Royale

Your interest in contributing to Bot Royale is highly appreciated. It is thanks to people like you that we can have nice things :)

## Contributing
Bot Royale is still pretty early in development and may need help in more ways than you might imagine. We hope that you may find an avenue that fits you.

Note that the following options are sorted in the order you are most likely to contribute. For example, it is more likely that a good contribution to the code will be made by someone who has been involved in tracking bugs or writing documentation. And it is unlikely that a good contribution for a feature request will be made by someone who has never written a bot.

- [Develop bots](#developing-bots)
- [Bugs and issues](#bugs-and-issues)
- [Feature requests](#feature-requests)
- [Guides and documentation](#guides-and-documentation)
- [Code contribution](#code-contribution)

### Developing Bots
Given the early stage of the project, any new bots that are publically shared are an excellent contribution. Not only is this arguably the most fun way to contribute, it also inspires others to learn more about what can be done with AI in Bot Royale.

Moreover, it helps the core developers immenesly because they may learn about any confusing or difficult issues for bot developers, and the project is ultimately about serving bot developers.

See the guides on [writing bots](guides/bots) to get started, and make sure to share your creation with others!

### Bugs and Issues
This one goes without saying, but any bugs or issues found and reported to the [issue tracker](https://github.com/ArielHorwitz/botroyale/issues) are incredibly helpful. If you do find a bug or an issue, please raise it with appropriate detail (especially any logs that may be related) so that the core developers may handle it as efficiently as possible.

> Issues with the API documentation or guides are considered highly important.

### Feature Requests
Feature requests can be divided into two categories: API features and game mechanics suggestions.

API feature requests which include any features that bot developers might want are more than welcome on the [issue tracker](https://github.com/ArielHorwitz/botroyale/issues). Game mechanics suggestions should be discussed in community forums and gather overwhelming agreement. See the [home page](https://github.com/ArielHorwitz/botroyale) for details on community forums.

### Guides and Documentation
A good API reference and collection of guides are critical for the purposes of this project -- it is here to serve bot developers that wish to play with writing AI. And so, any contribution to the guides or documentation is highly valued.

Guides are written in markdown, which is extremely easy to write and share. The documentation is generated from source code and requires setting up a [dev environment](install.html#dev-environment).

### Code Contribution
It has been said the project is still in early development, however we believe most of the core features have been implemented. This means the codebase is being refactored regularly to improve quality. Hence, code contributions should focus on improving the quality of the codebase.

Contributing code requires setting up a [dev environment](install.html#dev-environment).


## Dev Environment
Those wishing to [contribute](contributing.html) to the source code must set up an environment similar to other core developers such that cooperation is efficient.

### Install from source
Assuming we have cloned the repo, activated our virtual environment, and `cd`'d into the project directory, we can install the project in `editable` mode from source with the `dev` extras:
```noformat
pip install --upgrade --editable .[dev]
```

> **Note:** We should rerun this command any time the project metadata or requirements change (see `pyproject.toml`).

This essentially installs the project itself as a library in the project's environment. The `.` represents the current directory because we are working from within the project directory. We install it as `editable` so that local changes to our code may reflect on the installed library. The `dev` extras are extra library requirements that core developers use such as for code formatting and linting, building the documentation, etc.

You should now have access to the developer options in the [CLI utilities](ui/cli.html#developer-options), which include tests.

### Tests
It is critical to run the test suite ***before making any changes***:
```noformat
botroyale-test
```

This will run the suite of integration tests and make sure the codebase complies with the automated quality standards. If this fails before you made any changes, something is wrong and it should be reported immediately.

***Any changes that are meant to merged back upstream must pass these tests.***

> **Note:** To pass the format test, one simply needs to run `botroyale-format`.
