import threading
from typing import Type

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QMouseEvent
from PyQt5.QtWidgets import QWidget, QMainWindow, QGridLayout, QFormLayout, \
    QLabel, QPushButton, QSpinBox, QCheckBox, QMenu, QAction, QMenuBar, \
    QActionGroup

from utils.errors import ValidationError
from tiles.tile import Tile
from tiles.tile_type import TType, TILE_ROTATION, TILE_ROTATION_REVERSE
from utils.map_validation import MapValidator
from builders import NaiveBuilder

DEFAULT_SIZE = 6
MINIMUM_SIZE = 2


class TileWidget(QWidget):
    def __init__(self, tile: Tile):
        super(TileWidget, self).__init__()

        self.tile = tile

        self.setAutoFillBackground(True)
        self.set_type_color(self.tile.ttype)

    def rotate_type(self) -> None:
        """
        Change the type of the Tile to the next in rotation
        """
        self.tile.ttype = TILE_ROTATION[self.tile.ttype]
        self.set_type_color(self.tile.ttype)

    def rotate_type_reverse(self) -> None:
        """
        Change the type of the Tile to the previous in rotation
        """
        self.tile.ttype = TILE_ROTATION_REVERSE[self.tile.ttype]
        self.set_type_color(self.tile.ttype)

    def change_to_type(self, ttype: Type[TType]) -> None:
        """
        Change the type of the Tile to the given type

        Args:
            ttype: a new tile type

        """
        self.tile.ttype = ttype
        self.set_type_color(ttype)

    def set_type_color(self, ttype: Type[TType]) -> None:
        """
        Set the TileWidget's color to correspond with the given type

        Args:
            ttype: a tile type whose defined color is to be used
        """
        palette = self.palette()
        palette.setColor(QPalette.Window, ttype.qcolor)
        self.setPalette(palette)

    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.rotate_type()

        elif event.button() == Qt.RightButton:
            self.rotate_type_reverse()


