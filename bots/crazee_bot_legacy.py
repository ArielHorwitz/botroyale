import copy
import random
import numpy as np

from api.actions import Move, Push, Idle, Action
from bots import BaseBot
from util.hexagon import Hexagon, Hex
from api.bots import world_info
from util.settings import Settings
from time import perf_counter

DEBUG = Settings.get('bots.crazee.l.debug', False)


def debug(*lines):
    if DEBUG:
        print('\n'.join(str(_) for _ in lines))


class CrazeeBotLegacy(BaseBot):
    NAME = "CrazeeBot-0.1"
    COLOR_INDEX = 1
    LETHAL_PUSH_SCORE = 1000

    def __init__(self, id):
        super().__init__(id)
        self.enemy_positions: set = set()
        self.pos = None
        self.ap = None
        self.center_tile = Hex(0, 0)

    def get_action(self, wi: world_info):
        t1_start = perf_counter()
        self.pos: Hexagon = wi.positions[self.id]
        self.ap = wi.ap[self.id]
        self.enemy_positions: set = set(wi.positions) - {self.pos}
        debug(f"-" * 50,
              f"Crazee!!!!!!!!!!! id: {self.id}",
              f"-" * 50,
              )
        action = self.pick_action(wi)
        if not action:
            debug(f"NO LEGAL MOVES FOR ME TO DO, Bot {self.id}")
            # action = Idle()
            action = Move(Hex(100, 100))
        debug(f"{self.NAME}-{self.id} took {(perf_counter()-t1_start) * 1000:.2f}ms")
        debug(f"-" * 50)
        return action

    def pick_action(self, wi: world_info):
        def select_action():
            """True = Move, False = Push"""
            if len(push_scores) == 0 and len(move_scores) > 0:
                return True
            if len(push_scores) > 0 and len(move_scores) == 0:
                return False
            if max(push_scores) >= max(move_scores):
                return not self.ap >= Push.ap
            return True

        def make_action(action_set, scores, is_move):
            selected_action_dest = list(action_set)[np.argmax(scores)]
            debug(f"Selected Action: {'Move' if is_move else 'Push'} {selected_action_dest} with Score {max(scores):.2f}")
            return Move(selected_action_dest) if is_move else Push(selected_action_dest)

        legal_moves, move_scores = self.get_legal_moves(wi, self.enemy_positions)
        legal_pushes, push_scores = self.get_legal_pushes(wi)
        debug(f"{len(move_scores) + len(push_scores)} Possible Actions:",
              f"    Push> {[f'Score {score:.2f} : Dest {action}' for action, score in zip(legal_pushes, push_scores)]}",
              f"    Move> {[f'Score {score:.2f} : Dest {action}' for action, score in zip(legal_moves, move_scores)]}")
        if len(push_scores) == 0 and len(move_scores) == 0:
            return None
        return make_action(legal_moves, move_scores, True) if select_action() \
            else make_action(legal_pushes, push_scores, False)

    def get_legal_moves(self, wi: world_info, enemy_positions: set[Hexagon]):
        obstacles = wi.pits | wi.walls | enemy_positions
        legal_moves = set(self.pos.neighbors) - obstacles
        scores = []
        for move in legal_moves:
            scores.append(-self.gen_neighbor_heat_value(wi, move))
        return legal_moves, scores

    def get_legal_pushes(self, wi: world_info):
        scores = []
        legal_options = set()
        push_options = set(self.pos.neighbors) & self.enemy_positions
        for push_tile in push_options:
            end_tile = next(self.pos.straight_line(push_tile))
            if end_tile in wi.walls or end_tile in wi.positions:
                continue
            legal_options.add(push_tile)
            d_pits = min([push_tile.get_distance(pit) for pit in wi.pits])
            scores.append(self.LETHAL_PUSH_SCORE if end_tile in wi.pits else 6-d_pits)
        return legal_options, scores

    def gen_neighbor_heat_value(self, wi: world_info, neighbor: Hexagon):
        edge_of_map: set[Hexagon] = set(self.center_tile.ring(wi.ring_radius - 1))
        #debug(f'ring radius {wi.ring_radius}, edge {[str(e) for e in edge_of_map]}')
        tile_view_distance = 5
        terrain_heat = 0
        enemy_heat = 0
        edge_heat = 100 if neighbor in edge_of_map else 0

        # terrain_heat = (dist from pits - dist from walls)
        d_pits = [neighbor.get_distance(pit) for pit in wi.pits if neighbor.get_distance(pit) < tile_view_distance]
        d_walls = [neighbor.get_distance(wall) for wall in wi.walls if neighbor.get_distance(wall) < tile_view_distance]
        d_enemys = [neighbor.get_distance(enemy) for enemy in self.enemy_positions if neighbor.get_distance(enemy) < tile_view_distance]

        if len(d_pits) > 0:
            terrain_heat += (sum(d_pits) / len(d_pits))
        if len(d_walls) > 0:
            terrain_heat -= (sum(d_walls) / len(d_walls))
        if len(d_enemys) > 0:
            enemy_heat += (sum(d_enemys) / len(d_enemys))
        heat_value = terrain_heat - enemy_heat
        heat_value += edge_heat
        return heat_value


BOT = CrazeeBotLegacy
