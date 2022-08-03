from queue import Queue

from api.actions import Idle, Move, Push
from util.hexagon import Hex

from bots import BaseBot


class SurvivorBot(BaseBot):

    NAME = 'survivor'
    COLOR_INDEX = 11
    map_center = Hex(0, 0)
    logging_enabled = True


    def can_tile_be_used_for_push(self, tile):
        return self.is_tile_empty(tile) or tile in self.state.pits


    def is_tile_empty(self, tile):
        return tile not in self.state.positions and \
                tile not in self.state.walls and \
                tile not in self.state.pits


    def poll_action(self, state):
        
        self.state = state
        current_pos = state.positions[self.id]
        ap = self.state.ap[self.id]
        
        # Check if we're in the center of the map
        if current_pos == self.map_center:

            # Let's push anyone next to us away from the center
            if ap >= Push.ap:
                for neighbor in current_pos.neighbors:
                    two_step_line = current_pos.straight_line(neighbor, max_distance=2)
                    behind_neighbor = next(two_step_line)
                    if neighbor in state.positions and self.can_tile_be_used_for_push(behind_neighbor):
                        return Push(neighbor)

            # If nobody is around, stay put
            return Idle()

        # If next to center and someone is there, kick him the fuck out
        if ap >= Push.ap:
            for neighbor in current_pos.neighbors:
                if neighbor == self.map_center and neighbor in state.positions:
                    two_step_line = current_pos.straight_line(neighbor, max_distance=2)
                    behind_neighbor = next(two_step_line)
                    if self.can_tile_be_used_for_push(behind_neighbor):
                        return Push(neighbor)


        # Check if we can move towards the center
        if ap > Move.ap:
            # Find shortest path to center
            path = self.get_shortest_path(current_pos)
            if not len(path):
                return Idle()
            return Move(path.pop(0))

        # Just sit and twiddle our thumbs
        return Idle()


    def get_shortest_path(self, root, goal=map_center):

        root_tuple = (root, None)

        # Initialize set of explored nodes
        explored = set()
        explored.add(root)

        # Initialize queue of nodes to explore
        frontier = Queue()
        frontier.put(root_tuple)

        # Search as long as queue is not empty, until goal is found
        distance = 0
        num_of_next_step_tiles = 1
        while not frontier.empty():
            tiles_at_next_step = []
            for i in range(num_of_next_step_tiles):
                current_node_tuple = frontier.get()
                for neighbor in current_node_tuple[0].neighbors:
                    if neighbor == goal:
                        path = []
                        while current_node_tuple[1] is not None:
                            path.append(current_node_tuple[0])
                            current_node_tuple = current_node_tuple[1]
                        path.reverse()
                        if self.is_tile_empty(neighbor):
                            path.append(neighbor)
                        return path
                    neighbor_tuple = (neighbor, current_node_tuple)
                    if neighbor_tuple[0] not in explored:
                        explored.add(neighbor_tuple[0])
                        if self.is_tile_empty(neighbor_tuple[0]):
                            tiles_at_next_step.append(neighbor_tuple)
            num_of_next_step_tiles = len(tiles_at_next_step)
            for tile_tuple in tiles_at_next_step:
                frontier.put(tile_tuple)
            distance += 1
        
        # In case for some reason algorithm fails
        self.logger('wtf******************')
        return []


BOT = SurvivorBot
