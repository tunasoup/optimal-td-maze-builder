import threading
from typing import Type

import numpy as np
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPalette, QMouseEvent, QColor
from PyQt5.QtWidgets import QWidget, QMainWindow, QGridLayout, QFormLayout, \
    QLabel, QPushButton, QSpinBox, QCheckBox, QMenu, QAction, QMenuBar, \
    QActionGroup, QFileDialog

from builders import CutoffBuilder, NaiveBuilder
from gui.colorer import Colorer
from tiles.tile import Tile
from tiles.tile_type import TType, TILE_ROTATION, TILE_ROTATION_REVERSE, \
    TTypeOccupied, TTypeBasic
from utils.errors import ValidationError
from utils.map_validation import MapValidator

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
        palette.setColor(QPalette.Window, QColor(ttype.color))
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
        self.colorer = Colorer()

        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("TD maze builder")

        self.create_menubar()

        main_layout = QGridLayout()

        # Layout for the map
        self.grid_widget = QWidget()
        self.grid_widget.setAutoFillBackground(True)
        self.map_grid = QGridLayout(self.grid_widget)
        self.map_grid.setSpacing(1)
        main_layout.addWidget(self.grid_widget, 0, 0, -1, 3)

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
        self.tower_limit_box = QSpinBox()
        self.tower_limit_box.setMinimum(0)
        self.tower_limit_box.setDisabled(True)
        info_layout.addRow(QLabel('Limit towers:'), self.tower_limiter)
        info_layout.addRow(QLabel('Tower count:'), self.tower_limit_box)

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
        self.previous_index = None
        self.best_tower_coords = []

        color_profile_name = self.colorer.color_profile_names[0]
        self.colorer.change_to_profile(color_profile_name)
        self.change_background_color(color_profile_name)

    def create_menubar(self) -> None:
        menubar = self.menuBar()
        self.add_maze_menu(menubar)
        self.add_options_menu(menubar)
        #self.add_help_menu(menubar)

    def add_maze_menu(self, menubar: QMenuBar) -> None:
        maze_menu = QMenu('Maze', self)
        menubar.addMenu(maze_menu)

        import_action = QAction('Import...', self)
        import_action.triggered.connect(self.import_maze)
        maze_menu.addAction(import_action)

        export_action = QAction('Export...', self)
        export_action.triggered.connect(self.export_maze)
        maze_menu.addAction(export_action)

    def import_maze(self) -> None:
        """
        Import a saved maze.
        """
        file_path, _ = QFileDialog.getOpenFileName(self,
                                                   "Open File",
                                                   "maps",
                                                   "npz (*.npz)")
        if file_path:
            np_file = np.load(file_path, allow_pickle=True)
            tiles = np_file[np_file.files[0]]
            self.build_from_tiles(tiles)

    def export_maze(self) -> None:
        """
        Save the current maze as a file.

        Note that only the visual part of the current maze is saved,
        and the maze acts as if it has not been validated yet.
        """
        tiles = self.get_tiles()
        file_path, _ = QFileDialog.getSaveFileName(self,
                                                   "Save File",
                                                   "maps",
                                                   "npz (*.npz)")
        if file_path:
            print(file_path)
            np.savez_compressed(file_path, tiles)

    def add_options_menu(self, menubar: QMenuBar) -> None:
        options_menu = QMenu('Options', self)
        menubar.addMenu(options_menu)

        self.add_neighbors_submenu(options_menu)
        self.add_color_profile_submenu(options_menu)

    def add_neighbors_submenu(self, parent_menu: QMenu) -> None:
        """
        Add a submenu in which the number of neighbors for a node is selected.

        Args:
            parent_menu: a QMenu that this submenu is part of
        """
        neighbors_submenu = parent_menu.addMenu('Neigbors')
        self.neighbor_group = QActionGroup(self)

        for count in [4, 8]:
            neighbor_action = QAction(str(count), self)
            self.neighbor_group.addAction(neighbor_action)
            neighbor_action.setCheckable(True)
            neighbors_submenu.addAction(neighbor_action)

        self.neighbor_group.actions()[0].setChecked(True)

    def add_color_profile_submenu(self, parent_menu: QMenu) -> None:
        """
        Add a submenu in which the color profile for the GUI is selected.

        Args:
            parent_menu: a QMenu that this submenu is part of
        """
        color_profile_submenu = parent_menu.addMenu('Color Profile')
        self.color_profile_group = QActionGroup(self)

        for color_profile_name in self.colorer.color_profile_names:
            color_profile_action = QAction(color_profile_name, self)
            self.color_profile_group.addAction(color_profile_action)
            color_profile_action.setCheckable(True)
            color_profile_submenu.addAction(color_profile_action)

        self.color_profile_group.triggered.connect(self.change_color_profile)
        self.color_profile_group.actions()[0].setChecked(True)

    def change_background_color(self, color_profile_name: str) -> None:
        """
        Change the background color of the map to the given color profile.

        Args:
            color_profile_name: the name of a color profile
        """
        color = self.colorer.get_background_color(color_profile_name)
        palette = self.grid_widget.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.grid_widget.setPalette(palette)

    def change_color_profile(self) -> None:
        """
        Change the colors of the GUI to the currently selected color profile.
        """
        color_profile_name = self.color_profile_group.checkedAction().text()
        self.colorer.change_to_profile(color_profile_name)
        self.change_background_color(color_profile_name)

        # Update current GUI
        for tile_widget in self.tile_widgets.flatten():
            tile_widget.set_type_color(tile_widget.tile.ttype)

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
        self.tower_limit_box.setDisabled(not self.tower_limiter.isChecked())

    def variation_changed(self) -> None:
        index = self.variation_box.value() - 1
        self.show_variation(index)

    def build(self) -> None:
        """
        Build a rectangle area of TileWidgets.
        """
        self.clear_map()
        self.variation_box.setDisabled(True)

        width = self.width_box.value()
        height = self.height_box.value()
        self.tile_widgets = np.empty((width, height), TileWidget)

        for x in range(width):
            for y in range(height):
                tile = Tile(x=x, y=y)
                tilew = TileWidget(tile)
                self.map_grid.addWidget(tilew, y, x)
                self.tile_widgets[x, y] = tilew

    def build_from_tiles(self, tiles) -> None:
        """
        Build a rectangle area of TileWidgets with given tiles.
        """
        self.clear_map()
        self.variation_box.setDisabled(True)

        # The ultimate tile is assumed to be in the bottom-right corner
        ultimate_tile = tiles[-1]
        width, height = ultimate_tile.x + 1, ultimate_tile.y + 1

        self.width_box.setValue(width)
        self.height_box.setValue(height)
        self.tile_widgets = np.empty((width, height), TileWidget)

        for tile in tiles:
            tilew = TileWidget(tile)
            x, y = tile.x, tile.y
            self.map_grid.addWidget(tilew, y, x)
            self.tile_widgets[x, y] = tilew

    def clear_map(self) -> None:
        """
        Clear the TileWidgets from the map grid.
        """
        # No clearing needed on the first run
        if not self.tile_widgets.all():
            return

        for tilew in self.tile_widgets.flatten():
            self.map_grid.removeWidget(tilew)

        self.best_tower_coords = []

    def get_tiles(self) -> np.ndarray:
        tiles = np.empty(np.size(self.tile_widgets), Tile)
        for i, tilew in enumerate(self.tile_widgets.flatten()):
            tiles[i] = tilew.tile
        return tiles

    def build_button_clicked(self) -> None:
        self.build()

    def run_button_clicked(self) -> None:
        self.disable_buttons(True)
        self.variation_box.setDisabled(True)
        t1 = threading.Thread(target=self.create_maze)
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

    def create_maze(self):
        """
        Start the validation and optimal mazing for the current map.
        """
        neighbor_count = int(self.neighbor_group.checkedAction().text())
        tiles = self.get_tiles()
        if self.initiate_map_validation(tiles, neighbor_count):
            self.initiate_optimal_mazing(tiles, neighbor_count)

    def initiate_map_validation(self, tiles: np.ndarray, neighbor_count: int) -> bool:
        """
        Initiate the map validation.

        Args:
            tiles: an array of Tiles
            neighbor_count: the number of neighbors a Node can have

        Returns:
            True if the map is valid, else False
        """
        print('\nValidating map ...')
        try:
            self.map_validator.validate_map(tiles, neighbor_count)
            print(f'Map validation successful!')
            return True
        except ValidationError as e:
            print(f'Map validation failed: {e.message}!')
            self.disable_buttons(False)
            return False

    def initiate_optimal_mazing(self, tiles: np.ndarray, neighbor_count: int) -> None:
        """
        Initiate the optimal mazing, and show one of the solutions.

        Args:
            tiles: an array of Tiles
            neighbor_count: the number of neighbors a Node can have
        """
        print('\nGenerating optimal maze ...')
        tower_limit = None
        if self.tower_limiter.isChecked():
            tower_limit = self.tower_limit_box.value()

        #builder = NaiveBuilder(tiles, neighbor_count, tower_limit)
        builder = CutoffBuilder(tiles, neighbor_count, tower_limit)
        self.best_tower_coords = builder.generate_optimal_mazes()

        if self.best_tower_coords:
            maze_count = len(self.best_tower_coords)
            self.variation_label.setText(f'Variations ({maze_count})')
            self.variation_box.setMaximum(maze_count)

            # Show the variation which has the least towers (only for NaiveBuilder)
            self.previous_index = None
            index = 0
            if self.variation_box.value() == index + 1:
                self.show_variation(index)
            self.variation_box.setValue(index + 1)  # TODO Has a chance to crash
            # todo: after changing a variation and tiles and running
            self.variation_box.setDisabled(False)
            print('\nMaze generated!')

        else:
            print('\nCannot create a maze!')

        self.disable_buttons(False)

    def show_variation(self, index: int) -> None:
        """
        Change the tile types in the GUI according to a specific maze setup.

        Args:
            index: index of the best maze setup
        """
        if index >= len(self.best_tower_coords) or index < 0:
            print('Variation does not exist!')
            return

        # Remove the towers of the previous setup
        if self.previous_index is not None:
            for coords in self.best_tower_coords[self.previous_index]:
                self.tile_widgets[coords.x, coords.y].change_to_type(TTypeBasic)

        # Add the new towers
        for coords in self.best_tower_coords[index]:
            self.tile_widgets[coords.x, coords.y].change_to_type(TTypeOccupied)

        self.previous_index = index
