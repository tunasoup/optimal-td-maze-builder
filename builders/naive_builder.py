from itertools import combinations
from typing import Dict, List, Tuple, Optional

from builders import MazeBuilder
from tiles.tile import Coords
from tiles.tile_type import TTypeExit, TTypeOccupied, TTypeBasic
from utils.graph_algorithms import Node, Distances, \
    get_distances, reset_nodes


class NaiveBuilder(MazeBuilder):
    def __init__(self, coordinated_nodes: Dict[Coords, Node], tower_limit: Optional[int] = None):
        """
        Finds the optimal maze by testing every single maze combination.

        Args:
            coordinated_nodes: the (Coords and) Nodes of the maze
            tower_limit: maximum number of towers allowed in the maze
        """
        super().__init__(coordinated_nodes, tower_limit)

    def generate_optimal_mazes(self) -> List[List[Coords]]:
        """
        Generate a maze where the shortest path is as long as possible by
        testing every combination.

        Returns:
            a list of dictionaries with possibly modified traversable Nodes as values
        """
        # Go through all the possible tower counts to obtain the longest maze
        best_dists = None
        counter = 0
        from time import perf_counter
        while counter <= self.max_towers:
            print(f'Testing combinations with {counter} towers')
            start_time = perf_counter()
            dists, best_tower_coords = self.get_best_tower_combinations(counter)
            end_time = perf_counter()
            print(f'{end_time - start_time:.2f} seconds\n')

            if not dists:
                counter += 1
                continue

            if not best_dists or dists > best_dists:
                best_dists = dists
                self.best_tower_coords = best_tower_coords
            elif dists == best_dists:
                self.best_tower_coords += best_tower_coords

            counter += 1

        return self.best_tower_coords

    def get_best_tower_combinations(self, tower_count: int) -> (Optional[Distances], List[List[Coords]]):
        """
        For every possible tower combination with the given tower amount,
        calculate the spawn-exit Distances, and return the modified Nodes.

        Args:
            tower_count: number of towers/walls in the maze

        Returns:
            longest Distances of the modified map and their Nodes
        """
        best_dists = None
        best_tower_coords = []
        current_nodes = list(self.coordinated_traversables.values())

        combs = combinations(self.coordinated_build_nodes, tower_count)
        for combination in combs:
            reset_nodes(current_nodes)
            dists = self.calculate_maze_distances(self.spawn_nodes, self.coordinated_traversables, combination)
            self.revert_to_buildables(self.coordinated_traversables, combination)
            if not dists:
                continue

            if not best_dists or dists > best_dists:
                best_dists = dists
                best_tower_coords = [list(combination)]
            elif dists == best_dists:
                best_tower_coords.append(list(combination))

        return best_dists, best_tower_coords

    def calculate_maze_distances(self, spawn_nodes: List[Node],
                                 current_nodes: Dict[Coords, Node],
                                 combination: Tuple[Coords]) -> Optional[Distances]:
        """
        Mark the given coordinates as towers/walls, and get the distance
        between spawns and any exit Nodes.

        Args:
            spawn_nodes: a list of spawn coordinate_nodes
            current_nodes: a dictionary of all the Nodes currently in the graph
            combination: a tuple of Coords which mark the towers

        Returns:
            Distances object with the distances between spawns and their closest exit
        """
        for coords in combination:
            node = current_nodes[coords]
            node.ttype = TTypeOccupied

        dists = get_distances(spawn_nodes, TTypeExit, list(current_nodes.values()))

        return dists

    def revert_to_buildables(self, current_nodes: Dict[Coords, Node],
                             combination: Tuple[Coords]) -> None:
        """
        Mark the given coordinates as buildables.

        Meant to undo the effects of calculate_maze_distances().

        Args:
            current_nodes: a dictionary of all the Nodes currently in the graph
            combination: a tuple of Coords which mark the coordinate_nodes
        """
        for coords in combination:
            node = current_nodes[coords]
            node.ttype = TTypeBasic
