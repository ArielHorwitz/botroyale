# Maintainer: ninja
from collections import defaultdict
from contextlib import contextmanager
import numpy as np
from util.time import pingpong, ping, pong
from util.hexagon import DIAGONALS
from api.bots import BaseBot, CENTER, center_distance
from api.actions import Idle, Move, Push, Jump


DEBUG_VERBOSE = False
BOT_NAME = 'ninja'


MAX_CALC_TIME_MS = 10_000
MEAN_CALC_TIME_MS = 5_000

MIN_AP_PER_MOVE = Move.ap
MIN_AP_PER_PUSH = Push.ap


class CheckPoint:
    EVALUATION_HANDICAP = 0.0
    EVAL_THREAT_FACTOR = 25
    EVAL_KILL_FACTOR = 10
    EVAL_POS_FACTOR = 1
    EVAL_AP_FACTOR = 1
    CONSIDER_DOOMED = True

    def __init__(self, state, logger, friendly_uids):
        self.logger = logger
        self.uid = state.current_unit
        assert self.uid is not None
        self.state = state
        self.friendly_uids = friendly_uids
        done_mask = [self.is_done_turn(uid) for uid in range(state.num_of_units)]
        self.done_ids = set(np.flatnonzero(done_mask))
        self.alive_ids = set(np.flatnonzero(state.alive_mask))
        self.dead_ids = set(np.flatnonzero(~state.alive_mask))

        # My stats
        self.pos = state.positions[self.uid]
        self.ap = state.ap[self.uid]

        # Map features
        self.map_tiles = set(CENTER.range(state.death_radius-1))
        self.doomed_tiles = set(CENTER.ring(state.death_radius-1))
        self.ring_of_death_tiles = set(CENTER.ring(state.death_radius))
        self.blockers = state.walls | set(state.positions)
        self.obstacles = state.pits | self.blockers
        self.reposition_obstacles = self.obstacles - {self.pos}
        self.blocked_pits = state.pits & self.blockers
        self.open_pits = state.pits - self.blockers
        self.open_doomed_tiles = self.doomed_tiles - self.obstacles

        # Enemy stats
        enemy_mask = np.ones(state.num_of_units, dtype=np.bool)
        enemy_mask[self.uid] = False
        enemy_mask[~state.alive_mask] = False
        enemy_mask[friendly_uids] = False
        doomed_mask = [self.is_doomed(uid) for uid in range(state.num_of_units)]
        enemy_mask[doomed_mask] = False
        self.doomed_ids = set(np.flatnonzero(doomed_mask))
        self.enemy_ids = set(np.flatnonzero(enemy_mask))
        self.enemy_pos = set(state.positions[uid] for uid in self.enemy_ids)
        tombstone_ids = set(np.flatnonzero(~state.alive_mask))
        tombstone_ids |= self.doomed_ids
        self.tombstones = set(state.positions[uid] for uid in tombstone_ids)

    @classmethod
    def get_new(cls, *args, **kwargs):
        return cls(*args, **kwargs)

    def __repr__(self):
        return f'<CheckPoint S#{str(self.state.step_count):>4} {str(round(self.ap)):>3} AP {len(self.enemy_ids)} E {str(self.pos):<14}>'

    def _get_branch_sequences(self, recursive_index=0):
        """Returns branching sequences from this checkpoint and their guess
        evaluations as tuple(guess_evaluation, sequence).
        """
        vals_seqs = []
        # Add branching lethal push sequences
        lethal_seqs = self.get_lethal_sequences()

        # Branch recursively for each lethal push sequence
        for push_seq in lethal_seqs:
            branch_cp = self.get_new(push_seq.last_state, self.logger, self.friendly_uids)
            # Extend the push sequence with each sequence in this branch and save it
            branch_vals_seqs = branch_cp._get_branch_sequences(recursive_index+1)
            for val, branch_seq, debug_str in branch_vals_seqs:
                full_seq = push_seq + branch_seq
                vals_seqs.append((val, full_seq, debug_str))

        # Add move sequences
        repos_vals_seqs = self.get_reposition_sequences()
        # We should always at least get an idle sequence, hence assert
        assert repos_vals_seqs
        vals_seqs.extend(repos_vals_seqs)
        return vals_seqs

    def get_sequences(self, calculation_time_ms, debug_verbose=DEBUG_VERBOSE):
        """Returns a list of action sequences from this checkpoint sorted by evaluation."""
        start_time_ms = ping()
        self.logger(f'Searching sequences from {self} (allotted: {calculation_time_ms:.1f} ms)...')
        def remaining_time_ms():
            return calculation_time_ms - pong(start_time_ms)

        # Shortcut if no enemies
        if len(self.enemy_ids) == 0:
            self.logger(f'Found no enemies, finding special sequence.')
            suicide_seq = self.get_suicide_sequence()
            suicide_seq.append(Idle())
            return [suicide_seq]

        # Get all branching sequences and their guess values
        with pingpong('Get all branch sequences', self.logger):
            gvals_seqs = self._get_branch_sequences()
        assert gvals_seqs
        self.logger(f'Found {len(gvals_seqs)} total sequences')
        sorted_gvals_seqs = sorted(gvals_seqs, key=lambda x: x[0], reverse=True)
        gsorted_seqs = [(gval, seq) for gval, seq, debug_str in sorted_gvals_seqs]
        if debug_verbose:
            for gval, seq, debug_str in reversed(sorted_gvals_seqs):
                self.logger(f'Guess: [{self.__format_eval_value(gval)}] {seq}\t{debug_str}')

        # Evaluate the sequences (as many as possible/allowed)
        gs_count = len(gsorted_seqs)
        max_evaluations = max(2, int(gs_count - (gs_count * self.EVALUATION_HANDICAP)))
        self.logger(f'Available evaluation calc time: {remaining_time_ms():.1f} ms')
        self.logger(f'Max evaluations: {max_evaluations} / {gs_count} sequences (handicap: {self.EVALUATION_HANDICAP*100:.1f}%)')
        with pingpong('Sequence evaluations', self.logger):
            vals_seqs = []
            for sidx, (gval, seq) in enumerate(gsorted_seqs):
                cp = self.get_new(seq.last_state, self.logger, self.friendly_uids)
                val, debug_strs = cp.evaluate()
                vals_seqs.append((val, gval, seq, debug_strs))
                if sidx >= max_evaluations-1:
                    break
                if remaining_time_ms() <= 0:
                    self.logger(f'Ran out of time for evaluations!')
                    break

        # Sort and log the sequences with evaluations
        sorted_vals_seqs = sorted(vals_seqs, key=lambda x: x[0], reverse=True)
        final_sorted_seqs = [seq for v, g, seq, d in sorted_vals_seqs]
        didx = len(sorted_vals_seqs) if debug_verbose else 5
        for val, gval, seq, debug_strs in reversed(sorted_vals_seqs[:didx]):
            val_str = self.__format_eval_value(val)
            gval_str = self.__format_eval_value(gval)
            self.logger(f'[{val_str} <- {gval_str}] {str(seq)[:60]:<60}\t{debug_strs}')
        self.logger(f'Finished get_sequences with time remaining: {remaining_time_ms():.1f} ms')
        return final_sorted_seqs

    def get_reposition_sequences(self):
        """Find move sequences and their guess evaluation.
        We assume repositions are done last, before ending our turn."""
        # Collect tiles in potential range
        max_move = int(self.ap / MIN_AP_PER_MOVE)
        available_tiles = set(self.pos.range(max_move)) & self.map_tiles
        available_tiles -= self.doomed_tiles
        available_tiles -= self.reposition_obstacles
        available_tiles |= {self.pos}  # Should at least have our own tile for "idle" reposition

        # Guess evaluate tiles
        tile_values = {}
        tile_debugs = {}
        for tile in available_tiles:
            value, debug_str = self.evaluate_reposition_tile(tile)
            tile_values[tile] = value
            tile_debugs[tile] = debug_str

        # Convert to sequences, filter unreachable tiles, collect in list
        sequences = []
        for tile, val in tile_values.items():
            path_seq = self.get_path_sequence(tile)
            if path_seq is None:
                continue
            sequences.append((val, path_seq, tile_debugs[tile]))
        return sequences

    def get_lethal_sequences(self):
        """Returns action sequences that would be lethal to an enemy."""
        if self.ap < MIN_AP_PER_PUSH:
            return []
        lethal_sequences = []
        for enemy_id in self.enemy_ids:
            ls = self.get_lethal_sequences_uid(enemy_id)
            lethal_sequences.extend(ls)
        # Sort by ap cost, use number of actions as tiebreaker
        lethal_sequences = sorted(lethal_sequences,
            key=lambda x: x.ap + (len(x.actions) / 100))
        return lethal_sequences

    def get_suicide_sequence(self):
        if self.pos == CENTER:
            return ActionSequence(self.state, actions=[Idle()], logger=self.logger, description='Designated winner')
        center_path = self.get_path(CENTER, prune_ap_distance=False)
        if center_path:
            # Ensure at least one of us wins
            path_seq = self._path_to_sequence(center_path,
                allow_partial=True,
                description=f'Designated winner to center',
                )
            return path_seq
        targets = self.open_pits | self.ring_of_death_tiles
        targets = sorted(targets, key=lambda t: self.pos.get_distance(t))[:15]
        def suicide_neighbors(tile):
            neighbors = set(tile.range(2)) - self.state.walls - set(self.state.positions) - {tile}
            return neighbors & (self.map_tiles | self.ring_of_death_tiles)
        def get_next_path():
            target = targets.pop(0)
            path = a_star(self.pos, target, cost=self.pathfinder_cost, get_neighbors=suicide_neighbors)
            return path
        path = get_next_path()
        while targets and not path:
            path = get_next_path()
        if path:
            path_seq = self._path_to_sequence(path,
                allow_partial=True,
                description=f'Suicide path to {path[-1]}',
                )
            return path_seq
        # No path to pit found, give up
        return ActionSequence(self.state, actions=[Idle()], logger=self.logger, description='Suicide idle')

    # EVALUATION
    def evaluate(self):
        """Evaluate ending our turn in this state."""
        if self.uid in self.doomed_ids:
            return float('-inf'), 'doomed'
        kill_value, d_kill = self.evaluate_kills(self.EVAL_KILL_FACTOR)
        ap_value, d_ap = self.evaluate_ap(self.EVAL_AP_FACTOR)
        position_value, d_pos = self.evaluate_position(self.EVAL_POS_FACTOR)
        threat_value, d_threat = self.evaluate_threats(self.EVAL_THREAT_FACTOR)
        total = sum([
            kill_value,
            ap_value,
            position_value,
            threat_value,
        ])
        d = ' | '.join((d_pos, d_ap, d_kill, f'threats: {self.__format_eval_value(threat_value)} '))
        if threat_value:
            d = f'{d}\n\t\t{d_threat}'
        return total, d

    def evaluate_position(self, weight=1):
        # Consider the our position radius
        radius_value = self.evaluate_tile_radius(self.pos) * weight
        d = f'radius:  {self.__format_eval_value(radius_value)}'
        return radius_value, d

    def evaluate_threats(self, weight=1):
        # Check how many possibilities there are to lethally push us from this tile.
        threat_value = 0
        ds = []
        for enemy_id in self.enemy_ids:
            count, d = self.__find_enemy_threat(enemy_id)
            if count:
                threat_value -= count * weight
                ds.append(d)
        d = ' ; '.join(ds)
        return threat_value, d

    SPENT_AP_VALUE_FACTOR = -0.05

    def evaluate_ap(self, weight=1):
        useful_ap = self.ap - max(0, self.ap - BaseBot.ap_regen)
        ap_spent = self.state.round_ap_spent[self.uid]
        useful_ap_value = useful_ap / BaseBot.max_ap * weight
        ap_spent_value = self.SPENT_AP_VALUE_FACTOR * ap_spent / BaseBot.max_ap * weight
        total_ap_value = useful_ap_value + ap_spent_value
        d = f'ap: {self.__format_eval_value(total_ap_value)} ({useful_ap_value:.3f} + {ap_spent_value:.3f})'
        return total_ap_value, d

    def evaluate_kills(self, weight=1):
        if not self.uid in self.alive_ids:
            return float('-inf'), f'LOSING STATE'
        doomed = len(self.doomed_ids)
        alive = len(self.enemy_ids) - doomed
        if alive == 0:
            return float('inf'), f'WINNING STATE'
        dead = len(self.dead_ids)
        kill_value = dead * weight
        d = f'kills: {self.__format_eval_value(kill_value)} ({str(dead):>2} dead /{str(doomed):>2} doom)'
        return kill_value, d

    PIT1_THREAT = 1
    PIT2S_THREAT = 0.5
    PIT2D_THREAT = 0.4
    MAX_ENEMY_THREAT_DIST = (BaseBot.max_ap - MIN_AP_PER_PUSH) / MIN_AP_PER_MOVE + 1

    def evaluate_reposition_tile(self, tile):
        """Quickly guess the evaulation of standing on tile at the end of our turn."""
        assert tile not in self.reposition_obstacles
        if tile in self.doomed_tiles:
            return float('-inf'), 'doomed tile'
        # Consider the distance to the ring of death
        radius_value = self.evaluate_tile_radius(tile)
        # We like being next to walls and tombstones
        neighbor_walls = len(set(tile.neighbors) & (self.state.walls | self.tombstones))
        # Beware of nearby enemies
        enemy_distances = np.asarray([tile.get_distance(e) for e in self.enemy_pos])
        enemy_threat = np.sum(enemy_distances <= self.MAX_ENEMY_THREAT_DIST)
        # Beware of nearby pits (only if near enemies)
        pit_threat = 0
        if enemy_threat:
            diags = set(tile+d for d in DIAGONALS)
            pits_a = self.open_pits & set(tile.neighbors)
            pits_2 = self.open_pits & set(tile.ring(2))
            pits_s = pits_2 - diags
            pits_d = pits_2 & diags
            # Adjascent pits
            for pit in list(pits_a):
                if next(pit.straight_line(tile)) in self.reposition_obstacles:
                    pits_a.remove(pit)
            # Straight pits
            for pit in list(pits_s):
                sn = shared_neighbors(pit, tile)
                assert len(sn) == 1
                n = sn.pop()
                start_blocked = next(n.straight_line(tile)) in self.reposition_obstacles
                neighbor_blocked = n in self.reposition_obstacles
                if any((start_blocked, neighbor_blocked)):
                    pits_s.remove(pit)
            # Diagonal pits
            for pit in list(pits_d):
                sn = shared_neighbors(pit, tile)
                assert len(sn) == 2
                for n in sn:
                    neighbor_blocked = n in self.reposition_obstacles
                    start_blocked = next(n.straight_line(tile)) in self.reposition_obstacles
                    mid_blocked = next(pit.straight_line(n)) in self.reposition_obstacles
                    if any((start_blocked, neighbor_blocked, mid_blocked)):
                        pits_d.remove(pit)
                        # TODO consider both diagonal options as threat
                        break
            pit_threat += self.PIT1_THREAT * len(pits_a)
            pit_threat += self.PIT2S_THREAT * len(pits_s)
            pit_threat += self.PIT2D_THREAT * len(pits_d)
        # Weight and sum values
        radius_value = radius_value * 10
        wall_value = neighbor_walls * 0.5
        pit_value = -pit_threat * enemy_threat
        total = sum((radius_value, wall_value, pit_value))
        pitstr = self.__format_eval_value(pit_value)
        if pit_value:
            a_str = ''.join(f'{p.xy}' for p in pits_a)
            s_str = ''.join(f'{p.xy}' for p in pits_s)
            d_str = ''.join(f'{p.xy}' for p in pits_d)
            pitstr = f'{pitstr} {enemy_threat} E a:{a_str} s:{s_str} d:{d_str}'
        debug_str = '\t| '.join([
            f'radius: {self.__format_eval_value(radius_value)}',
            f'wall neighbors: {self.__format_eval_value(wall_value)}',
            f'pits: {pitstr}',
            ])
        return total, debug_str

    def evaluate_tile_radius(self, tile):
        if tile in self.doomed_tiles:
            return float('-inf')
        center_distance_ratio = center_distance(tile) / self.state.death_radius
        rod_distance_ratio = 1 - center_distance_ratio
        return (rod_distance_ratio - center_distance_ratio)

    THREAT_IDLE_COST_FACTOR = 0.3
    THREAT_AP_COST_FACTOR = 0.3

    def __find_enemy_threat(self, enemy_id):
        """Returns the weighted number of options enemy_id has to lethally push us from this state."""
        state = self.state.copy()
        total_threat = 0
        d = []
        extra_ap_cost_max = BaseBot.max_ap - MIN_AP_PER_PUSH
        # Find the(<=2) states that is the enemy's turn before ours
        enemy_turns = []
        enemy_turn_state = iter_state_to_turn(state, enemy_id, self.uid)
        while True:
            if enemy_turn_state is None:
                break
            enemy_turns.append(enemy_turn_state)
            enemy_turn_state = iter_state_to_turn(enemy_turn_state, enemy_id, self.uid)
        # For each state, check push sequences against us
        for sidx, enemy_turn in enumerate(enemy_turns):
            cp = self.get_new(enemy_turn, self.logger, self.friendly_uids)
            enemy_push_sequences = cp.get_lethal_sequences_uid(self.uid)
            if not enemy_push_sequences:
                continue
            for pseq in enemy_push_sequences:
                extra_ap_cost = pseq.ap - MIN_AP_PER_PUSH
                assert extra_ap_cost >= 0
                ap_cost_ratio = extra_ap_cost / extra_ap_cost_max
                ap_cost = ap_cost_ratio * self.THREAT_AP_COST_FACTOR
                idle_cost = sidx * self.THREAT_IDLE_COST_FACTOR
                pthreat = 1 - ap_cost - idle_cost
                total_threat += pthreat
                origin = pseq.last_state.positions[enemy_id].xy
                pit = pseq.last_state.positions[self.uid].xy
                d.append(f'{enemy_id}[{sidx+1},{extra_ap_cost}]{origin}->{pit}={pthreat:.2f}')
            # Don't count the next turn, we assume a threat on this turn is stronger than the next turn
            break
        return total_threat, ' ; '.join(d)

    @staticmethod
    def __format_eval_value(v):
        return f'{f"{v:.3f}":>7}'

    # MOVEMENT
    def get_path(self, target, prune_ap_distance=True):
        if target == self.pos:
            return []
        if target in self.obstacles:
            return None
        enough_ap = self.ap >= self.pos.get_distance(target) * MIN_AP_PER_MOVE
        if not enough_ap and prune_ap_distance:
            return None
        return a_star(
            self.pos, target,
            cost=self.pathfinder_cost,
            get_neighbors=self.pathfinder_neighbors,
            )

    def get_path_sequence(self, target, description=None):
        path = self.get_path(target)
        if path is None:
            return None
        return self._path_to_sequence(path, description=description)

    def _path_to_sequence(self, path, description=None, allow_partial=False):
        actions = []
        current = self.pos
        ap_sum = 0
        for next_tile in path:
            assert 1 <= current.get_distance(next_tile) <= 2
            acls = Move if current.get_distance(next_tile) == 1 else Jump
            ap_sum += acls.ap
            if ap_sum > self.ap:
                if not allow_partial:
                    return None
                if description is None:
                    description = f'Path->{current.xy}->{path[-1].xy}'
                break
            actions.append(acls(next_tile))
            current = next_tile
        if description is None:
            description = f'Path->{current.xy}' if current != self.pos else f'No move'
        return ActionSequence(
            self.state, actions=actions, logger=self.logger, description=description)

    def pathfinder_cost(self, origin, target):
        dist = origin.get_distance(target)
        assert 1 <= dist <= 2
        return Move.ap if dist == 1 else Jump.ap

    def pathfinder_neighbors(self, tile):
        tiles = set(tile.range(2)) - self.obstacles - {tile}
        return tiles & self.map_tiles

    # OFFENSE
    def get_lethal_sequences_uid(self, uid):
        """Returns the lethal sequences by us against uid from this checkpoint."""
        if uid not in self.enemy_ids:
            return []
        sequences = []
        enemy_pos = self.state.positions[uid]
        open_pits = self.open_pits
        if self.CONSIDER_DOOMED and uid in self.done_ids:
            open_pits = open_pits | self.open_doomed_tiles
        neighboring_pits = open_pits & set(enemy_pos.neighbors)
        second_ring_pits = open_pits & set(enemy_pos.ring(radius=2))
        diagonals = set(enemy_pos + d for d in DIAGONALS)
        double_pits = second_ring_pits - diagonals
        diagonal_pits = second_ring_pits & diagonals
        # Neighboring pits
        for pit in neighboring_pits:
            ls = self.__push_sequence_simple(pit, enemy_pos)
            if ls is not None:
                sequences.append(ls)
        # Double sequence
        for pit in double_pits:
            ls = self.__push_sequence_double(pit, enemy_pos)
            if ls is not None:
                sequences.append(ls)
        # Diagonal sequence
        for pit in diagonal_pits:
            # Hexwise, there are two ways to push a unit 2 tiles diagonally
            for n in shared_neighbors(pit, enemy_pos):
                ls = self.__push_sequence_diag(pit, n, enemy_pos)
                if ls is not None:
                    sequences.append(ls)
        return sequences

    def __push_sequence_simple(self, pit, enemy):
        # Assert geometry
        assert pit not in self.blockers
        assert pit in enemy.neighbors
        # Get to start position
        start_pos = next(pit.straight_line(enemy))
        desc = f'Push->{pit.xy}'
        aseq = self.get_path_sequence(start_pos, description=desc)
        if aseq is None:
            return None
        # Add push sequence
        legal = aseq.append(Push(enemy))
        if not legal:
            return None
        return aseq

    def __push_sequence_double(self, pit, enemy):
        # Assert geometry
        assert pit not in self.blockers
        assert pit - enemy not in DIAGONALS
        assert pit.get_distance(enemy) == 2
        mid_points = set(enemy.neighbors) & set(pit.neighbors)
        assert len(mid_points) == 1
        mid_point = mid_points.pop()
        # Check ap and sequence blockers
        ap_cost = Push.ap * 2 + Move.ap
        vector = enemy - mid_point
        start_pos = enemy + vector
        if mid_point in self.obstacles:
            return None
        aseq = self.get_path_sequence(start_pos, description=f'Push {enemy} -> {pit}')
        if aseq is None:
            return None
        legal = aseq.extend([Push(enemy), Move(enemy), Push(mid_point)])
        if not legal:
            return None
        return aseq

    def __push_sequence_diag(self, pit, neighbor, enemy):
        # Assert geometry
        assert pit not in self.blockers
        assert pit - enemy in DIAGONALS
        assert neighbor.get_distance(pit) == 1
        assert neighbor.get_distance(enemy) == 1
        # Check ap and sequence blockers
        start_pos = next(neighbor.straight_line(enemy))
        mid_pos = next(pit.straight_line(neighbor))
        if {neighbor, mid_pos} & self.obstacles:
            return None
        aseq = self.get_path_sequence(start_pos, description=f'Push {enemy} -> {pit}')
        if aseq is None:
            return None
        legal = aseq.extend([Push(enemy), Move(enemy), Move(mid_pos), Push(neighbor)])
        if not legal:
            return None
        return aseq

    def is_doomed(self, uid):
        alive = uid in self.alive_ids
        is_done = self.is_done_turn(uid)
        in_doomed_tile = self.state.positions[uid] in self.doomed_tiles
        return alive and is_done and in_doomed_tile

    def is_done_turn(self, uid):
        return uid not in self.state.round_remaining_turns


