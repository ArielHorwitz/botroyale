from collections import namedtuple
import numpy as np
from bots import BaseBot
from api.actions import Idle, Move, Push
from util.settings import Settings
from util.hexagon import Hex
from util.pathfinding import a_star


DEBUG = Settings.get('bots.ninja.debug', 0)


def mlogger(*lines):
    if DEBUG:
        print('\n'.join(str(_) for _ in lines))


class NinjaBotV001(BaseBot):
    NAME = 'ninja.001'
    COLOR_INDEX = 5

    TileValue = namedtuple('TileValue', ['tile', 'value'])

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__last_step_round = -1
        self.turn_step = 0

    def update(self, wi):
        if self.__last_step_round < wi.round_count:
            self.turn_step = 0
        else:
            self.turn_step += 1
        self.__last_step_round = wi.round_count
        self.pos = wi.positions[self.id]
        self.ap = wi.ap[self.id]
        self.walls = wi.walls
        self.pits = wi.pits
        enemy_mask = np.ones(len(wi.positions), dtype=np.bool)
        enemy_mask[self.id] = False
        enemy_mask[~wi.alive_mask] = False
        self.enemy_ids = np.flatnonzero(enemy_mask)
        self.enemy_pos = set(wi.positions[uid] for uid in self.enemy_ids)

    def get_action(self, wi):
        self.update(wi)
        # Move
        move_target = self.pos
        my_pos_value = self.move_tile_value(wi, self.pos)
        move_options = self.move_options(wi)
        if move_options[0].value > my_pos_value:
            move_target = move_options[0].tile
        # Push
        push_options = self.push_options(wi)
        push_option_reprs = []
        for push in push_options:
            if push.value < 0:
                continue
            lethal = ' LETHAL' if push.value > 0 else ' NOT VALID' if push.value < 0 else ''
            push_option_reprs.append(f'Can push enemy @ {push.tile}{lethal}')

        # Choose move
        action = Move(move_target)
        if move_target is self.pos:
            action = Idle()
            action_str = 'Staying put'
        else:
            action_str = f'Moving to: {move_target} {move_options[0].value}'
        # Choose push
        push = push_options[0]
        if push.value >= 0:
            action = Push(push.tile)
            action_str = f'Pushing: {push.tile} {"LETHAL" if push.value > 0 else "not lethal"}'

        mlogger(
            f'{action_str}',
            '',
            f'Turn step: {self.turn_step}',
            f'My position: {self.pos} {my_pos_value}',
            f'Action: {action}',
            '=== MOVE OPTIONS',
            '\n'.join(f'{tv.value} {tv.tile}' for tv in move_options),
            '=== PUSH OPTIONS',
            '\n'.join(push_option_reprs),
            '_'*30,
        )
        return action

    def move_options(self, wi):
        tvs = (self.TileValue(n, self.move_tile_value(wi, n)) for n in self.pos.neighbors)
        sorted_tvs = sorted(tvs, key=lambda tv: -tv.value)
        return sorted_tvs

    def move_tile_value(self, wi, tile):
        """
        Value of a tile.
        i.e. "How good is it to move to tile?"
        """
        # Consider if is even possible to move to this tile
        if tile in self.pits:
            return -1_000_000
        if tile in self.enemy_pos or tile in self.walls:
            return -1000
        # Otherwise consider value of neighbor tiles
        return sum(self.move_tile_neighbor_value(wi, tile, n) for n in tile.neighbors)

    def move_tile_neighbor_value(self, wi, tile, neighbor):
        """
        Value of a neighbor.
        i.e. "How good is it to stand next to neighbor (when moving to tile)?"
        """
        v = 0
        # We don't like standing next to enemies
        near_enemy = neighbor in self.enemy_pos
        v -= 10 * near_enemy
        # We really don't like standing next to pits
        v -= 100 * (neighbor in self.pits)
        # We really don't like standing between enemies and pits
        if near_enemy:
            push_target = next(neighbor.straight_line(tile))
            v -= 500 * (push_target in self.pits)
        # We like standing up against walls
        v += 25 * (neighbor in self.walls)
        return v

    def push_options(self, wi):
        tvs = (self.TileValue(n, self.push_value(wi, n)) for n in self.pos.neighbors)
        sorted_tvs = sorted(tvs, key=lambda tv: -tv.value)
        return sorted_tvs

    def push_value(self, wi, push_tile):
        my_pos = wi.positions[self.id]
        end_tile = next(my_pos.straight_line(push_tile))
        # Check if push is legal
        no_unit_to_push = push_tile not in wi.positions
        against_wall = end_tile in wi.walls
        against_unit = end_tile in wi.positions
        if no_unit_to_push or against_wall or against_unit:
            return -1
        # Check if push is lethal
        is_lethal = end_tile in self.pits
        return int(is_lethal)


BOT = NinjaBotV001
