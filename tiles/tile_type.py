from abc import ABC
from typing import Dict, Type

from PyQt5.QtGui import QColor


class TType(ABC):
    name = NotImplemented
    allow_building = NotImplemented     # can place a tower
    is_removable = NotImplemented       # can be converted to a basic tile
    is_traversable = NotImplemented     # enemies can traverse the tile
    is_spawn = NotImplemented
    is_exit = NotImplemented
    qcolor = NotImplemented             # color of the tile on the GUI


class TTypeBasic(TType):
    name = 'basic'
    allow_building = True
    is_removable = False
    is_traversable = True
    is_spawn = False
    is_exit = False
    qcolor = QColor('#82add5')


class TTypeUnbuildable(TType):
    name = 'unbuildable'
    allow_building = False
    is_removable = False
    is_traversable = True
    is_spawn = False
    is_exit = False
    qcolor = QColor('#1f2d3a')


class TTypeVoid(TType):
    name = 'void'
    allow_building = False
    is_removable = False
    is_traversable = False
    is_spawn = False
    is_exit = False
    qcolor = QColor('transparent')


class TTypeSpawn(TType):
    name = 'spawn'
    allow_building = False
    is_removable = False
    is_traversable = True
    is_spawn = True
    is_exit = False
    qcolor = QColor('#ff0000')


class TTypeExit(TType):
    name = 'exit'
    allow_building = False
    is_removable = False
    is_traversable = True
    is_spawn = False
    is_exit = True
    qcolor = QColor('green')


class TTypeOccupied(TType):
    name = 'occupied'
    allow_building = False
    is_removable = False  # todo: toggleable?
    is_traversable = False
    is_spawn = False
    is_exit = False
    qcolor = QColor('#348bab')


class TTypeRoute(TType):
    name = 'route'
    allow_building = True
    is_removable = False
    is_traversable = True
    is_spawn = False
    is_exit = False
    qcolor = QColor('#f7ed23')


TILE_ROTATION: Dict[Type[TType], Type[TType]] = {
    TTypeBasic:         TTypeUnbuildable,
    TTypeUnbuildable:   TTypeVoid,
    TTypeVoid:          TTypeSpawn,
    TTypeSpawn:         TTypeExit,
    TTypeExit:          TTypeOccupied,
    TTypeOccupied:      TTypeBasic,
}

TILE_ROTATION_REVERSE = dict((v, k) for k, v in TILE_ROTATION.items())
