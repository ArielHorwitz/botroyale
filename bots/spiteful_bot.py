# Maintainer: ninja
import random
from collections import namedtuple
from bots import BaseBot
from util.hexagon import Hex, DIAGONALS, is_hex
from util.settings import Settings
from util.pathfinding import a_star
from api.logging import logger as glogger
from api.actions import Move, Push, Idle


DEBUG = Settings.get('bots.spiteful.debug', False)
LethalSequence = namedtuple('LethalSequence', ['ap_cost', 'actions', 'vfx'])


def logger(m):
    if DEBUG:
        glogger(str(m))


class SpitefulBot(BaseBot):
    NAME = 'spiteful'
    COLOR_INDEX = 0
    map_center = Hex(0, 0)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__last_step_round = -1
        self.__completed_setup = False
        self.turn_step = 0
        self.current_sequence = None

    def setup(self, wi):
        self.update(wi)

    def update(self, wi):
        if self.__last_step_round < wi.round_count:
            self.turn_step = 0
        else:
            self.turn_step += 1
        self.__last_step_round = wi.round_count
        self.wi = wi
        self.pos = wi.positions[self.id]
        self.ap = wi.ap[self.id]
        self.obstacles = self.wi.walls | set(self.wi.positions)
        self.sequence_blockers = self.wi.pits | self.obstacles - {self.pos}
        self.blocked_pits = self.wi.pits & self.obstacles
        self.open_pits = self.wi.pits - self.obstacles

    def get_action(self, wi):
        self.update(wi)
        if self.ap < 10:
            logger(f'Out of AP.')
            return Idle()

        if not self.current_sequence:
            logger(f'No sequence.')
            seqs = self.find_lethal_sequences()
            if seqs:
                seq_str = '\n'.join(f'{s.ap_cost} AP {" ".join(str(a) for a in s.actions)}' for s in seqs)
                logger(f'Found sequences:\n{seq_str}')
                self.current_sequence = list(seqs[0].actions)

        if self.current_sequence:
            s = '\n'.join(f'-> {a}' for a in self.current_sequence)
            logger(f'Remaining sequence:\n{s}')
            action = self.current_sequence.pop(0)
            return action

        target_distance = self.wi.ring_radius - 3
        if self.pos.get_distance(self.map_center) > target_distance:
            path = self.path_as_close(self.map_center)
            if path:
                trunc_path = []
                moves = int(self.ap/10)
                for t in path[:moves]:
                    trunc_path.append(Move(t))
                    if self.map_center.get_distance(t) <= target_distance:
                        break
                while trunc_path:
                    if self.map_center.get_distance(trunc_path[-1].target) == self.wi.ring_radius - 1:
                        trunc_path = trunc_path[:-1]
                    else:
                        break
                if trunc_path:
                    self.current_sequence = trunc_path
                    logger(f'Moving to center: {self.current_sequence[0]} {len(self.current_sequence)} steps to target')
                    return self.current_sequence.pop(0)
                logger(f'On edge but cannot reach safer tile!')
            else:
                logger(f'On edge but no path to center!')

        logger(f'Idling.')
        return Idle()

    def move_tile_cost(self, tile):
        is_obstacle = tile in (self.wi.pits | self.wi.walls | set(self.wi.positions))
        obs_cost = float('inf') if is_obstacle else 0
        return 1 + obs_cost

    def get_path(self, target):
        return a_star(self.pos, target, cost=self.move_tile_cost)

    def get_paths(self, targets, sort=len):
        targets = (t for t in targets if self.move_tile_cost(t) < float('inf'))
        path_results = (self.get_path(t) for t in targets)
        paths = [p for p in path_results if p is not None]
        if sort:
            return sorted(paths, key=sort)
        return paths

    def path_as_close(self, target, sort=len):
        my_dist = self.pos.get_distance(target)
        best_paths = []
        options_radius = 0
        while not best_paths:
            if options_radius >= my_dist:
                return None
            targets = target.ring(radius=options_radius)
            best_paths = self.get_paths(targets, sort=sort)
            options_radius += 1
        return best_paths[0]

    def push_sequence_simple(self, pit, enemy):
        logger(f'Considering simple push sequence: {enemy} -> {pit}')
        # Assert geometry
        assert pit not in self.blocked_pits
        assert pit in enemy.neighbors
        # Check ap and sequence blockers
        ap_cost = 30
        start_pos = next(pit.straight_line(enemy))
        cannot_reach = self.pos.get_distance(start_pos) > self.ap - ap_cost
        if start_pos in self.sequence_blockers or cannot_reach:
            return None
        start_path = []
        if self.pos is not start_pos:
            start_path = self.get_path(start_pos)
        if start_path is None:
            return None
        ap_cost += len(start_path) * 10
        if ap_cost > self.ap:
            return None
        # Collect actions and vfx
        actions = [
            *(Move(t) for t in start_path),
            Push(enemy),
            ]
        vfx = [
            {'name': 'mark-green', 'hex': start_pos},
            {'name': 'push', 'hex': start_pos, 'neighbor': enemy},
            {'name': 'push', 'hex': enemy, 'neighbor': pit},
            {'name': 'mark-red', 'hex': pit},
            ]
        logger(f'Good sequence!')
        return LethalSequence(ap_cost, actions, vfx)

    def push_sequence_double(self, pit, enemy):
        logger(f'Considering double push sequence: {enemy} -> {pit}')
        # Assert geometry
        assert pit not in self.blocked_pits
        assert pit - enemy not in DIAGONALS
        assert pit.get_distance(enemy) == 2
        mid_points = set(enemy.neighbors) & set(pit.neighbors)
        assert len(mid_points) == 1
        mid_point = mid_points.pop()
        # Check ap and sequence blockers
        ap_cost = 70
        vector = enemy - mid_point
        start_pos = enemy + vector
        cannot_reach = self.pos.get_distance(start_pos) > self.ap - ap_cost
        if {start_pos, mid_point} & self.sequence_blockers or cannot_reach:
            return None
        start_path = []
        if self.pos is not start_pos:
            start_path = self.get_path(start_pos)
        if start_path is None:
            return None
        ap_cost += len(start_path) * 10
        if ap_cost > self.ap:
            return None
        # Collect actions and vfx
        actions = [
            *(Move(t) for t in start_path),
            Push(enemy), Move(enemy), Push(mid_point),
            ]
        vfx = [
            {'name': 'mark-green', 'hex': start_pos},
            {'name': 'push', 'hex': start_pos, 'neighbor': enemy},
            {'name': 'push', 'hex': enemy, 'neighbor': mid_point},
            {'name': 'move', 'hex': start_pos, 'neighbor': enemy},
            {'name': 'push', 'hex': enemy, 'neighbor': mid_point},
            {'name': 'push', 'hex': mid_point, 'neighbor': pit},
            {'name': 'mark-red', 'hex': pit},
        ]
        logger(f'Good sequence!')
        return LethalSequence(ap_cost, actions, vfx)

    def push_sequence_diag(self, pit, neighbor, enemy):
        logger(f'Considering diagonal push sequence: {enemy} -> {neighbor} -> {pit}')
        # Assert geometry
        assert pit not in self.blocked_pits
        assert pit - enemy in DIAGONALS
        assert neighbor.get_distance(pit) == 1
        assert neighbor.get_distance(enemy) == 1
        # Check ap and sequence blockers
        ap_cost = 80
        start_pos = next(neighbor.straight_line(enemy))
        mid_pos = next(pit.straight_line(neighbor))
        seq_blocked = {start_pos, neighbor, mid_pos} & self.sequence_blockers
        cannot_reach = self.pos.get_distance(start_pos) > self.ap - ap_cost
        if seq_blocked or cannot_reach:
            return None
        start_path = []
        if self.pos is not start_pos:
            start_path = self.get_path(start_pos)
        if start_path is None:
            return None
        ap_cost += len(start_path) * 10
        if ap_cost > self.ap:
            return None
        # Collect actions and vfx
        actions = [
            *(Move(t) for t in start_path),
            Push(enemy), Move(enemy), Move(mid_pos), Push(neighbor),
            ]
        vfx = [
            {'name': 'mark-green', 'hex': start_pos},
            {'name': 'push', 'hex': start_pos, 'neighbor': enemy},
            {'name': 'push', 'hex': enemy, 'neighbor': neighbor},
            {'name': 'move', 'hex': start_pos, 'neighbor': enemy},
            {'name': 'move', 'hex': enemy, 'neighbor': mid_pos},
            {'name': 'push', 'hex': mid_pos, 'neighbor': neighbor},
            {'name': 'push', 'hex': neighbor, 'neighbor': pit},
            {'name': 'mark-red', 'hex': pit},
        ]
        logger(f'Good sequence!')
        return LethalSequence(ap_cost, actions, vfx)

    def find_lethal_sequences(self):
        lethal_sequences = []
        for enemy_id, enemy_pos in enumerate(self.wi.positions):
            if enemy_id == self.id or not self.wi.alive_mask[enemy_id]:
                continue
            neighboring_pits = set(enemy_pos.neighbors) & self.open_pits
            second_ring_pits = set(enemy_pos.ring(radius=2)) & self.open_pits
            diagonals = set(enemy_pos + d for d in DIAGONALS)
            double_pits = second_ring_pits - diagonals
            diagonal_pits = second_ring_pits & diagonals
            # Neighboring pits
            for pit in neighboring_pits:
                ls = self.push_sequence_simple(pit, enemy_pos)
                if ls is not None:
                    lethal_sequences.append(ls)
            # Double sequence
            for pit in double_pits:
                ls = self.push_sequence_double(pit, enemy_pos)
                if ls is not None:
                    lethal_sequences.append(ls)
            # Diagonal sequence
            for pit in diagonal_pits:
                for n in pit.neighbors:
                    # Hexwise, there are two ways to push a unit 2 tiles diagonally
                    if n.get_distance(enemy_pos) != 1:
                        continue
                    ls = self.push_sequence_diag(pit, n, enemy_pos)
                    if ls is not None:
                        lethal_sequences.append(ls)
        # Sort by ap cost, use number of actions as tiebreaker
        lethal_sequences = sorted(
            lethal_sequences, key=lambda x: x.ap_cost + len(x.actions) / 100)
        return lethal_sequences

    def click_debug(self, hex, button):
        seqs = self.find_lethal_sequences()
        if not seqs:
            return None
        ap_cost, actions, vfx = seqs[0]
        logger('\n'.join(str(a) for a in actions))
        return vfx


BOT = SpitefulBot
