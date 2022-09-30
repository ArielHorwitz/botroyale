# flake8: noqa

from hypothesis import settings
from botroyale.util.code import UNITTEST_PROFILES


def pytest_deselected(items):
    if not items:
        return
    config = items[0].session.config
    reporter = config.pluginmanager.getplugin("terminalreporter")
    reporter.ensure_newline()
    for item in items:
        reporter.line(f"deselected: {item.nodeid}", yellow=True, bold=True)


for prof, psettings in UNITTEST_PROFILES.items():
    settings.register_profile(prof, **psettings)
