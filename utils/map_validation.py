from abc import ABC, abstractmethod
from collections import defaultdict

import numpy as np

from utils.errors import ValidationError
from utils.graph_algorithms import depth_first_search_any_ttype, \
    tiles_to_nodes, \
    connect_all_neighboring_nodes, reset_nodes, get_cluster_of_nodes
from tiles.tile_type import TTypeBasic, TTypeUnbuildable, TTypeSpawn, TTypeExit


class MapValidator(ABC):
    """
    Makes sure that the given map is playable
    i.e. enemies can reach the exit.
    """

    def __init__(self):
        self.tiles = None
        self.traversables = None
        self.spawns = None
        self.exits = None

    def validate_map(self, tiles: np.ndarray, neighbor_count: int):
        """
        Initiate the validation of a built map, whose subfunctions raise an
        error if the map is flawed.

        Args:
            tiles: an array of Tiles
            neighbor_count: the number of neighbors a Node can have
        """
        self.divide_types(tiles)

        self.validate_spawns()
        self.validate_exits()
        self.validate_route(neighbor_count)

    def divide_types(self, tiles: np.ndarray) -> None:
        """
        Divide the tiles according to their tile type.

        Args:
            tiles: an array of Tiles
        """
        ttypes = defaultdict(list)

        for tile in tiles:
            ttypes[tile.ttype.name].append(tile)

        basics = np.array(ttypes[TTypeBasic.name])
        unbuildables = np.array(ttypes[TTypeUnbuildable.name])
        self.spawns = np.array(ttypes[TTypeSpawn.name])
        self.exits = np.array(ttypes[TTypeExit.name])
        self.traversables = np.concatenate((basics, unbuildables, self.spawns,
                                           self.exits))

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
    def validate_route(self, neighbor_count: int) -> None:
        """
        Check that there is a route for the enemies, so that they can
        reach the exit(s).

        Args:
            neighbor_count: the number of neighbors a Node can have
        """
        raise NotImplementedError()


class MapValidator2D(MapValidator):
    """
    Validates a 2D map where a spawn or an exit cannot be blocked.
    """

    def validate_route(self, neighbor_count: int):
        """
        Raise an error if any spawn or exit is not connected to at least one
        counterpart.

        Args:
            neighbor_count: the number of neighbors a Node can have
        """
        nodes = tiles_to_nodes(self.traversables)
        spawn_nodes = [node for node in nodes.values() if node.ttype == TTypeSpawn]
        exit_nodes = [node for node in nodes.values() if node.ttype == TTypeExit]
        connect_all_neighboring_nodes(nodes, neighbor_count)

        # Look for spawn clusters
        current_spawns = set(spawn_nodes)
        if len(self.spawns) > 1:
            reset_nodes(list(nodes.values()))
            for node in spawn_nodes:
                if node not in current_spawns:
                    continue
                cluster = get_cluster_of_nodes(node)

                # Only need the first (any) node of a cluster for validation
                if len(cluster) > 1:
                    cluster = cluster[1:]
                    current_spawns = current_spawns.difference(cluster)

        # Validate a route for all the spawn clusters
        found_exits = set()
        for spawn in current_spawns:
            reset_nodes(list(nodes.values()))
            exit_node = depth_first_search_any_ttype(spawn, TTypeExit)
            if not exit_node:
                raise ValidationError('a spawn is blocked')
            found_exits.add(exit_node)

        # Only validate the exit tiles that were not already found
        remaining_exits = {node for node in exit_nodes if node not in found_exits}
        current_exits = remaining_exits

        # Look for clusters of found exits
        if remaining_exits:
            reset_nodes(list(nodes.values()))
            for node in remaining_exits:
                if node not in current_exits:
                    continue
                cluster = get_cluster_of_nodes(node)

                # Validate all the clusters exits if it contains a found exit
                if len(found_exits.difference(cluster)) < len(found_exits):
                    current_exits = current_exits.difference(cluster)
                    found_exits.update(cluster)

                # Only need the first (any) node of a cluster for validation
                elif len(cluster) > 1:
                    cluster = cluster[1:]
                    current_exits = current_exits.difference(cluster)

        exit_coords = [node.coords for node in current_exits]

        # Validate a route for the remaining exit clusters
        for coords in exit_coords:
            reset_nodes(list(nodes.values()))
            spawn_node = depth_first_search_any_ttype(nodes[coords], TTypeSpawn)
            if not spawn_node:
                raise ValidationError('an exit is blocked')