class ActionSequence:
    def __init__(self, state, logger,
            actions=None, description='No description',
            ):
        self.description = description
        self.logger = logger
        self.states = [state]
        self.__actions = []
        if actions:
            self.extend(actions)

    def __len__(self):
        return len(self.__actions)

    def __repr__(self):
        end = ' ends turn' if self.turn_end else ''
        return f'<ActionSequence: -{str(self.ap):<3} AP{end} ({len(self)} actions) | {self.description}>'

    def __add__(self, other_seq):
        return ActionSequence(
            self.initial_state,
            actions=[*self.actions, *other_seq.actions],
            description=f'{self.description} + {other_seq.description}',
            logger=self.logger,
            )

    @property
    def initial_state(self):
        return self.states[0]

    @property
    def last_state(self):
        return self.states[-1]

    @property
    def turn_end(self):
        diff_unit = self.initial_state.current_unit != self.last_state.current_unit
        return diff_unit

    @property
    def actions(self):
        return list(self.__actions)

    @property
    def ap(self):
        if len(self.__actions) == 0:
            return 0
        actions = (s.last_action for s in self.states[1:])
        return sum(a.ap for a in actions)

    def append(self, action):
        if self.turn_end or self.last_state.game_over:
            return
        if not self.last_state.check_legal_action(action=action):
            return False
        new_state = self.last_state.apply_action(action)
        self.__actions.append(action)
        self.states.append(new_state)
        return True

    def extend(self, actions):
        for a in actions:
            if not self.append(a):
                return False
        return True

    def unlock(self):
        self.__locked = False

    def get_vfx(self):
        uid = self.states[0].round_remaining_turns[0]
        vfx = []
        for i, action in enumerate(self.__actions):
            my_pos = self.states[i].positions[uid]
            if type(action) is Move:
                aname = 'move'
            elif type(action) is Jump:
                aname = 'jump'
            elif type(action) is Push:
                aname = 'push'
            vfx.append({'name': aname, 'hex': my_pos, 'direction': action.target})
        return vfx


