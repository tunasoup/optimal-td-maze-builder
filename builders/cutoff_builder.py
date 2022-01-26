from time import perf_counter
from typing import Dict, List, Set

import numpy as np

from builders import MazeBuilder
from tiles.tile import Coords
from tiles.tile_type import TTypeExit, TTypeOccupied, TTypeBasic
from utils.graph_algorithms import get_nodes_on_shortest_paths_multiple


class CutoffBuilder(MazeBuilder):
    def __init__(self, tiles: np.ndarray, neighbor_count: int, tower_limit: int = None):
        """
        Finds the optimal maze by recursively blocking the shortest route.

        Args:
            tiles: an array of Tiles
            neighbor_count: the number of neighbors a Node can have
            tower_limit: maximum number of towers allowed in the maze
        """
        super().__init__(tiles, neighbor_count, tower_limit)
        self.spawn_nodes = [self.traversables[coords] for coords in self.spawn_coords]
        self.best_dists = None
        self.processed_coordinates: Dict[int, Set[Coords]] = dict()
        self.combination_counter = 0
        self.first_node_counter = 0
        self.first_nodes = 0
        self.start_time = None

    def generate_optimal_mazes(self) -> List[List[Coords]]:
        """
        Generate a maze where the shortest route is as long as possible by
        always blocking the shortest route.

        Returns:
            a list of lists with coordinates for the optimal tower placements
        """
        self.start_time = perf_counter()
        for count in range(self.max_towers, 0, -1):
            self.processed_coordinates[count] = set()

        self.cut_off_route([], self.max_towers)
        print(f'Number of combinations checked: {self.combination_counter}')

        return self.best_tower_coords

    def cut_off_route(self, combination: List[Coords], towers_left: int) -> None:
        """
        Obtains all the Nodes on the shortest possible paths,
        and recursively for each of those builds a tower on them.
        All the checked combinations only include towers on the possible
        shortest paths.

        Args:
            combination: a list of Coords with current tower placements
            towers_left: the number of towers left to build
        """
        # Find all the shortest paths and dist
        dists, nodes = get_nodes_on_shortest_paths_multiple(self.spawn_nodes, TTypeExit,
                                                            list(self.traversables.values()))
        self.combination_counter += 1

        # On the first run of this function, count the number of nodes (first nodes)
        if towers_left == self.max_towers:
            buildable_first_nodes = [node for node in nodes if node.ttype.allow_building]
            self.first_nodes = len(buildable_first_nodes)

        # Unsolvable
        if not dists:
            if towers_left > 0:
                self.processed_coordinates[towers_left].add(combination[-1])
            return

        # Save good results
        if not self.best_dists or dists > self.best_dists:
            self.best_dists = dists
            self.best_tower_coords = [list(combination)]
        elif dists == self.best_dists:
            self.best_tower_coords.append(list(combination))

        # Cannot insert more towers to the combination
        if towers_left == 0:
            return

        # Remove processed coordinates to avoid duplicate combinations
        for count in range(self.max_towers, towers_left, -1):
            nodes = nodes - self.processed_coordinates[count]

        # Loop every found buildable node
        for node in nodes:
            if not node.ttype.allow_building:
                continue

            node.ttype = TTypeOccupied  # place tower on node
            self.cut_off_route(combination + [node.coords], towers_left - 1)
            node.ttype = TTypeBasic

            # Add coordinate as processed, mark deeper processed coordinates as unprocessed
            self.processed_coordinates[towers_left].add(node.coords)
            if towers_left > 1:
                self.processed_coordinates[towers_left-1].clear()

            # Verbose
            if towers_left == self.max_towers:  # Depth 0
                self.first_node_counter += 1
                end_time = perf_counter()
                print(f'Time spent {end_time - self.start_time:.2f} seconds'
                      f', first nodes processed {self.first_node_counter}/{self.first_nodes}\n ')
