from copy import deepcopy
from itertools import combinations
from typing import Dict, List, Tuple, Optional

import numpy as np

from builders import MazeBuilder
from tiles.tile import Coords
from tiles.tile_type import TTypeExit, TTypeOccupied
from utils.graph_algorithms import Node, get_maxmin_distance, Distances, \
    get_distances


class NaiveBuilder(MazeBuilder):
    def __init__(self, tiles: np.ndarray, max_towers: int = None):
        """
        Finds the optimal maze by testing every single maze combination.

        Args:
            tiles: an array of Tiles
            max_towers: maximum number of towers allowed in the maze
        """
        super().__init__(tiles, max_towers)

    def generate_optimal_maze(self) -> Optional[Dict[Coords, Node]]:
        """
        Generate a maze where the shortest route is as long as possible.

        Returns:
            a dictionary with possibly modified traversable Nodes as values
        """
        # Find the maxmin distance to determine the possible amount of towers
        spawn_nodes = [self.traversables[k] for k in self.spawn_coords]
        maxmin_dist = get_maxmin_distance(spawn_nodes,
                                          TTypeExit, list(self.traversables.values()))
        build_count = len(self.build_nodes)
        possible_tower_count = build_count - (maxmin_dist - 1 - self.removed)
        # todo: what if more than 1 exit, what of when unbuildables

        # Set the largest amount of towers
        if self.max_towers and self.max_towers <= possible_tower_count:
            counter = self.max_towers
        else:
            counter = possible_tower_count

        # Go through all the possible tower counts to obtain the longest maze
        best_dists = None
        while counter >= 0:
            dists, best_setup = self.get_best_tower_combination(counter)
            if not best_dists or (dists and dists >= best_dists):
                best_dists = dists
                self.best_setup = deepcopy(best_setup)
            print(f'Tower count {counter} done')
            counter -= 1

        return self.best_setup

    def get_best_tower_combination(self, tower_count: int) -> (Optional[Distances], Optional[Coords]):
        """
        For every possible tower combination with the given tower amount,
        calculate the maxmin distance, and return the modified Nodes.

        Args:
            tower_count: number of towers/walls in the maze

        Returns:
            the maxmin distance of the modified map and its Nodes
        """
        best_dists = None
        best_setup = None

        combs = combinations(self.build_nodes, tower_count)
        for combination in combs:
            current_nodes = deepcopy(self.traversables)
            current_spawn_nodes = [current_nodes[k] for k in self.spawn_coords]
            dists = self.calculate_maze_distances(current_spawn_nodes, current_nodes, combination)
            if not best_dists or (dists and dists > best_dists):
                best_dists = dists
                best_setup = deepcopy(current_nodes)

        return best_dists, best_setup

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