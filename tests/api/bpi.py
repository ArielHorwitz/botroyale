# flake8: noqa

import botroyale as br
from botroyale import api


def _get_api_doc_refs():
    identifier_start = "### All available attributes"
    identifier_end = "<br>"
    found_identifier = False
    api_doc_refs = []
    for line in api.__doc__.strip().split("\n"):
        if found_identifier and line == identifier_end:
            break
        is_identifer = line == identifier_start
        if not is_identifer and not found_identifier:
            continue
        if is_identifer:
            found_identifier = True
            continue
        assert line.startswith("- `botroyale.")
        assert line.endswith("`")
        attribute = line.split(".")[-1][:-1]
        api_doc_refs.append(attribute)
    return api_doc_refs


API_DOC_REFS = _get_api_doc_refs()


def test_api_docstring():
    for attribute in api.__all__:
        assert attribute in API_DOC_REFS


def test_api_all():
    for attribute in API_DOC_REFS:
        assert hasattr(api, attribute)
        assert attribute in api.__all__
