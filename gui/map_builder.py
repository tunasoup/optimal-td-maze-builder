from typing import Dict, Type

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QColor, QMouseEvent
from PyQt5.QtWidgets import QWidget, QMainWindow, QGridLayout, QFormLayout, \
    QLabel, QPushButton, QSpinBox

from utils.errors import ValidationError
from utils.tile import Tile
from utils.map_validation import MapValidator

DEFAULT_SIZE = 6
MINIMUM_SIZE = 2

# todo: place these dicts somewhere else
tile_colors: Dict[str, QColor] = {
    'basic': QColor('#82add5'),
    'unbuildable': QColor('#1f2d3a'),
    'void': QColor('transparent'),
    'spawn': QColor('#ff0000'),
    'exit': QColor('green'),
    'tower': QColor('#348bab'),
    'route': QColor('#b5cfe8'),
}

tile_rotation: Dict[str, str] = {
    'basic': 'unbuildable',
    'unbuildable':  'void',
    'void': 'spawn',
    'spawn': 'exit',
    'exit': 'tower',
    'tower': 'basic',
}


class TileWidget(QWidget):
    def __init__(self, tile: Tile):
        super(TileWidget, self).__init__()

        self.tile = tile

        self.setAutoFillBackground(True)
        self.set_type_color(self.tile.tile_type)

    def rotate_type(self) -> None:
        """
        Change the type of the Tile to the next in rotation
        """
        self.tile.tile_type = tile_rotation[self.tile.tile_type]
        self.set_type_color(self.tile.tile_type)

    def change_to_type(self, tile_type: str) -> None:
        """
        Change the type of the Tile to the given type

        Args:
            tile_type: a string of the new tile type

        """
        self.tile.tile_type = tile_type
        self.set_type_color(tile_type)

    def set_type_color(self, tile_type: str) -> None:
        """
        Set the TileWidget's color to correspond with the given type

        Args:
            tile_type: string of a tile type
        """
        palette = self.palette()
        palette.setColor(QPalette.Window, tile_colors[tile_type])
        self.setPalette(palette)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.rotate_type()


class Window(QMainWindow):
    def __init__(self, map_validator: MapValidator):
        super().__init__()

        self.map_validator = map_validator

        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("TD maze builder")

        main_layout = QGridLayout()

        # Layout for the map
        grid_widget = QWidget()
        self.map_grid = QGridLayout()
        self.map_grid.setSpacing(1)
        grid_widget.setLayout(self.map_grid)
        main_layout.addWidget(grid_widget, 0, 0, -1, 3)

        # Layout for the parameters
        info_widget = QWidget()
        self.info_layout = QFormLayout()
        self.info_layout.setSpacing(20)

        # Spin boxes for determing the map area
        self.width_box = QSpinBox()
        self.height_box = QSpinBox()
        for sb in [self.width_box, self.height_box]:
            sb.setMinimum(MINIMUM_SIZE)
            sb.setValue(DEFAULT_SIZE)
        self.info_layout.addRow(QLabel('W:'), self.width_box)
        self.info_layout.addRow(QLabel('H:'), self.height_box)

        self.build_button = QPushButton('Build')
        self.build_button.clicked.connect(self.build_button_clicked)
        self.info_layout.addRow(self.build_button)

        self.run_button = QPushButton('Run')
        self.run_button.clicked.connect(self.run_button_clicked)
        self.info_layout.addRow(self.run_button)

        info_widget.setLayout(self.info_layout)
        main_layout.addWidget(info_widget, 0, 3)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.tilews = np.empty((DEFAULT_SIZE, DEFAULT_SIZE), TileWidget)

    def build(self) -> None:
        """
        Build a square area with TileWidgets.
        """
        self.clear_map()

        width = self.width_box.value()
        height = self.height_box.value()
        self.tilews = np.empty((width, height), TileWidget)

        counter = 0
        for x in range(width):
            for y in range(height):
                tile = Tile(x=x, y=y)
                tilew = TileWidget(tile)
                self.map_grid.addWidget(tilew, y, x)
                self.tilews[x, y] = tilew
                counter += 1

    def clear_map(self) -> None:
        """
        Clear the TileWidgets from the map grid.
        """
        # No clearing needed on the first run
        if not self.tilews.all():
            return

        for tilew in self.tilews.flatten():
            self.map_grid.removeWidget(tilew)

    def get_tiles(self) -> np.ndarray:
        tiles = np.empty(np.size(self.tilews), Tile)
        for i, tilew in enumerate(self.tilews.flatten()):
            tiles[i] = tilew.tile
        return tiles

    def build_button_clicked(self) -> None:
        self.build()

    def run_button_clicked(self) -> None:
        print('\nValidating map ...')
        try:
            self.map_validator.validate_map(self.get_tiles())
            print(f'Map validation successful!')
        except ValidationError as e:
            print(f'Map validation failed: {e.message}!')
