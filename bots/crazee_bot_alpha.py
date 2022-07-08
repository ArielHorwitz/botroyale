import copy
import random
import numpy as np

from api.actions import Move, Push, Idle, Action
from bots import BaseBot
from util.hexagon import Hexagon, Hex
from api.bots import world_info
from util.settings import Settings
from time import perf_counter

DEBUG = Settings.get('bots.crazee.debug', False)


def debug(*lines):
    if DEBUG:
        print('\n'.join(str(_) for _ in lines))


class CrazeeBotAlpha(BaseBot):
    NAME = "CrazeeBot"
    COLOR_INDEX = 7
    MAX_AP = 100
    AP_REGEN = 50
    CENTER_TILE = Hex(0, 0)
    LETHAL_PUSH_SCORE = 1000

    def __init__(self, id):
        super().__init__(id)
        self.enemy_positions: set = set()
        self.pos = None
        self.ap = None
        self.planed_actions = []

    def get_action(self, wi: world_info):
        t1_start = perf_counter()
        self.pos: Hexagon = wi.positions[self.id]
        self.ap = wi.ap[self.id]
        self.enemy_positions: set = set(wi.positions) - {self.pos}
        # action = self.pick_action(wi)
        action = self.plan_action(wi)
        if not action:
            debug(f"NO LEGAL MOVES FOR ME TO DO, Bot {self.id}")
            action = Idle()
            # action = Move(Hex(100, 100))
        debug(f"{self.NAME}-{self.id} took {(perf_counter() - t1_start) * 1000:.2f}ms")
        return action

    def plan_action(self, wi: world_info):
        if len(self.planed_actions) == 0:
            self.planed_actions = self.calc_turn(wi)
        return self.planed_actions.pop(0).action

    def get_legal_actions(self, wi: world_info):
        actions = []
        my_ap = wi.ap[self.id]
        if my_ap < Move.ap or not wi.alive_mask[self.id]:
            return actions
        pos: Hexagon = wi.positions[self.id]

        enemy_mask = np.ones(len(wi.positions), dtype=np.bool)
        enemy_mask[self.id] = False
        enemy_ids = np.flatnonzero(enemy_mask)
        enemy_positions = set(wi.positions[uid] for uid in enemy_ids)
        # obstacles = wi.pits | wi.walls | enemy_positions
        obstacles = wi.walls | enemy_positions
        legal_moves = set(pos.neighbors) - obstacles
        actions.extend([Move(m) for m in legal_moves])
        if my_ap < Push.ap:
            return actions
        pos: Hexagon = wi.positions[self.id]
        enemy_positions: set = set(wi.positions) - {pos}
        legal_options = set()
        push_options = set(pos.neighbors) & enemy_positions
        for push_tile in push_options:
            end_tile = next(pos.straight_line(push_tile))
            if end_tile in wi.walls or end_tile in wi.positions:
                continue
            legal_options.add(Push(push_tile))

        actions.extend(legal_options)
        return actions

    def calc_turn(self, wi: world_info):
        MAX_DEPTH = 5

        def copy_wi(_wi: world_info) -> world_info:
            return world_info(
                positions=copy.copy(_wi.positions),
                walls=copy.copy(_wi.walls),
                pits=copy.copy(_wi.pits),
                ring_radius=_wi.ring_radius,
                alive_mask=copy.deepcopy(_wi.alive_mask),
                turn_count=_wi.turn_count,
                round_count=_wi.round_count,
                ap=copy.deepcopy(_wi.ap),
                round_ap_spent=copy.deepcopy(_wi.round_ap_spent),
                round_remaining_turns=copy.deepcopy(_wi.round_remaining_turns),
            )

        def get_new_world_state(old_wi: world_info, action: Action):
            new_cwi = copy_wi(old_wi)
            c_pos = new_cwi.positions
            c_ap = new_cwi.ap
            if type(action) is Push:
                # print(f"My Pos: {c_pos[self.id]}, Target: {action.action.target}")
                end_tile = next(c_pos[self.id].straight_line(action.target))
                enemy_index = [e for e in range(len(c_pos)) if c_pos[e] == action.target][0]
                c_pos[enemy_index] = end_tile
            elif type(action) is Move:
                c_pos[self.id] = action.target
            else:
                print(action)
            c_ap[self.id] -= action.ap
            new_cwi.alive_mask[:] = [pos not in new_cwi.pits for pos in c_pos]
            return new_cwi

        def get_wi_score(cwi: world_info, bot_id: int):
            if not cwi.alive_mask[bot_id]:
                return float('-inf')

            enemys_alive = cwi.alive_mask.sum() - 1
            if enemys_alive == 0:
                return float('inf')

            my_pos: Hexagon = cwi.positions[bot_id]
            edge_of_map: set[Hexagon] = set(self.CENTER_TILE.ring(cwi.ring_radius - 1))
            if my_pos in edge_of_map:
                return float('-inf')

            enemy_dead_score = -enemys_alive
            enemy_mask = np.ones(len(cwi.positions), dtype=np.bool)
            enemy_mask[self.id] = False
            enemy_ids = np.flatnonzero(enemy_mask)
            alive_enemy_pos = set(wi.positions[uid] for uid in enemy_ids)
            tile_view_distance = 5
            terrain_score = 0
            enemy_score = 0
            d_pits = [my_pos.get_distance(pit) for pit in cwi.pits if my_pos.get_distance(pit) < tile_view_distance]
            d_walls = [my_pos.get_distance(wall) for wall in cwi.walls if
                       my_pos.get_distance(wall) < tile_view_distance]
            d_enemys = [my_pos.get_distance(enemy) for enemy in alive_enemy_pos
                        if my_pos.get_distance(enemy) < tile_view_distance]

            if len(d_pits) > 0:
                terrain_score += (sum(d_pits) / len(d_pits)) * 2
            if len(d_walls) > 0:
                terrain_score -= (sum(d_walls) / len(d_walls))
            if len(d_enemys) > 0:
                enemy_score += (sum(d_enemys) / len(d_enemys))
            score = terrain_score + enemy_score + enemy_dead_score
            # print(f"Score: {score:.2f}, terrain_score: {terrain_score:.2f}, enemy_score: {enemy_score:.2f}, "
            #       f"enemy_dead_score: {enemy_dead_score:.2f}")
            return score

        def find_max_chain(chain: list[CWorld], depth=MAX_DEPTH):
            if depth == 0:
                return chain
            best_chain = chain
            current_state = chain[-1].state
            for next_action in self.get_legal_actions(current_state):
                new_state = get_new_world_state(current_state,
                                                next_action)
                new_cstate = CWorld(new_state,
                                    get_wi_score(new_state, self.id),
                                    next_action)
                child_best_chain = find_max_chain([*chain, new_cstate], depth - 1)
                if child_best_chain[-1].score > best_chain[-1].score:
                    best_chain = child_best_chain
                elif child_best_chain[-1].score == best_chain[-1].score:
                    if len(child_best_chain) < len(best_chain):
                        best_chain = child_best_chain
            # print(f"depth: {depth}")
            # print('\n'.join(str(_) for _ in best_chain))
            return best_chain

        init_chain = [CWorld(wi, get_wi_score(wi, self.id), Idle())]
        result_chain = find_max_chain(init_chain)
        if len(result_chain) > 1:
            temp = result_chain.pop(0)
            result_chain.append(temp)
        # print('End result_chain')
        debug('\n'.join(str(_) for _ in result_chain))
        return result_chain


class CWorld:
    def __init__(self, state: world_info, score: float, action: Action):
        self.state = state
        self.score = score
        self.action = action

    def __str__(self):
        return f"Score: {self.score:.2f}, " \
               f"State: {[h.xy for h in self.state.positions]}, " \
               f"Action: <{type(self.action).__name__}> {self.action.target if hasattr(self.action, 'target') else ''}"

    def __repr__(self):
        return str(self)


BOT = CrazeeBotAlpha
