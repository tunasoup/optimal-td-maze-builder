import sys
from time import perf_counter
from typing import Dict, List, Set, Optional

from builders import MazeBuilder
from tiles.tile import Coords
from tiles.tile_type import TTypeExit, TTypeOccupied, TTypeBasic
from utils.graph_algorithms import get_nodes_on_shortest_paths_multiple, Node


class CutoffBuilder(MazeBuilder):
    def __init__(self, coordinated_nodes: Dict[Coords, Node], tower_limit: Optional[int] = None):
        """
        Finds the optimal maze by recursively blocking the shortest path.

        Args:
            coordinated_nodes: the (Coords and) Nodes of the maze
            tower_limit: maximum number of towers allowed in the maze
        """
        super().__init__(coordinated_nodes, tower_limit)
        self.best_dists = None
        self.processed_coordinates: Dict[int, Set[Coords]] = dict()
        self.combination_counter = 0
        self.first_node_counter = 0
        self.n_first_nodes = 0
        self.start_time = None

    def generate_optimal_mazes(self) -> List[List[Coords]]:
        """
        Generate a maze where the shortest path is as long as possible by
        always blocking the shortest path.

        Returns:
            a list of lists with coordinates for the optimal tower placements
        """
        self.start_time = perf_counter()
        for count in range(self.max_towers, 0, -1):
            self.processed_coordinates[count] = set()

        self.cut_off_path([], self.max_towers)
        print(f'\nNumber of combinations checked: {self.combination_counter}')

        return self.best_tower_coords

    def cut_off_path(self, combination: List[Coords], towers_left: int) -> None:
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
                                                            list(self.coordinated_traversables.values()))
        self.combination_counter += 1

        # On the first run of this function, count the number of Nodes (first coordinate_nodes)
        if towers_left == self.max_towers:
            buildable_first_nodes = [node for node in nodes if node.ttype.allow_building]
            self.n_first_nodes = len(buildable_first_nodes)

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

            node.ttype = TTypeOccupied  # Place a tower on Node
            self.cut_off_path(combination + [node.coords], towers_left - 1)
            node.ttype = TTypeBasic

            # Add coordinate as processed, mark deeper processed coordinates as unprocessed
            self.processed_coordinates[towers_left].add(node.coords)
            if towers_left > 1:
                self.processed_coordinates[towers_left-1].clear()

            # Verbose
            if towers_left == self.max_towers:  # Depth 0
                self.first_node_counter += 1
                out_print = (f'\rTime spent {perf_counter() - self.start_time:.2f} seconds'
                             f', unique shortest Nodes processed {self.first_node_counter}/{self.n_first_nodes}')
                print(out_print, end='', flush=True, file=sys.stdout)
