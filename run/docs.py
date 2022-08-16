"""
Opens the documentation index in the default browser. Creates the docs if they are missing.
"""
from util.file import popen_path
from run.makedocs import INDEX_FILE, make_docs


def run():
    if not INDEX_FILE.is_file():
        print('Docs missing. Making from source.')
        make_docs()
    print('Opening docs in browser.')
    popen_path(INDEX_FILE)
