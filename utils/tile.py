from typing import NamedTuple


class Coords(NamedTuple):
    x: int
    y: int


class Tile:
    def __init__(self, x, y, tile_type: str = 'basic'):
        """
        A square tile which is a component of a map.

        Args:
            x: location on the x-axis
            y: location on the y-axis
            tile_type: type of the tile
        """
        self.x = x
        self.y = y
        self.coords = Coords(self.x, self.y)
        self.tile_type = tile_type
