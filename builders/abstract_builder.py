from abc import ABC
from typing import Dict

import numpy as np

from tiles.tile import Coords
from tiles.tile_type import TTypeSpawn, TTypeExit
from utils.graph_algorithms import tiles_to_nodes, \
    connect_all_neighboring_nodes, Node


class MazeBuilder(ABC):
    def __init__(self, tiles: np.ndarray, max_towers: int = None):
        """
        An abstract maze builder class. The maze builders try to build the
        optimal maze (long routes, minimal resources) for a given map.

        Args:
            tiles: an array of Tiles
            max_towers: maximum number of towers allowed in the maze
        """
        self.traversables = tiles_to_nodes(tiles[[tile.ttype.is_traversable for tile in tiles]])
        self.build_nodes = {k: v for k, v in self.traversables.items() if
                            v.ttype.allow_building}
        self.spawn_coords = [k for k, v in self.traversables.items() if
                             v.ttype == TTypeSpawn]
        self.exit_coords = [k for k, v in self.traversables.items() if
                            v.ttype == TTypeExit]
        connect_all_neighboring_nodes(self.traversables)

        self.removed = 0
        self.clear_single_paths()

        self.max_towers = max_towers
        self.best_setup = None

    def clear_single_paths(self) -> None:
        """
        Remove a traversable path from the list of build nodes, if it is the
        only path that can be taken.
        This reduces the number of combinations by ignoring
        unsolvable mazes.
        """
        spawn_nodes = [self.traversables[k] for k in self.spawn_coords]
        exit_nodes = [self.traversables[k] for k in self.exit_coords]

        for node in spawn_nodes + exit_nodes:
            neighbors = node.neighbors
            if len(neighbors) != 1:
                continue

            node = next(iter(neighbors))    # Get the only neighbor Node
            if node.ttype.is_spawn or node.ttype.is_exit:
                break
            if node.ttype.allow_building:
                del self.build_nodes[node.coords]
                self.removed += 1
            prev_node = node

            while len(prev_node.neighbors) == 2:
                neighbor = None
                for neighbor in list(prev_node.neighbors):
                    if neighbor == prev_node:
                        continue
                    if neighbor.ttype.is_spawn or neighbor.ttype.is_exit:
                        break
                    if neighbor.ttype.allow_building:
                        del self.build_nodes[neighbor.coords]
                        self.removed += 1
                        break

                prev_node = neighbor
                if not neighbor:
                    break

    def generate_optimal_maze(self) -> Dict[Coords, Node]:
        raise NotImplementedError
