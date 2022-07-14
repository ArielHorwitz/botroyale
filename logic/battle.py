import numpy as np
from api.logic import BaseLogicAPI
from bots import make_bots
from logic import maps
from api.bots import world_info
import copy
from util.settings import Settings
from api.actions import Action, Move, Push, IllegalAction, Idle
from util.hexagon import Hex


MAX_ROUNDS = Settings.get('logic.round_cap', 300)
RNG = np.random.default_rng()


class Battle(BaseLogicAPI):
    def __init__(self):
        super().__init__()
        map = maps.get_map()
        self.map_size_hint = map.radius + 0.2
        # Bots
        self.num_of_bots = len(map.spawns)
        self.bots = make_bots(self.num_of_bots)
        self.unit_colors = [self.get_color(bot.COLOR_INDEX) for bot in self.bots]
        # Map
        self.center = Hex(0, 0)
        # Ring contracts before the first round, so we set the ring even
        # further out than one tile past the map radius.
        self.ring_radius = map.radius + 2
        self.positions = map.spawns
        self.walls = map.walls
        # Add the first ring now (the one added before the first round)
        self.pits = map.pits | set(self.center.ring(map.radius+1))
        # Metadata
        self.alive_mask = np.ones(self.num_of_bots, dtype=bool)
        self.step_count = 0
        self.turn_count = 0
        self.round_count = 0
        self.ap = np.zeros(self.num_of_bots)
        self.round_ap_spent = np.zeros(self.num_of_bots)
        # when round_priority is empty, round is over.
        self.round_remaining_turns = []
        self.history = []

    def next_step(self):
        if self.game_over:
            return
        self.step_count += 1
        if len(self.round_remaining_turns) == 0:
            self._next_round()
            return
        bot_id = self.round_remaining_turns[0]
        self.logger('='*50)
        self.logger(f'R: {self.round_count} T: {self.turn_count} S: {self.step_count} | #{bot_id:<2} {self.bots[bot_id].name}')
        self.logger('='*50)
        action = self._get_bot_action(bot_id)
        if not action.has_effect:
            self.round_remaining_turns.pop(0)
            self.turn_count += 1
            return
        self.logger(f'Applying bot #{bot_id} action: {action}')
        self._apply_action(bot_id, action)

    def _next_round(self):
        self._next_round_order()
        self.round_ap_spent = np.zeros(self.num_of_bots)
        self.ap[self.alive_mask] += 50
        self.ap[self.ap > 100] = 100
        self.round_count += 1
        self.ring_radius -= 1
        self.pits |= set(self.center.ring(self.ring_radius))
        self._apply_mortality()

    def _next_round_order(self):
        bots_id = np.arange(self.num_of_bots)
        p = RNG.permutation(bots_id[self.alive_mask])
        while len(p) > 0:
            min_index = np.argmin(self.round_ap_spent[p][self.alive_mask[p]])
            self.round_remaining_turns.append(p[min_index])
            p = np.delete(p, min_index)

    def _get_bot_action(self, bot_id):
        world_state = self.set_world_info()
        action = self.bots[bot_id].get_action(world_state)
        if not isinstance(action, Action):
            self.logger(f'Revceived NON-ACTION type from #{bot_id} {self.bots[bot_id].name}: {action} {self.bots[bot_id]}')
            return IllegalAction()
        if action.has_effect:
            if not self._check_legal_action(bot_id, action):
                self.logger(f'Revceived ILLEGAL action from #{bot_id} {self.bots[bot_id].name}: {action} {self.bots[bot_id]}')
                return IllegalAction()
        return action

    def _check_legal_action(self, bot_id, action):
        if not self.check_ap(bot_id, action.ap):
            self.logger(f'Unit #{bot_id} missing AP: {action}')
            return False
        if isinstance(action, Push):
            return self._check_legal_push(bot_id, action.target)
        if isinstance(action, Move):
            return self._check_legal_move(bot_id, action.target)
        raise TypeError(f'Unknown action: {action}')

    def check_ap(self, bot_id, ap_cost):
        return self.ap[bot_id] >= ap_cost

    def _check_legal_move(self, bot_id, target_tile):
        # check if target is a neighbor
        self_position = self.positions[bot_id]
        if not self_position.get_distance(target_tile) == 1:
            self.logger(f'Illegal move by Unit #{bot_id}: not neighbor {self_position} -> {target_tile}')
            return False
        # check if moving into a wall
        if target_tile in self.walls:
            self.logger(f'Illegal move by Unit #{bot_id}: is wall {self_position} -> {target_tile}')
            return False
        # check if moving on top of another bot
        if target_tile in self.positions:
            self.logger(f'Illegal move by Unit #{bot_id}: is unit {self_position} -> {target_tile}')
            return False
        return True

    def _check_legal_push(self, bot_id, target_tile):
        # check if target is a neighbor
        self_position = self.positions[bot_id]
        if not self_position.get_distance(target_tile) == 1:
            self.logger(f'Illegal push by Unit #{bot_id}: not neighbor {self_position} -> {target_tile}')
            return False
        # check if actually pushing a bot
        if not (target_tile in self.positions):
            self.logger(f'Illegal push by Unit #{bot_id}: no unit {self_position} -> {target_tile}')
            return False
        # check if pushing to a wall
        self_pos = self.positions[bot_id]
        push_end = next(self_pos.straight_line(target_tile))
        if push_end in self.walls:
            self.logger(f'Illegal move by Unit #{bot_id}: against wall {self_position} -> {target_tile}')
            return False
        # check if pushing on top of another bot
        if push_end in self.positions:
            self.logger(f'Illegal move by Unit #{bot_id}: against unit {self_position} -> {target_tile}')
            return False
        return True

    def _apply_action(self, bot_id, action):
        assert action.has_effect
        if isinstance(action, Push):
            self.logger(f'{bot_id} APPLY PUSH: {action}')
            opp_id = self.positions.index(action.target)
            self_pos = self.positions[bot_id]
            self.positions[opp_id] = next(self_pos.straight_line(action.target))
            self.add_vfx('push', self_pos, action.target)
            self.add_vfx('push', action.target, self.positions[opp_id])
        elif isinstance(action, Move):
            self.logger(f'{bot_id} APPLY MOVE: {action}')
            old_pos = self.positions[bot_id]
            self.positions[bot_id] = action.target
            self.add_vfx('move', old_pos, action.target)
        self._apply_mortality()
        self.ap[bot_id] -= action.ap
        self.round_ap_spent[bot_id] += action.ap

    def _apply_mortality(self):
        live_bots = np.flatnonzero(self.alive_mask)
        for bot_id in live_bots:
            if self.positions[bot_id] in self.pits:
                self.add_vfx('death', self.positions[bot_id])
                self.alive_mask[bot_id] = False
                if bot_id in self.round_remaining_turns:
                    self.round_remaining_turns.remove(bot_id)
                # Move to graveyard
                # TODO move to graveyard when GUI can handle it
                # self.positions[bot_id] = Hex(10**6+bot_id, 10**6)

    def get_map_state(self):
        return self.get_match_state()

    @property
    def casualties(self):
        return np.arange(self.num_of_bots)[~self.alive_mask]

    @property
    def round_done_turns(self):
        return [bid for bid in range(self.num_of_bots) if (bid not in self.casualties and bid not in self.round_remaining_turns)]

    def get_match_state(self):
        def get_bot_string(bot_id):
            bot = self.bots[bot_id]
            ap = round(self.ap[bot_id])
            pos = self.positions[bot_id]
            name_label = f'#{bot_id:<2} {bot.name[:15]:<15}'
            bot_str = f'{name_label} {ap:>3} AP {pos}'
            if bot_id in self.casualties:
                bot_str = f'[s]{bot_str}[/s]'
            return bot_str
        unit_strs = []
        unit_strs.extend(get_bot_string(bot_id) for bot_id in self.round_remaining_turns)
        unit_strs.append('-'*10)
        unit_strs.extend(get_bot_string(bot_id) for bot_id in self.round_done_turns)
        unit_strs.append('='*10)
        unit_strs.extend(get_bot_string(bot_id) for bot_id in self.casualties)
        unit_strs = '\n'.join(unit_strs)
        if self.round_remaining_turns:
            bot_id = self.round_remaining_turns[0]
            bot = self.bots[bot_id]
            turn_str = f'#{bot_id:<2} {bot.name}\'s turn'
        else:
            turn_str = f'starting new round'
        state_str = '\n'.join([
            f'Ring of death radius:  {self.ring_radius}',
            f'Round: #{self.round_count:<3} Turn: #{self.turn_count:<4} Step: #{self.step_count:<5}',
            f'Currently:  [u]{turn_str}[/u]',
            '',
            f'{unit_strs}',
        ])
        if self.game_over:
            winner_str = ''
            if self.alive_mask.sum() == 1:
                winner = np.arange(self.num_of_bots)[self.alive_mask]
                winner_str = f'This game winner is: unit #{winner[0]}'
            status_str = f'GAME OVER\n{winner_str}'
        else:
            autoplay = 'Playing' if self.autoplay else 'Paused'
            status_str = f'{autoplay} <= {1000 / self.step_interval_ms:.2f} steps/second'
        return f'{status_str}\n\n{state_str}'

    def set_world_info(self):
        return world_info(
            positions=copy.copy(self.positions),
            walls=copy.copy(self.walls),
            pits=copy.copy(self.pits),
            ring_radius=self.ring_radius,
            alive_mask=copy.deepcopy(self.alive_mask),
            turn_count=self.turn_count,
            round_count=self.round_count,
            ap=copy.deepcopy(self.ap),
            round_ap_spent=copy.deepcopy(self.round_ap_spent),
            round_remaining_turns=copy.deepcopy(self.round_remaining_turns),
            )

    def debug(self):
        super().debug()

    @staticmethod
    def _calc_ap(pos, target):
        return 10 * (pos is not target)

    @property
    def game_over(self):
        cond1 = self.round_count > MAX_ROUNDS
        cond2 = self.alive_mask.sum() <= 1
        return cond1 or cond2

    def handle_hex_click(self, hex, button):
        super().handle_hex_click(hex, button)
        if hex in self.positions:
            bot_id = self.positions.index(hex)
            vfx_seq = self.bots[bot_id].click_debug(hex, button)
            if vfx_seq is not None:
                for vfx_kwargs in vfx_seq:
                    vfx_kwargs['steps'] = 1
                    self.add_vfx(**vfx_kwargs)
        else:
            if button == 'left':
                vfx = 'mark-green'
            elif button == 'right':
                vfx = 'mark-red'
            else:
                vfx = 'mark-blue'
            self.add_vfx(vfx, hex, steps=1)
