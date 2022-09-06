"""Opens the documentation in the default browser. Creates the docs if missing."""
from botroyale.util.docs import open_docs, make_docs


def run():
    """Recreates and opens the docs."""
    # make_docs(dry_run=True)
    open_docs(force_remake=True)