class Bot(BaseBot):
    SPRITE = 'fox'
    checkpoint_class = CheckPoint
    logging_enabled = True
    game_started = False
    enable_cooperation = False
    current_game_hash = None
    friendly_uids = []

    @classmethod
    def add_friendly_uid(cls, state, uid):
        state_hash_value = hash_state(state)
        if state_hash_value != cls.current_game_hash:
            cls.current_game_hash = state_hash_value
            cls.friendly_uids = []
        cls.friendly_uids.append(uid)

    def setup(self, state):
        if self.enable_cooperation:
            self.add_friendly_uid(state, self.id)
        self.timer = []
        self.current_sequence = []
        self.last_known_round = state.round_count
        self.last_state = state
        self.turn_step = 0

    def update(self, state):
        self.game_started = True
        self.last_state = state
        if state.round_count > self.last_known_round:
            self.logger(f'First step in round {state.round_count} (last round: {self.last_known_round})')
            self.last_known_round = state.round_count
            self.turn_step = 0
            self.current_sequence = []
        else:
            self.turn_step += 1

    def poll_action(self, state):
        self.update(state)
        if not self.current_sequence:
            self.logger(f'Searching sequences...')
            aseq = self.get_sequence(state)
            self.current_sequence = list(aseq.actions)
            self.logger(f'Set new sequence {aseq}')
        seq_str = '\n'.join(f'-> {a}' for a in self.current_sequence)
        self.logger(f'Remaining sequence:\n{seq_str}')
        self.logger('_'*30)
        action = self.current_sequence.pop(0)
        return action

    def get_sequence(self, state):
        cp = self.get_new_checkpoint(state, self.logger, self.friendly_uids)
        with self.time_allocation() as allotted_time:
            seqs = cp.get_sequences(allotted_time)
        assert seqs
        best_seq = seqs[0]
        best_seq.append(Idle())
        return best_seq

    def get_new_checkpoint(self, *args, **kwargs):
        return self.checkpoint_class.get_new(*args, **kwargs)

    @contextmanager
    def time_allocation(self):
        turn_count = len(self.timer)
        assert turn_count == self.last_state.round_count - 1
        target_mean = MEAN_CALC_TIME_MS * 0.9 - 300
        max_allocation = MAX_CALC_TIME_MS * 0.9 - 300
        min_allocation = MAX_CALC_TIME_MS * 0.1
        if turn_count == 0:
            current_mean = target_mean
        else:
            current_mean = np.mean(np.asarray(self.timer))
        total_spent = np.sum(np.asarray(self.timer))
        allocated = target_mean * turn_count + target_mean - total_spent
        allocated = max(min_allocation, min(max_allocation, allocated))
        self.logger(f'Allocated time on turn count {turn_count+1}: {allocated:.3f}')
        self.logger(f'Mean and target: {current_mean:.3f} -> {target_mean:.3f}')
        p = ping()
        yield allocated
        spent = pong(p)
        self.timer.append(spent)

    def gui_click_debug(self, hex):
        if self.game_started:
            cp = self.get_new_checkpoint(self.last_state, self.logger, self.friendly_uids)
            self.logger(f'EVAL state: {cp.evaluate()}')


