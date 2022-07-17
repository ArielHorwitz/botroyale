# Maintainer: ninja
import numpy as np
from bots import BaseBot
from api.logging import logger
from api.actions import Idle, Move, Push
from util.settings import Settings
from util.hexagon import Hex
from util.pathfinding import a_star


DEBUG_LEVEL = Settings.get('logging.bots.ninja.debug_level', 1)


class NinjaBotV002(BaseBot):
    NAME = 'ninja.002'
    COLOR_INDEX = 10
    map_center = Hex(0, 0)

    def setup(self, wi):
        self.__last_step_round = -1
        self.turn_step = 0

    def update(self, wi):
        if self.__last_step_round < 0:
            self.setup(wi)
        if self.__last_step_round < wi.round_count:
            self.turn_step = 0
        else:
            self.turn_step += 1
        self.__last_step_round = wi.round_count
        self.wi = wi
        self.ring_of_death = wi.ring_radius
        self.round_count = wi.round_count
        self.turn_count = wi.turn_count
        self.positions = wi.positions
        self.pos_set = set(wi.positions)
        self.pos = wi.positions[self.id]
        self.ap = wi.ap[self.id]
        self.walls = wi.walls
        self.pits = wi.pits
        enemy_mask = np.ones(len(wi.positions), dtype=np.bool)
        enemy_mask[self.id] = False
        enemy_mask[~wi.alive_mask] = False
        self.enemy_ids = np.flatnonzero(enemy_mask)
        self.live_enemy_pos = set(wi.positions[uid] for uid in self.enemy_ids)
        self.live_pos = self.live_enemy_pos | {self.pos}
        self.other_pos = self.pos_set - {self.pos}
        self.non_move_options = self.walls | self.pits | self.other_pos
        self.tile_values = {}
        self.my_tile_value = self.move_tile_value(self.pos)

    def log_status(self):
        self.logger('\n'.join([
            f'=== STATUS ===',
            f'My AP: {self.ap:.1f} ; Turn step: {self.turn_step} ; Ring radius: {self.ring_of_death}',
            f'My position: {self.pos} (value: {self.my_tile_value:.3f})',
            '_'*30,
        ]))

    def get_action(self, wi):
        self.update(wi)
        self.log_status()
        action = self.get_best_action()
        self.logger(
            '_'*30+f'\n{self} : {self.ap} AP @ {self.round_count} / {self.turn_count} / {self.turn_step}',
            level=2)
        self.logger('_'*30)
        return action

    def get_best_action(self):
        if self.ap == 0:
            self.logger(f'Out of AP, staying put.')
            return Idle()
        # Defend center
        if self.pos is self.map_center:
            self.logger(f'Defending center.')
            return self.get_best_defence(self.pos)

        # Avoid RoD if necessary
        on_edge = self.pos.get_distance(self.map_center) == self.ring_of_death - 1
        if on_edge:
            self.logger(f'On edge of map...')
        if on_edge and self.ap <= 30:
            best_neighbor = sorted(self.pos.neighbors, key=lambda n: self.move_tile_value(n))[-1]
            self.logger(f'Too close to edge, moving away to: {best_neighbor}.')
            return Move(best_neighbor)

        # Try push
        if self.ap >= 30:
            push_tile, push_value = self.get_best_pushes(self.pos)[0]
            if push_value > 0:
                self.logger(f'Found good push: {push_tile} {push_value}')
                return Push(push_tile)
            self.logger(f'No good push options.')
        else:
            self.logger(f'Not enough AP for push.')

        # Try go to center
        path_to_center = self.path_as_close(self.map_center, sort=lambda x: -self.evaulate_path(x))
        if path_to_center:
            path_str = 'Best path:\n'+'\n'.join(f'-> {n.xy} : {self.move_tile_value(n):.3f} move value' for n in path_to_center)
            self.logger(path_str, level=2)
            if self.evaulate_path(path_to_center) > self.my_tile_value:
                self.logger(f'Moving as close as possible to center.')
                return Move(path_to_center[0])
            self.logger(f'No good paths toward the center, saving AP.')
        else:
            self.logger(f'No paths toward the center!')


        # Spend AP if useful
        best_neighbor = sorted(self.pos.neighbors, key=lambda n: self.move_tile_value(n))[-1]
        better_value = self.move_tile_value(best_neighbor) > self.my_tile_value
        move_cost = self.move_tile_cost(best_neighbor)
        if move_cost < float('inf'):
            if better_value:
                self.logger(f'Free AP, repositioning: {self.pos} -> {best_neighbor}.')
                return Move(best_neighbor)
            else:
                self.logger(f'No better neighbor tiles to reposition.')

        self.logger(f'Found no good actions, staying put.')
        return Idle()

    def evaulate_path(self, path):
        last_tile_value = self.move_tile_value(path[-1])
        radius_delta_value = path[0].get_distance(self.map_center) - path[-1].get_distance(self.map_center)
        turn_distance_cover = int(self.ap / 10)
        can_reach_this_turn = len(path) <= turn_distance_cover
        if can_reach_this_turn:
            stop_tile_value = last_tile_value
        else:
            stop_tile_value = self.move_tile_value(path[turn_distance_cover-1])
        final_value = (last_tile_value + stop_tile_value*5) / 6

        self.logger(' '.join([
            f'Evaluating path: {path[0].xy} ->',
            f'{path[-1].xy} {stop_tile_value:.3f} {last_tile_value:.3f}',
            f'(covering {turn_distance_cover} / {len(path)} tiles)',
            f'~= {final_value:.3f}',
            ]), level=2)
        return final_value

    def get_best_defence(self, tile):
        if self.ap >= 30:
            nset = set(tile.neighbors)
            enemies = nset & self.pos_set
            if 0 < len(enemies) < 6:
                push_tile, push_value = self.get_best_pushes(self.pos)[0]
                if push_value > 0:
                    self.logger(f'Defending with push.')
                    return Push(push_tile)
            self.logger(f'Defending, nobody worth pushing.')
            return Idle()
        self.logger(f'Defending, not enough AP for push.')
        return Idle()

    def get_best_pushes(self, tile):
        pvs = ((n, self.push_value(tile, n)) for n in tile.neighbors)
        push_options = sorted(pvs, key=lambda pv: -pv[1])
        push_str = '\n'.join(f'- {t} {v}' for t, v in push_options)
        self.logger(f'Push options:\n{push_str}', level=2)
        return push_options

    def move_tile_cost(self, tile):
        is_obstacle = tile in (self.pits | self.walls | self.other_pos)
        obs_cost = float('inf') if is_obstacle else 0
        value_cost = -self.move_tile_value(tile)
        return 1 + obs_cost + value_cost

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

    def move_tile_value(self, tile):
        """Value of me standing on this tile (sum of tile neighbor values)."""
        if tile not in self.tile_values:
            nv = sum(self.move_tile_neighbor_value(tile, n) for n in tile.neighbors) / 6
            nv = abs(nv) ** 0.2 * (-1 if nv < 0 else 1)
            ring_distance = self.ring_of_death - tile.get_distance(self.map_center)
            ring_of_death_cool = (ring_distance-1) / (self.ring_of_death-1) * 2 - 1
            total_value = (nv*4 + ring_of_death_cool) / 5
            if tile in self.pits:
                total_value = -1
            self.logger('; '.join([
                f'Tile move value {str(tile):<16}',
                f'Neighbors: {nv:.3f}',
                f'RoD {ring_of_death_cool:.3f}',
                f'Final = {total_value:.3f}']), level=2)
            self.tile_values[tile] = total_value
            return total_value
        return self.tile_values[tile]

    def move_tile_neighbor_value(self, tile, neighbor):
        """Value of standing next to neighbor (while standing on tile)."""
        threatening = self.push_value(tile, neighbor)
        threatened = self.pushed_value(neighbor, tile)
        v = 0
        v += 0.1 * (neighbor in self.walls)
        v += 0.3 * max(0, threatening)
        v -= 0.3 * (neighbor in self.pits)
        v -= 0.7 * max(0, threatened)
        self.logger(f'- neighbor value {tile} next to {neighbor} : {v:.3f} (push: {threatening} pushed: {threatened})', level=3)
        return v

    def pushed_value(self, tile, neighbor):
        """Value of a push action from tile on neighbor.
        Assume we stand on neighbor, but don't assume an enemy stands on tile."""
        end_tile = next(tile.straight_line(neighbor))
        # Check if push is legal
        no_unit_pushing = tile not in self.live_enemy_pos
        # When checking for obstacle, we ignore our position (hence `other_pos`)
        # Since we assume we are standing on neighbor
        against_obstacle = end_tile in self.walls | self.other_pos
        if no_unit_pushing or against_obstacle:
            return -1
        # Check if push is lethal
        if end_tile in self.pits:
            return 1
        end_radius = end_tile.get_distance(self.map_center)
        neighbor_radius = neighbor.get_distance(self.map_center)
        tile_radius = tile.get_distance(self.map_center)
        # Check if push results in target further from center
        result_value = 0.5 * (end_radius - neighbor_radius)
        # Check if push clears a tile closer to the center
        clear_value = 0.5 * (tile_radius - neighbor_radius)
        return result_value + clear_value

    def push_value(self, tile, neighbor):
        """Value of a push action from tile on neighbor (assuming we stand on tile)."""
        end_tile = next(tile.straight_line(neighbor))
        # Check if push is legal
        no_unit_to_push = neighbor not in self.live_enemy_pos
        # When checking for obstacle, we ignore our position (hence `other_pos`)
        # since we assume that we are standing on `tile`.
        against_obstacle = end_tile in self.walls | self.other_pos
        if no_unit_to_push or against_obstacle:
            return -1
        # Check if push is lethal
        if end_tile in self.pits:
            return 1
        end_radius = end_tile.get_distance(self.map_center)
        neighbor_radius = neighbor.get_distance(self.map_center)
        tile_radius = tile.get_distance(self.map_center)
        # Check if push results in target further from center
        result_value = 0.5 * (end_radius - neighbor_radius)
        # Check if push clears a tile closer to the center
        clear_value = 0.25 * (tile_radius - neighbor_radius)
        return result_value + clear_value

    def logger(self, text, level=1):
        if DEBUG_LEVEL >= level:
            super().logger(text)

BOT = NinjaBotV002
