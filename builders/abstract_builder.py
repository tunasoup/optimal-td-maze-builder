from abc import ABC
from typing import Dict, List, Optional

import numpy as np

from tiles.tile import Coords
from tiles.tile_type import TTypeSpawn, TTypeExit
from utils.graph_algorithms import tiles_to_nodes, \
    connect_all_neighboring_nodes, Node, get_maxmin_distance


class MazeBuilder(ABC):
    def __init__(self, tiles: np.ndarray, neighbor_count: int, tower_limit: int = None):
        """
        An abstract maze builder class. The maze builders try to build the
        optimal maze (long routes, minimal resources) for a given map.

        Args:
            tiles: an array of Tiles
            neighbor_count: the number of neighbors a Node can have
            tower_limit: maximum number of towers allowed in the maze
        """
        self.traversables = tiles_to_nodes(tiles[[tile.ttype.is_traversable for tile in tiles]])
        self.build_nodes = {k: v for k, v in self.traversables.items() if
                            v.ttype.allow_building}
        self.spawn_coords = [k for k, v in self.traversables.items() if
                             v.ttype == TTypeSpawn]
        self.exit_coords = [k for k, v in self.traversables.items() if
                            v.ttype == TTypeExit]
        connect_all_neighboring_nodes(self.traversables, neighbor_count)

        self.removed = 0
        self.clear_single_paths()

        self.max_towers = None
        self.calculate_max_towers(tower_limit)

        self.best_setups = []

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

    def calculate_max_towers(self, tower_limit: Optional[int]) -> None:
        """
        Calculate the maximum number of towers for the map and save that or
        the given limit to a class variable. The smaller number is saved.

        Args:
            tower_limit: optional tower limitation
        """
        # Find the maxmin distance to determine the possible amount of towers
        spawn_nodes = [self.traversables[k] for k in self.spawn_coords]
        maxmin_dist = get_maxmin_distance(spawn_nodes,
                                          TTypeExit,
                                          list(self.traversables.values()))
        build_count = len(self.build_nodes)
        possible_tower_count = build_count - (maxmin_dist - 1 - self.removed)
        # todo: what if more than 1 exit, what of when unbuildables

        # Set the largest amount of towers
        if tower_limit and tower_limit <= possible_tower_count:
            self.max_towers = tower_limit
        else:
            self.max_towers = possible_tower_count

    def generate_optimal_mazes(self) -> List[Dict[Coords, Node]]:
        """
        Generate a maze where the shortest route is as long as possible.

        Returns:
            a list of dictionaries with possibly modified traversable Nodes as values
        """
        raise NotImplementedError