def iter_state_to_turn(state, uid, only_before_uid=None, ignore_initial_state=True):
    """
    Given a state, find the state of uid's next turn that is before
    `only_before_uid` by repeatedly applying Idle(). Return None if no such
    state is found. `ignore_initial_state` will Idle the first turn if it is
    one of uid or `only_before_uid`.
    """
    if state.game_over:
        return None
    if ignore_initial_state:
        if state.current_unit == uid or state.current_unit == only_before_uid:
            state = state.apply_action(Idle())
    while not state.game_over and state.current_unit != only_before_uid:
        if state.current_unit == uid:
            return state
        state = state.apply_action(Idle())
    return None


def shared_neighbors(tile1, tile2):
    assert tile1.get_distance(tile2) == 2
    return set(tile1.neighbors) & set(tile2.neighbors)


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


def a_star(origin, target, cost, get_neighbors):
    def _get_full_path(node, came_from):
        full_path = [node]
        while node in came_from:
            node = came_from[node]
            full_path.insert(0, node)
        return tuple(full_path[1:])

    if origin == target:
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
        if current == target:
            return _get_full_path(current, came_from)
        open_set.remove(current)
        for neighbor in get_neighbors(current):
            tentative_partial_score = partial_score[current] + cost(current, neighbor)
            if tentative_partial_score < partial_score[neighbor]:
                came_from[neighbor] = current
                partial_score[neighbor] = tentative_partial_score
                guess_score[neighbor] = tentative_partial_score + neighbor.get_distance(target)
                if neighbor not in open_set:
                    open_set.add(neighbor)
    return None


