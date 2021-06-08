from abc import ABC, abstractmethod
from collections import defaultdict

import numpy as np

from utils.errors import ValidationError
from utils.graph_algorithms import depth_first_search_any_ttype, tiles_to_nodes, \
    connect_all_neighboring_nodes, reset_nodes
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

    def validate_map(self, tiles: np.ndarray):
        """
        Initiate the validation of a built map, whose subfunctions raise an
        error if the map is flawed.

        Args:
            tiles: an array of Tiles
        """
        self.divide_types(tiles)

        self.validate_spawns()
        self.validate_exits()
        self.validate_route()

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
    def validate_route(self) -> None:
        """
        Check that there is a route for the enemies, so that they can
        reach the exit(s).
        """
        raise NotImplementedError()


class MapValidator2D(MapValidator):
    """
    Validates a 2D map where a spawn or an exit cannot be blocked.
    """

    def validate_route(self):
        """
        Raise an error if any spawn or exit is not connected to at least one
        counterpart.
        """
        nodes = tiles_to_nodes(self.traversables)
        connect_all_neighboring_nodes(nodes)

        found_exits = set()
        for coords in [tile.coords for tile in self.spawns]:
            reset_nodes(nodes)
            exit_node = depth_first_search_any_ttype(nodes[coords], TTypeExit)
            if not exit_node:
                raise ValidationError('a spawn is blocked')
            found_exits.add(exit_node.coords)

        # Only validate the exit tiles that were not already found
        exit_coords = [tile.coords for tile in self.exits]
        exit_coords = [coords for coords in exit_coords if coords not in found_exits]

        for coords in exit_coords:
            reset_nodes(nodes)
            spawn_node = depth_first_search_any_ttype(nodes[coords], TTypeSpawn)
            if not spawn_node:
                raise ValidationError('an exit is blocked')
