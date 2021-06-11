from abc import ABC
from copy import deepcopy
from itertools import combinations
from math import factorial
from typing import Dict, List, Type, Tuple

import numpy as np

from tiles.tile import Tile, Coords
from tiles.tile_type import TType, TTypeSpawn, TTypeExit, TTypeOccupied
from utils.graph_algorithms import tiles_to_nodes, Node, \
    get_shortest_distance_any, connect_all_neighboring_nodes, reset_nodes


class MazeBuilder(ABC):
    def generate_optimal_maze(self) -> Dict[Coords, Node]:
        raise NotImplementedError


class NaiveBuilder(MazeBuilder):
    def __init__(self, tiles: np.ndarray, max_towers: int = None):
        self.traversables = tiles_to_nodes(tiles[[tile.ttype.is_traversable for tile in tiles]])
        self.build_nodes = {k: v for k, v in self.traversables.items() if v.ttype.allow_building}
        self.spawn_nodes = {k: v for k, v in self.traversables.items() if v.ttype == TTypeSpawn}
        connect_all_neighboring_nodes(self.traversables)

        self.max_towers = max_towers
        self.best_setup = None

    def generate_optimal_maze(self) -> Dict[Coords, Node]:
        """
        Generate a maze where the shortest route is as long as possible.

        Returns:
            a dictionary with possibly modified traversable Nodes as values
        """
        # Find the maxmin distance to determine the possible amount of towers
        maxmin_dist = get_maxmin_distance(list(self.spawn_nodes.values()),
                                          TTypeExit, len(self.traversables))
        reset_nodes(self.traversables)
        possible_tower_count = len(self.build_nodes) - (maxmin_dist - 1)
        # todo: what if more than 1 exit

        # Set the largest amount of towers
        if self.max_towers and self.max_towers <= possible_tower_count:
            counter = self.max_towers
        else:
            counter = possible_tower_count

        # Go through all the possible tower counts to obtain the longest maze
        best_dist = None
        while counter >= 0:
            dist, best_setup = self.get_best_tower_combination(counter)
            if not best_dist or (dist and dist >= best_dist):
                best_dist = dist
                self.best_setup = deepcopy(best_setup)
            print(f'Tower count {counter} done')
            counter -= 1

        return self.best_setup

    def get_best_tower_combination(self, tower_count: int) -> (int, Dict[Coords, Node]):
        """
        For every possible tower combination with the given tower amount,
        calculate the maxmin distance, and return the modified Nodes.

        Args:
            tower_count: number of towers/walls in the maze

        Returns:
            the maxmin distance of the modified map and its Nodes
        """
        best_dist = None
        best_setup = None

        combs = combinations(self.build_nodes, tower_count)
        for combination in combs:
            current_nodes = deepcopy(self.traversables)
            current_build_nodes = {k: v for k, v in current_nodes.items() if
                                   v.ttype.allow_building}
            current_spawn_nodes = {k: v for k, v in current_nodes.items() if
                                   v.ttype == TTypeSpawn}
            dist = self.generate_maze(current_spawn_nodes, current_build_nodes, combination)
            if not best_dist or (dist and dist > best_dist):
                best_dist = dist
                best_setup = deepcopy(current_nodes)

        return best_dist, best_setup

    def generate_maze(self, spawn_nodes: Dict[Coords, Node],
                      current_build_nodes: Dict[Coords, Node],
                      combination: Tuple[Coords, Coords, Coords]) -> int:
        """
        Mark the given coordinates as towers/walls, and calculate the maxmin
        distance of the map.

        Args:
            spawn_nodes:
            current_build_nodes:
            combination:

        Returns:
            the maxmin distance of the modified map
        """
        for coords in combination:
            node = current_build_nodes[coords]
            node.ttype = TTypeOccupied
            node.remove_all_undirected()

        dist = get_maxmin_distance(list(spawn_nodes.values()), TTypeExit,
                                   len(self.traversables))

        return dist


def number_of_combinations(subset: int, population: int) -> int:
    c = factorial(population) / (factorial(subset)*factorial(population - subset))
    return int(c)


def number_of_all_combinations(population: int) -> int:
    combinations_count = 0
    subset = population
    while subset >= 0:
        combinations_count += number_of_combinations(subset, population)
        subset -= 1

    return combinations_count


def get_maxmin_distance(l_spawn_nodes: List[Node], ending_type: Type[TType],
                        node_count: int) -> int:
    """
    Calculate and return the maxmin distance of a map. The value returned
    is the greatest shortest distance between different spawn nodes.

    Args:
        l_spawn_nodes:
        ending_type:
        node_count:

    Returns:
        the maxmin distance of a map
    """
    maxmin_distance = None
    for spawn_node in l_spawn_nodes:
        dist = get_shortest_distance_any(spawn_node, ending_type,
                                         node_count)
        if not maxmin_distance or (dist and dist > maxmin_distance):
            maxmin_distance = dist

    return maxmin_distance
