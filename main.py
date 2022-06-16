import argparse

from api.logic_api import BaseLogicAPI
from logic.battle import Battle
from gui.gui import App


def parse_args():
    parser = argparse.ArgumentParser(description='Battle royale for bots.')
    parser.add_argument('--gui-dev',
        dest='gui_dev_mode',
        action='store_const', const=True,
        default=False,
        help='GUI developer mode')
    args = parser.parse_args()
    return args


def run():
    args = parse_args()
    logic_api_cls = Battle
    if args.gui_dev_mode:
        print(f'Running in GUI dev mode')
        logic_api_cls = BaseLogicAPI
    logic_api = logic_api_cls()
    app = App(logic_api=logic_api)
    app.run()


if __name__ == '__main__':
    run()
