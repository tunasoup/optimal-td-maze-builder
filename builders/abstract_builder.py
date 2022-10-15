from abc import ABC
from typing import List, Optional, Dict

from tiles.tile import Coords
from tiles.tile_type import TTypeExit
from utils.graph_algorithms import get_maxmin_distance, unvisit_nodes, \
    get_cluster_of_nodes, get_center_coords, get_surrounded_coords, Node


class MazeBuilder(ABC):
    def __init__(self, coordinated_nodes: Dict[Coords, Node], tower_limit: Optional[int] = None):
        """
        An abstract maze builder class. The maze builders try to build the
        optimal maze (the longest possible paths with minimal resources) for a given map.

        Args:
            coordinated_nodes: the (Coords and) Nodes of the maze
            tower_limit: maximum number of towers allowed in the maze
        """
        self.coordinated_traversables = {k: v for k, v in coordinated_nodes.items() if v.ttype.is_traversable}
        self.coordinated_build_nodes = {k: v for k, v in self.coordinated_traversables.items() if
                                        v.ttype.allow_building}
        self.coordinated_unbuildables = {k: v for k, v in self.coordinated_traversables.items() if
                                         not v.ttype.allow_building}
        self.spawn_nodes = [v for k, v in self.coordinated_traversables.items()
                            if v.ttype.is_spawn]
        self.exit_nodes = [v for k, v in self.coordinated_traversables.items()
                           if v.ttype.is_exit]

        self.removed = []
        self.clear_single_paths()

        self.clear_redundant_spawns()

        self.max_towers = 0
        self.calculate_max_towers(tower_limit)

        self.best_tower_coords = []

    def clear_single_paths(self) -> None:
        """
        Remove a traversable path from the list of build coordinate_nodes, if it is the
        only path that can be taken. This reduces the number of combinations by ignoring unsolvable mazes.
        """
        unvisit_nodes(list(self.coordinated_traversables.values()))

        for node in self.spawn_nodes + self.exit_nodes:
            neighbors = node.neighbors
            if len(neighbors) != 1:
                continue
            node.visited = True

            current_node = next(iter(neighbors))  # Get the only neighbor Node
            if current_node.ttype.is_spawn or current_node.ttype.is_exit or current_node.visited:
                continue
            if current_node.ttype.allow_building:
                del self.coordinated_build_nodes[current_node.coords]
                self.removed.append(current_node.coords)
            current_node.visited = True
            prev_node = node

            while len(current_node.neighbors) == 2:
                neighbors = list(current_node.neighbors)
                neighbors.remove(prev_node)
                neighbor = neighbors[0]
                if neighbor.visited:
                    break
                if neighbor.ttype.is_spawn or neighbor.ttype.is_exit:
                    neighbor.visited = True
                    break
                if neighbor.ttype.allow_building:
                    del self.coordinated_build_nodes[neighbor.coords]
                    self.removed.append(neighbor.coords)
                    prev_node = current_node
                    current_node = neighbor
                    current_node.visited = True

    def clear_redundant_spawns(self) -> None:
        """
        Remove reduntant spawn Nodes from the list of spawn coordinate_nodes.
        A spawn is considered redundant if removing it does not change
        the result of the optimal maze. Only spawns in clusters are checked.

        Having fewer spawns reduces the amount of computed graph algorithms.
        """
        if len(self.spawn_nodes) < 2:
            return

        unvisit_nodes(self.spawn_nodes)
        unvisited_spawn_nodes = set(self.spawn_nodes)
        redundant_spawn_coords = set()
        for node in self.spawn_nodes:

            if node not in unvisited_spawn_nodes:
                continue

            cluster = get_cluster_of_nodes(node)
            if len(cluster) < 2:
                continue
            unvisited_spawn_nodes = unvisited_spawn_nodes.difference(cluster)
            center_coords = get_center_coords(cluster)
            redundant_spawn_coords.update(center_coords)
            surrounded_coords = get_surrounded_coords(cluster)
            redundant_spawn_coords.update(surrounded_coords)

        self.spawn_nodes = [node for node in self.spawn_nodes if node.coords not in redundant_spawn_coords]

    def calculate_max_towers(self, tower_limit: Optional[int]) -> None:
        """
        Calculate the maximum number of towers for the map and save that or
        the given limit to a class variable. The smaller number is saved.

        Args:
            tower_limit: optional tower limitation
        """
        # Find the maxmin distance to determine the possible amount of towers
        maxmin_dist = get_maxmin_distance(self.spawn_nodes,
                                          TTypeExit,
                                          list(self.coordinated_traversables.values()))

        build_count = len(self.coordinated_build_nodes)

        # todo: currently only reduces tower count in some cases, more thorough check of
        #  tile types would have to be made on the maxmin_dist path, + possible other checks
        possible_tower_count = build_count - max(maxmin_dist - len(self.removed) - len(self.coordinated_unbuildables) + 1, 0)

        # Set the largest amount of towers
        if (tower_limit or tower_limit == 0) and tower_limit <= possible_tower_count:
            self.max_towers = tower_limit
        else:
            self.max_towers = possible_tower_count

    def generate_optimal_mazes(self) -> List[List[Coords]]:
        """
        Generate a maze where the shortest path is as long as possible.

        Returns:
           a list of lists with Coordinates for the tower placements
        """
        raise NotImplementedError
