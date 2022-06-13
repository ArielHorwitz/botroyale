from logic.battle import Battle
from gui.gui import App


def start_gui():
    b = Battle()
    app = App(logic_api=b)
    app.run()


if __name__ == '__main__':
    start_gui()
