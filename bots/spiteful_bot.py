# Maintainer: ninja
import random
from collections import namedtuple, defaultdict
from bots import BaseBot
from util.hexagon import Hex, DIAGONALS, is_hex
from util.settings import Settings
from api.actions import Move, Push, Idle


LethalSequence = namedtuple('LethalSequence', ['ap_cost', 'actions', 'vfx'])


class SpitefulBot(BaseBot):
    TESTING_ONLY = True
    NAME = 'spiteful'
    SPRITE = 'fox'
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
        if self.ap < Move.ap:
            self.logger(f'Out of AP.')
            return Idle()

        if not self.current_sequence:
            self.logger(f'No sequence.')
            seqs = self.find_lethal_sequences()
            if seqs:
                seq_str = '\n'.join(f'{s.ap_cost} AP {" ".join(str(a) for a in s.actions)}' for s in seqs)
                self.logger(f'Found sequences:\n{seq_str}')
                self.current_sequence = list(seqs[0].actions)

        if self.current_sequence:
            s = '\n'.join(f'-> {a}' for a in self.current_sequence)
            self.logger(f'Remaining sequence:\n{s}')
            action = self.current_sequence.pop(0)
            return action

        target_distance = self.wi.ring_radius - 3
        if self.pos.get_distance(self.map_center) > target_distance:
            path = self.path_as_close(self.map_center)
            if path:
                trunc_path = []
                moves = int(self.ap/Move.ap)
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
                    self.logger(f'Moving to center: {self.current_sequence[0]} {len(self.current_sequence)} steps to target')
                    return self.current_sequence.pop(0)
                self.logger(f'On edge but cannot reach safer tile!')
            else:
                self.logger(f'On edge but no path to center!')

        self.logger(f'Idling.')
        return Idle()

    def move_tile_cost(self, origin, target):
        is_obstacle = target in (self.wi.pits | self.wi.walls | set(self.wi.positions))
        obs_cost = float('inf') if is_obstacle else 0
        return 1 + obs_cost

    def get_path(self, target):
        return a_star(self.pos, target, cost=self.move_tile_cost)

    def get_paths(self, targets, sort=len):
        targets = (t for t in targets if self.move_tile_cost(None, t) < float('inf'))
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
        self.logger(f'Considering simple push sequence: {enemy} -> {pit}')
        # Assert geometry
        assert pit not in self.blocked_pits
        assert pit in enemy.neighbors
        # Check ap and sequence blockers
        ap_cost = Push.ap
        start_pos = next(pit.straight_line(enemy))
        cannot_reach = self.pos.get_distance(start_pos) > self.ap - ap_cost
        if start_pos in self.sequence_blockers or cannot_reach:
            return None
        start_path = []
        if self.pos is not start_pos:
            start_path = self.get_path(start_pos)
        if start_path is None:
            return None
        ap_cost += len(start_path) * Move.ap
        if ap_cost > self.ap:
            return None
        # Collect actions and vfx
        actions = [
            *(Move(t) for t in start_path),
            Push(enemy),
            ]
        vfx = [
            {'name': 'mark-green', 'hex': start_pos},
            {'name': 'push', 'hex': start_pos, 'direction': enemy},
            {'name': 'push', 'hex': enemy, 'direction': pit},
            {'name': 'mark-red', 'hex': pit},
            ]
        self.logger(f'Good sequence!')
        return LethalSequence(ap_cost, actions, vfx)

    def push_sequence_double(self, pit, enemy):
        self.logger(f'Considering double push sequence: {enemy} -> {pit}')
        # Assert geometry
        assert pit not in self.blocked_pits
        assert pit - enemy not in DIAGONALS
        assert pit.get_distance(enemy) == 2
        mid_points = set(enemy.neighbors) & set(pit.neighbors)
        assert len(mid_points) == 1
        mid_point = mid_points.pop()
        # Check ap and sequence blockers
        ap_cost = Move.ap + Push.ap*2
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
        ap_cost += len(start_path) * Move.ap
        if ap_cost > self.ap:
            return None
        # Collect actions and vfx
        actions = [
            *(Move(t) for t in start_path),
            Push(enemy), Move(enemy), Push(mid_point),
            ]
        vfx = [
            {'name': 'mark-green', 'hex': start_pos},
            {'name': 'push', 'hex': start_pos, 'direction': enemy},
            {'name': 'push', 'hex': enemy, 'direction': mid_point},
            {'name': 'move', 'hex': start_pos, 'direction': enemy},
            {'name': 'push', 'hex': enemy, 'direction': mid_point},
            {'name': 'push', 'hex': mid_point, 'direction': pit},
            {'name': 'mark-red', 'hex': pit},
        ]
        self.logger(f'Good sequence!')
        return LethalSequence(ap_cost, actions, vfx)

    def push_sequence_diag(self, pit, neighbor, enemy):
        self.logger(f'Considering diagonal push sequence: {enemy} -> {neighbor} -> {pit}')
        # Assert geometry
        assert pit not in self.blocked_pits
        assert pit - enemy in DIAGONALS
        assert neighbor.get_distance(pit) == 1
        assert neighbor.get_distance(enemy) == 1
        # Check ap and sequence blockers
        ap_cost = Move.ap*2 + Push.ap*2
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
        ap_cost += len(start_path) * Move.ap
        if ap_cost > self.ap:
            return None
        # Collect actions and vfx
        actions = [
            *(Move(t) for t in start_path),
            Push(enemy), Move(enemy), Move(mid_pos), Push(neighbor),
            ]
        vfx = [
            {'name': 'mark-green', 'hex': start_pos},
            {'name': 'push', 'hex': start_pos, 'direction': enemy},
            {'name': 'push', 'hex': enemy, 'direction': neighbor},
            {'name': 'move', 'hex': start_pos, 'direction': enemy},
            {'name': 'move', 'hex': enemy, 'direction': mid_pos},
            {'name': 'push', 'hex': mid_pos, 'direction': neighbor},
            {'name': 'push', 'hex': neighbor, 'direction': pit},
            {'name': 'mark-red', 'hex': pit},
        ]
        self.logger(f'Good sequence!')
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


def a_star(origin, target, cost):
    def _get_full_path(node, came_from):
        full_path = [node]
        while node in came_from:
            node = came_from[node]
            full_path.insert(0, node)
        return tuple(full_path[1:])

    if origin is target:
        return None

    open_set = {origin}
    came_from = {}
    partial_score = defaultdict(lambda: float('inf'))
    partial_score[origin] = 0
    guess_score = defaultdict(lambda: float('inf'))
    guess_score[origin] = origin.get_distance(target)

    while open_set:
        best_nodes = sorted(open_set, key=lambda x: guess_score[x])
        current = best_nodes[0]
        if current is target:
            return _get_full_path(current, came_from)
        open_set.remove(current)
        for neighbor in current.neighbors:
            tentative_partial_score = partial_score[current] + cost(current, neighbor)
            if tentative_partial_score < partial_score[neighbor]:
                came_from[neighbor] = current
                partial_score[neighbor] = tentative_partial_score
                guess_score[neighbor] = tentative_partial_score + neighbor.get_distance(target)
                if neighbor not in open_set:
                    open_set.add(neighbor)
    return None


BOT = SpitefulBot