class Window(QMainWindow):
    def __init__(self, map_validator: MapValidator):
        super().__init__()

        self.map_validator = map_validator

        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("TD maze builder")

        self.create_menubar()

        main_layout = QGridLayout()

        # Layout for the map
        grid_widget = QWidget()
        self.map_grid = QGridLayout()
        self.map_grid.setSpacing(1)
        grid_widget.setLayout(self.map_grid)
        main_layout.addWidget(grid_widget, 0, 0, -1, 3)

        # Layout for the parameters
        info_widget = QWidget()
        info_layout = QFormLayout()
        info_layout.setSpacing(20)

        # Spin boxes for determing the map area
        self.width_box = QSpinBox()
        self.height_box = QSpinBox()
        for sb in [self.width_box, self.height_box]:
            sb.setMinimum(MINIMUM_SIZE)
            sb.setValue(DEFAULT_SIZE)
        info_layout.addRow(QLabel('W:'), self.width_box)
        info_layout.addRow(QLabel('H:'), self.height_box)

        # Build button for initiating the map construction
        build_button = QPushButton('Build')
        build_button.clicked.connect(self.build_button_clicked)
        info_layout.addRow(build_button)

        # Optional limit for the number of towers
        self.tower_limiter = QCheckBox()
        self.tower_limiter.clicked.connect(self.tower_limiter_clicked)
        self.max_towers_box = QSpinBox()
        self.max_towers_box.setMinimum(0)
        self.max_towers_box.setDisabled(True)
        info_layout.addRow(QLabel('Limit towers:'), self.tower_limiter)
        info_layout.addRow(QLabel('Tower count:'), self.max_towers_box)

        # Run button for initiating the maze construction
        run_button = QPushButton('Run')
        run_button.clicked.connect(self.run_button_clicked)
        info_layout.addRow(run_button)

        # Spin box for selecting different variations of the best maze
        self.variation_box = QSpinBox()
        self.variation_box.setMinimum(1)
        self.variation_box.setDisabled(True)
        self.variation_box.valueChanged.connect(self.variation_changed)
        self.variation_label = QLabel('Variations (1)')
        info_layout.addRow(self.variation_label, self.variation_box)

        info_widget.setLayout(info_layout)
        main_layout.addWidget(info_widget, 0, 3)

        central_widget = QWidget()
        central_widget.setLayout(main_layout)
        self.setCentralWidget(central_widget)

        self.buttons = [build_button, run_button]

        self.tile_widgets = np.empty((DEFAULT_SIZE, DEFAULT_SIZE), TileWidget)
        self.best_setups = []

    def create_menubar(self) -> None:
        menubar = self.menuBar()
        self.add_maze_menu(menubar)
        self.add_options_menu(menubar)
        self.add_help_menu(menubar)

    def add_maze_menu(self, menubar: QMenuBar) -> None:
        maze_menu = QMenu('Maze', self)
        menubar.addMenu(maze_menu)

        import_action = QAction('Import...', self)
        import_action.triggered.connect(self.import_maze)
        maze_menu.addAction(import_action)

        export_action = QAction('Export...', self)
        export_action.triggered.connect(self.export_maze)
        maze_menu.addAction(export_action)

    def import_maze(self):
        # Todo
        print('clicked import')

    def export_maze(self):
        # Todo
        print('clicked export')

    def add_options_menu(self, menubar: QMenuBar) -> None:
        options_menu = QMenu('Options', self)
        menubar.addMenu(options_menu)

        # Select the number of neighbors
        neighbors_menu = options_menu.addMenu('Neigbors')
        neighbor_group = QActionGroup(self)
        neighbors_four_action = QAction('4', self)
        neighbors_eight_action = QAction('8', self)
        neighbor_group.addAction(neighbors_four_action)
        neighbor_group.addAction(neighbors_eight_action)
        neighbors_four_action.setCheckable(True)
        neighbors_eight_action.setCheckable(True)
        neighbors_four_action.setChecked(True)
        neighbors_menu.addAction(neighbors_four_action)
        neighbors_menu.addAction(neighbors_eight_action)
        # todo slot neighbor_group.triggered

    def add_help_menu(self, menubar: QMenuBar) -> None:
        help_menu = QMenu('Help', self)
        menubar.addMenu(help_menu)

        help_action = QAction('Help...', self)
        help_action.triggered.connect(self.show_help)
        help_menu.addAction(help_action)

        help_menu.addSeparator()

        about_action = QAction('About...', self)
        about_action.triggered.connect(self.show_about)
        help_menu.addAction(about_action)

    def show_help(self):
        # Todo
        print('clicked help')

    def show_about(self):
        # Todo
        print('clicked about')

    def tower_limiter_clicked(self) -> None:
        self.max_towers_box.setDisabled(not self.tower_limiter.isChecked())

    def variation_changed(self) -> None:
        index = self.variation_box.value() - 1
        self.show_variation(index)

    def build(self) -> None:
        """
        Build a square area with TileWidgets.
        """
        self.clear_map()
        self.best_setups = []
        self.variation_box.setDisabled(True)

        width = self.width_box.value()
        height = self.height_box.value()
        self.tile_widgets = np.empty((width, height), TileWidget)

        counter = 0
        for x in range(width):
            for y in range(height):
                tile = Tile(x=x, y=y)
                tilew = TileWidget(tile)
                self.map_grid.addWidget(tilew, y, x)
                self.tile_widgets[x, y] = tilew
                counter += 1

    def clear_map(self) -> None:
        """
        Clear the TileWidgets from the map grid.
        """
        # No clearing needed on the first run
        if not self.tile_widgets.all():
            return

        for tilew in self.tile_widgets.flatten():
            self.map_grid.removeWidget(tilew)

    def get_tiles(self) -> np.ndarray:
        tiles = np.empty(np.size(self.tile_widgets), Tile)
        for i, tilew in enumerate(self.tile_widgets.flatten()):
            tiles[i] = tilew.tile
        return tiles

    def build_button_clicked(self) -> None:
        self.build()

    def run_button_clicked(self) -> None:
        self.disable_buttons(True)
        t1 = threading.Thread(target=self.initiate_maze_creating)
        t1.daemon = True
        t1.start()

    def disable_buttons(self, set_disable: bool) -> None:
        """
        Disable or enable all the buttons on the GUI.

        Args:
            set_disable: True to disable buttons, False to enable
        """
        for button in self.buttons:
            button.setDisabled(set_disable)

    def initiate_maze_creating(self):
        """
        Start the validation and maze creation for the current map.
        """
        print('\nValidating map ...')
        tiles = self.get_tiles()
        try:
            self.map_validator.validate_map(tiles)
            print(f'Map validation successful!')
        except ValidationError as e:
            print(f'Map validation failed: {e.message}!')
            self.disable_buttons(False)
            return

        print('\nGenerating optimal maze ...')
        max_towers = None
        if self.tower_limiter.isChecked():
            max_towers = self.max_towers_box.value()

        builder = NaiveBuilder(tiles, max_towers)
        self.best_setups = builder.generate_optimal_mazes()
        if self.best_setups:
            maze_count = len(self.best_setups)
            self.variation_label.setText(f'Variations ({maze_count})')
            self.variation_box.setMaximum(maze_count)

            # Show the final variation which has least towers
            if self.variation_box.value() == maze_count:
                self.show_variation(maze_count - 1)
            self.variation_box.setValue(maze_count)
            self.variation_box.setDisabled(False)

        else:
            print('\nCannot create a maze!')

        self.disable_buttons(False)

    def show_variation(self, index: int) -> None:
        """
        Change the tile types in the GUI according to a specific maze setup.

        Args:
            index: index of the best maze setup
        """
        if index >= len(self.best_setups) or index < 0:
            print('Variation does not exist!')
            return

        for coords, node in self.best_setups[index].items():
            self.tile_widgets[coords.x, coords.y].change_to_type(node.ttype)
        # print('\nMaze generated!')
