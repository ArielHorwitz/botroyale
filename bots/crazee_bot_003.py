import copy
import numpy as np

from api.actions import Move, Push, Idle, Action, Jump
from bots import BaseBot
from logic.state import State
from util.hexagon import Hexagon, Hex
from api.bots import world_info, center_distance
from time import perf_counter


class CrazeeBotAlpha(BaseBot):
    NAME = "CrazeeBot"
    COLOR_INDEX = 9
    MAX_AP = 100
    AP_REGEN = 50
    CENTER_TILE = Hex(0, 0)
    logging_enabled = False
    SPRITE = 'flower'

    def __init__(self, id):
        super().__init__(id)
        self.planed_actions = []

    def poll_action(self, state: State):
        t1_start = perf_counter()
        action = self.plan_action(state)
        if not action:
            self.logger(f"NO LEGAL MOVES FOR ME TO DO, Bot {self.id}")
            action = Idle()
        self.logger(f"{self.NAME}-{self.id} took {(perf_counter() - t1_start) * 1000:.2f}ms")
        return action

    def plan_action(self, state: State):
        if len(self.planed_actions) == 0:
            self.planed_actions = self.calc_turn(state)
        return self.planed_actions.pop(0)

    @staticmethod
    def get_legal_actions(state):
        pos = state.positions[state.current_unit]
        obstacles = state.pits | state.walls | set(state.positions)
        neighbors = set(pos.neighbors) - obstacles
        neighbors2 = set(pos.ring(2)) - obstacles
        possible_actions = []
        ap = state.ap[state.current_unit]
        if ap >= Move.ap:
            possible_actions.extend(Move(t) for t in neighbors)
        if ap >= Jump.ap:
            possible_actions.extend(Jump(t) for t in neighbors2)
        if ap >= Push.ap:
            possible_actions.extend(Push(t) for t in neighbors)
        legal_actions = [Idle()]
        for action in possible_actions:
            if state.check_legal_action(state.current_unit, action):
                legal_actions.append(action)
        return legal_actions

    def calc_turn(self, start_state: State):
        MAX_DEPTH = 5
        explored_worlds = set()

        def get_next_state(_state: State, action: Action):
            s = _state.apply_action(action)
            s.score = get_state_score(s)
            return s

        def get_state_score(_state: State):
            bot_id = _state.current_unit
            if not _state.alive_mask[bot_id]:
                return float('-inf')

            enemys_alive = _state.alive_mask.sum() - 1
            if enemys_alive == 0:
                return float('inf')

            my_pos: Hexagon = _state.positions[bot_id]
            edge_of_map: set[Hexagon] = set(self.CENTER_TILE.ring(_state.death_radius - 1))
            if my_pos in edge_of_map:
                return float('-inf')

            enemy_dead_score = -enemys_alive * 1.5
            enemy_mask = np.ones(len(_state.positions), dtype=np.bool)
            enemy_mask[self.id] = False
            enemy_ids = np.flatnonzero(enemy_mask)
            alive_enemy_pos = set(_state.positions[uid] for uid in enemy_ids)
            tile_view_distance = 5
            terrain_score = 0
            enemy_score = 0
            d_pits = [my_pos.get_distance(pit) for pit in _state.pits if my_pos.get_distance(pit) < tile_view_distance]
            d_walls = [my_pos.get_distance(wall) for wall in _state.walls if
                       my_pos.get_distance(wall) < tile_view_distance]
            d_enemys = [my_pos.get_distance(enemy) for enemy in alive_enemy_pos
                        if my_pos.get_distance(enemy) < tile_view_distance]
            d_center = my_pos.get_distance(self.CENTER_TILE)
            terrain_score -= d_center / 4
            my_ap = _state.ap[self.id]
            ap_score = min(my_ap, self.AP_REGEN)
            ap_score += max(0, my_ap - self.AP_REGEN) / 4
            ap_score /= 20
            if len(d_pits) > 0:
                terrain_score += (sum(d_pits) / len(d_pits)) * 2
            if len(d_walls) > 0:
                terrain_score -= (sum(d_walls) / len(d_walls))
            if len(d_enemys) > 0:
                enemy_score += (sum(d_enemys) / len(d_enemys))
            score = terrain_score + enemy_score + enemy_dead_score + ap_score
            # self.logger(f"Score: {score:.2f}, terrain: {terrain_score:.2f}, enemy: {enemy_score:.2f}, "
            #             f"enemy_dead: {enemy_dead_score:.2f}, ap: {ap_score:.2f}")
            return score

        def find_max_chain(chain: list[State], depth=MAX_DEPTH):
            if depth == 0:
                return chain
            best_chain = chain
            current_state = chain[-1]
            for next_action in self.get_legal_actions(current_state):
                new_state = get_next_state(current_state, next_action)
                # Pruning explored worlds
                c_hash = hash_state(new_state)
                if c_hash in explored_worlds:
                    continue
                explored_worlds.add(c_hash)

                child_best_chain = find_max_chain([*chain, new_state], depth - 1)
                if child_best_chain[-1].score > best_chain[-1].score:
                    best_chain = child_best_chain
            return best_chain

        start_state.score = get_state_score(start_state)

        init_chain = [start_state]
        result_chain = find_max_chain(init_chain)
        result_chain.append(get_next_state(result_chain[-1], Idle()))
        actions = [state.last_action for state in result_chain[1:]]
        self.logger('\n'.join(str(_) for _ in actions))
        return actions


def hash_state(state):
    return sum([
        *(hash(h) for h in state.positions),
        *(hash(h) for h in state.walls),
        *(hash(h) for h in state.pits),
        hash(state.death_radius),
        hash(state.alive_mask.tostring()),
        hash(state.ap.tostring()),
        hash(state.round_ap_spent.tostring()),
        hash(str(state.round_remaining_turns)),
        hash(state.step_count),
        hash(state.turn_count),
        hash(state.round_count),
        ])


BOT = CrazeeBotAlpha
