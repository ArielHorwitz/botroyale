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

See the guides on [writing bots](bots/index.html) to get started, and make sure to share your creation with others!

### Bugs and Issues
This one goes without saying, but any bugs or issues found and reported to the [issue tracker](https://github.com/ArielHorwitz/botroyale/issues) are incredibly helpful. If you do find a bug or an issue, please raise it with appropriate detail (especially any logs that may be related) so that the core developers may handle it as efficiently as possible.

> Issues with the API documentation or guides are considered highly important.

### Feature Requests
Feature requests can be divided into two categories: API features and game mechanics suggestions.

API feature requests which include any features that bot developers might want are more than welcome on the [issue tracker](https://github.com/ArielHorwitz/botroyale/issues). Game mechanics suggestions should be discussed in community forums and gather overwhelming agreement. See the [home page](../index.html#resources) for details on community forums.

### Guides and Documentation
A good API reference and collection of guides are critical for the purposes of this project -- it is here to serve bot developers that wish to play with writing AI. And so, any contribution to the guides or documentation is high priority.

Guides are written in markdown, which is extremely easy to write and share. The API reference is generated from source code and requires the same procedure as for [code contribution](#code-contribution).

### Code Contribution
While the project is still in early development, many of the core features have been implemented. Hence, code contributions should generally focus on improving the quality of the API and codebase in general.

Contributing code requires [installing from source](install.html#install-from-source). It is critical to run the test suite ***before making any changes***:
```noformat
botroyale test
```

This will run the suite of integration tests and make sure the codebase complies with the automated quality standards. If this fails before you made any changes, something is wrong and it should be reported immediately.

***Any changes that are meant to merged back upstream must pass these tests.***

> **Note:** To pass the format test, one simply needs to run `botroyale format`.
