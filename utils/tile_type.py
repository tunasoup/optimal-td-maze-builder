from abc import ABC
from typing import Dict, Type

from PyQt5.QtGui import QColor


class TType(ABC):
    name = NotImplemented
    allow_building = NotImplemented     # can place a tower
    is_removable = NotImplemented       # can be converted to a basic tile
    is_traversable = NotImplemented     # enemies can traverse the tile
    qcolor = NotImplemented             # color of the tile on the GUI


class TTypeBasic(TType):
    name = 'basic'
    can_be_build_on = True
    is_removable = False
    is_traversable = True
    qcolor = QColor('#82add5')


class TTypeUnbuildable(TType):
    name = 'unbuildable'
    can_be_build_on = False
    is_removable = False
    is_traversable = True
    qcolor = QColor('#1f2d3a')


class TTypeVoid(TType):
    name = 'void'
    can_be_build_on = False
    is_removable = False
    is_traversable = False
    qcolor = QColor('transparent')


class TTypeSpawn(TType):
    name = 'spawn'
    can_be_build_on = False
    is_removable = False
    is_traversable = True
    qcolor = QColor('#ff0000')


class TTypeExit(TType):
    name = 'exit'
    can_be_build_on = False
    is_removable = False
    is_traversable = True
    qcolor = QColor('green')


class TTypeOccupied(TType):
    name = 'occupied'
    can_be_build_on = False
    is_removable = False  # todo: toggleable?
    is_traversable = False
    qcolor = QColor('#348bab')


class TTypeRoute(TType):
    name = 'route'
    can_be_build_on = True
    is_removable = False
    is_traversable = True
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