# Difficulty variations
class CheckPointL1(CheckPoint):
    EVALUATION_HANDICAP = 0.3


class CheckPointL2(CheckPoint):
    EVALUATION_HANDICAP = 0.6


class CheckPointL3(CheckPoint):
    EVALUATION_HANDICAP = 0.9


# Behavior variations
class CheckPointAggressive(CheckPoint):
    EVAL_THREAT_FACTOR = 10
    EVAL_KILL_FACTOR = 25


class CheckPointPacifist(CheckPoint):
    EVAL_KILL_FACTOR = 0.01


class CheckPointNoDoomed(CheckPoint):
    CONSIDER_DOOMED = True


class CheckPointCenterRush(CheckPoint):
    EVAL_POS_FACTOR = 3
    EVAL_AP_FACTOR = 0.01


# Bot personas
class BotBoss(Bot):
    NAME = f'{BOT_NAME}-boss'
    COLOR_INDEX = 0


class BotMaster(Bot):
    NAME = f'{BOT_NAME}-hard'
    COLOR_INDEX = 1
    checkpoint_class = CheckPointL1


class BotHard(Bot):
    NAME = f'{BOT_NAME}-medium'
    COLOR_INDEX = 3
    checkpoint_class = CheckPointL2


class BotEasy(Bot):
    NAME = f'{BOT_NAME}-easy'
    COLOR_INDEX = 5
    checkpoint_class = CheckPointL3


class BotAggro(Bot):
    TESTING_ONLY = True
    NAME = f'{BOT_NAME}-aggro'
    checkpoint_class = CheckPointAggressive


class BotDefensive(Bot):
    TESTING_ONLY = True
    NAME = f'{BOT_NAME}-def'
    checkpoint_class = CheckPointPacifist


class BotCooperator(Bot):
    TESTING_ONLY = True
    NAME = f'{BOT_NAME}-coop'
    COLOR_INDEX = 10
    enable_cooperation = True
    checkpoint_class = CheckPointCenterRush


BOTS = [
    BotBoss,
    BotMaster,
    BotHard,
    BotEasy,
    BotAggro,
    BotDefensive,
    BotCooperator,
    ]
