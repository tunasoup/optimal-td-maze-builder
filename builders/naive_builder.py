from copy import deepcopy
from itertools import combinations
from typing import Dict, List, Tuple, Optional

import numpy as np

from builders import MazeBuilder
from tiles.tile import Coords
from tiles.tile_type import TTypeExit, TTypeOccupied
from utils.graph_algorithms import Node, get_maxmin_distance, Distances, \
    get_distances, reset_nodes, unvisit_nodes


class NaiveBuilder(MazeBuilder):
    def __init__(self, tiles: np.ndarray, neighbor_count: int, tower_limit: int = None):
        """
        Finds the optimal maze by testing every single maze combination.

        Args:
            tiles: an array of Tiles
            tower_limit: maximum number of towers allowed in the maze
        """
        super().__init__(tiles, neighbor_count, tower_limit)

    def generate_optimal_mazes(self) -> List[Dict[Coords, Node]]:
        """
        Generate a maze where the shortest route is as long as possible by
        testing every combination.

        Returns:
            a list of dictionaries with possibly modified traversable Nodes as values
        """
        # Go through all the possible tower counts to obtain the longest maze
        best_dists = None
        counter = self.max_towers
        while counter >= 0:
            print(f'Testing combinations with {counter} towers')
            dists, best_setups = self.get_best_tower_combinations(counter)
            if not dists:
                counter -= 1
                continue

            if not best_dists or dists > best_dists:
                best_dists = dists
                self.best_setups = best_setups
            elif dists == best_dists:
                self.best_setups += best_setups

            counter -= 1

        return self.best_setups

    def get_best_tower_combinations(self, tower_count: int) -> (Optional[Distances], List[Dict[Coords, Node]]):
        """
        For every possible tower combination with the given tower amount,
        calculate the spawn-exit Distances, and return the modified Nodes.

        Args:
            tower_count: number of towers/walls in the maze

        Returns:
            longest Distances of the modified map and their Nodes
        """
        best_dists = None
        best_setups = []
        unvisit_nodes(list(self.traversables.values()))

        combs = combinations(self.build_nodes, tower_count)
        for combination in combs:
            current_nodes = deepcopy(self.traversables)
            current_spawn_nodes = [current_nodes[k] for k in self.spawn_coords]
            dists = self.calculate_maze_distances(current_spawn_nodes, current_nodes, combination)
            if not dists:
                continue

            if not best_dists or dists > best_dists:
                best_dists = dists
                best_setups = [deepcopy(current_nodes)]
            elif dists == best_dists:
                best_setups.append(deepcopy(current_nodes))

        return best_dists, best_setups

    def calculate_maze_distances(self, spawn_nodes: List[Node],
                                 current_nodes: Dict[Coords, Node],
                                 combination: Tuple[Coords]) -> Optional[Distances]:
        """
        Mark the given coordinates as towers/walls, and get the distance
        between spawns and any exit Nodes.

        Args:
            spawn_nodes: a list of spawn nodes
            current_nodes: a dictionary of all the Nodes currently in the graph
            combination: a tuple of Coords which mark the towers

        Returns:
            Distances object with the distances between spawns and their closest exit
        """
        for coords in combination:
            node = current_nodes[coords]
            node.ttype = TTypeOccupied
            node.remove_all_undirected()

        dists = get_distances(spawn_nodes, TTypeExit, list(current_nodes.values()))

        return dists
