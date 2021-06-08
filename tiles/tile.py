from typing import NamedTuple, Type

from tiles.tile_type import TType, TTypeBasic


class Coords(NamedTuple):
    x: int
    y: int


class Tile:
    def __init__(self, x, y, ttype: Type[TType] = TTypeBasic):
        """
        A square tile which is a component of a map.

        Args:
            x: location on the x-axis
            y: location on the y-axis
            ttype: type of the tile
        """
        self.x = x
        self.y = y
        self.coords = Coords(self.x, self.y)
        self.ttype = ttype
