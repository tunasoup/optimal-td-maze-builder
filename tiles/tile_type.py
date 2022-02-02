from abc import ABC


class TType(ABC):
    name = NotImplemented
    allow_building = NotImplemented     # can place a tower
    is_removable = NotImplemented       # can be converted to a basic tile
    is_traversable = NotImplemented     # enemies can traverse the tile
    is_spawn = NotImplemented
    is_exit = NotImplemented
    color = NotImplemented              # color of the tile on the GUI


class TTypeBasic(TType):
    name = 'basic'
    allow_building = True
    is_removable = False
    is_traversable = True
    is_spawn = False
    is_exit = False
    color = '#a16b55'


class TTypeUnbuildable(TType):
    name = 'unbuildable'
    allow_building = False
    is_removable = False
    is_traversable = True
    is_spawn = False
    is_exit = False
    color = '#6e3b27'


class TTypeVoid(TType):
    name = 'void'
    allow_building = False
    is_removable = False
    is_traversable = False
    is_spawn = False
    is_exit = False
    color = 'transparent'


class TTypeSpawn(TType):
    name = 'spawn'
    allow_building = False
    is_removable = False
    is_traversable = True
    is_spawn = True
    is_exit = False
    color = '#ff0000'


class TTypeExit(TType):
    name = 'exit'
    allow_building = False
    is_removable = False
    is_traversable = True
    is_spawn = False
    is_exit = True
    color = '#00ff00'


class TTypeOccupied(TType):
    name = 'occupied'
    allow_building = False
    is_removable = False  # todo: toggleable?
    is_traversable = False
    is_spawn = False
    is_exit = False
    color = '#6e1fa6'


class TTypePath(TType):
    name = 'path'
    allow_building = True
    is_removable = False
    is_traversable = True
    is_spawn = False
    is_exit = False
    color = '#f7ed23'


TTYPES = {
    'basic': TTypeBasic,
    'unbuildable': TTypeUnbuildable,
    'void': TTypeVoid,
    'spawn': TTypeSpawn,
    'exit': TTypeExit,
    'occupied': TTypeOccupied,
    'path': TTypePath,
}
