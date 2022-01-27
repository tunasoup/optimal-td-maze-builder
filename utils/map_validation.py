from abc import ABC, abstractmethod

import numpy as np

from tiles.tile_type import TTypeSpawn, TTypeExit
from utils.errors import ValidationError
from utils.graph_algorithms import depth_first_search_any_ttype, \
    reset_nodes, get_cluster_of_nodes


class MapValidator(ABC):
    """
    Makes sure that the given map is playable
    i.e. enemies can reach the exit.
    """

    def __init__(self):
        self.traversables = None
        self.spawns = None
        self.exits = None

    def validate_map(self, nodes: np.ndarray):
        """
        Initiate the validation of a built map, whose subfunctions raise an
        error if the map is flawed.

        Args:
            nodes: an array of Nodes
        """
        self.divide_types(nodes)

        self.validate_spawns()
        self.validate_exits()
        self.validate_path()

    def divide_types(self, nodes: np.ndarray) -> None:
        """
        Divide the coordinated_nodes according to their tile type.

        Args:
            nodes: an array of Nodes
        """
        self.spawns = np.array([node for node in nodes if node.ttype.is_spawn])
        self.exits = np.array([node for node in nodes if node.ttype.is_exit])
        self.traversables = np.array([node for node in nodes if node.ttype.is_traversable])

    def validate_spawns(self) -> None:
        """
        Check that there is at least a single spawn tile.
        """
        if not np.size(self.spawns) > 0:
            raise ValidationError('not enough spawns')

    def validate_exits(self) -> None:
        """
        Check that there is at least a single exit tile.
        """
        if not np.size(self.exits) > 0:
            raise ValidationError('not enough exits')

    @abstractmethod
    def validate_path(self) -> None:
        """
        Check that there is a path for the enemies, so that they can
        reach the exit(s).
        """
        raise NotImplementedError()


class MapValidator2D(MapValidator):
    """
    Validates a 2D map where a spawn or an exit cannot be blocked.
    """

    def validate_path(self):
        """
        Raise an error if any spawn or exit is not connected to at least one
        counterpart.
        """
        # Look for spawn clusters
        current_spawns = set(self.spawns)
        if len(self.spawns) > 1:
            reset_nodes(self.traversables)
            for node in self.spawns:
                if node not in current_spawns:
                    continue
                cluster = get_cluster_of_nodes(node)

                # Only need the first (any) Node of a cluster for validation
                if len(cluster) > 1:
                    cluster = cluster[1:]
                    current_spawns = current_spawns.difference(cluster)

        # Validate a path for all the spawn clusters
        found_exits = set()
        for spawn in current_spawns:
            reset_nodes(self.traversables)
            exit_node = depth_first_search_any_ttype(spawn, TTypeExit)
            if not exit_node:
                raise ValidationError('a spawn is blocked')
            found_exits.add(exit_node)

        # Only validate the exit coordinated_nodes that were not already found
        remaining_exits = {node for node in self.exits if node not in found_exits}
        current_exits = remaining_exits

        # Look for clusters of found exits
        if remaining_exits:
            reset_nodes(self.traversables)
            for node in remaining_exits:
                if node not in current_exits:
                    continue
                cluster = get_cluster_of_nodes(node)

                # Validate all the clusters exits if it contains a found exit
                if len(found_exits.difference(cluster)) < len(found_exits):
                    current_exits = current_exits.difference(cluster)
                    found_exits.update(cluster)

                # Only need the first (any) Node of a cluster for validation
                elif len(cluster) > 1:
                    cluster = cluster[1:]
                    current_exits = current_exits.difference(cluster)

        # Validate a path for the remaining exit clusters
        for exit_node in current_exits:
            reset_nodes(self.traversables)
            spawn_node = depth_first_search_any_ttype(exit_node, TTypeSpawn)
            if not spawn_node:
                raise ValidationError('an exit is blocked')
