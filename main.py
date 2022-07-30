print('\n\nWelcome to Bot Royale.\n')

from util.settings import Settings


RUN_CLI = Settings.get('gui.|cli', False)


def run_gui():
    from gui.gui import App
    app = App()
    # We write settings to file after completing startup, after all parts
    # of the program have had a chance to set their defaults.
    Settings.write_to_file()
    app.run()


def run_cli():
    from gui.cli import CLI
    CLI().run()


if __name__ == '__main__':
    run_cli() if RUN_CLI else run_gui()
