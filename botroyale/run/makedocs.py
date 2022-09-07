"""Opens the documentation in the default browser. Creates the docs if missing."""
from botroyale.util.docs import make_docs


def run():
    """Recreates and opens the docs."""
    make_docs()
