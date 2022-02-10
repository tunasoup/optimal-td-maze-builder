import threading
from typing import Type, Dict, List, Optional, Tuple, NamedTuple, Deque
from collections import deque

import numpy as np
from PyQt5.QtCore import Qt, pyqtSignal, pyqtSlot, QPoint, QRect, QSize
from PyQt5.QtGui import QPalette, QMouseEvent, QColor, QKeySequence
from PyQt5.QtWidgets import QWidget, QMainWindow, QGridLayout, QFormLayout, \
    QLabel, QPushButton, QSpinBox, QCheckBox, QMenu, QAction, QMenuBar, \
    QActionGroup, QFileDialog, QDockWidget, QHBoxLayout, QVBoxLayout, \
    QRubberBand,  QGraphicsBlurEffect

from builders import CutoffBuilder, NaiveBuilder
from gui.colorer import Colorer
from tiles.tile import Tile, Coords
from tiles.tile_type import TType, TTypeOccupied, TTypeBasic, TTYPES
from utils.errors import ValidationError
from utils.graph_algorithms import tiles_to_nodes, Node, \
    connect_all_neighboring_nodes
from utils.map_validation import MapValidator

DEFAULT_SIZE = 6
MINIMUM_SIZE = 2


class TTypeChange(NamedTuple):
    widget: QWidget
    old_ttype: Type[TType]
    new_ttype: Type[TType]


class ColoredRectangle(QWidget):
    def __init__(self, ttype: Type[TType]):
        super(ColoredRectangle, self).__init__()

        self.setAutoFillBackground(True)
        self.set_type_color(ttype)
        self.highlight: bool = False

        # todo better highlight system
        highlight_effect = QGraphicsBlurEffect()
        highlight_effect.setBlurRadius(4.0)
        self.setGraphicsEffect(highlight_effect)
        self.graphicsEffect().setEnabled(False)

    def set_type_color(self, ttype: Type[TType]) -> None:
        """
        Set the ColoredRectangle's color to correspond with the given type

        Args:
            ttype: a tile type whose defined color is to be used
        """
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(ttype.color))
        self.setPalette(palette)

    def toggle_highlight(self) -> None:
        self.highlight = not self.highlight
        self.graphicsEffect().setEnabled(self.highlight)


class TileWidget(ColoredRectangle):
    def __init__(self, tile: Tile):
        super(TileWidget, self).__init__(tile.ttype)

        self.tile = tile

    def change_to_type(self, ttype: Type[TType]) -> None:
        """
        Change the type of the Tile to the given type

        Args:
            ttype: a new tile type

        """
        self.tile.ttype = ttype
        self.set_type_color(ttype)


class MapWidget(QWidget):
    action_created = pyqtSignal(object)

    def __init__(self):
        """
        The map area of the GUI, which is responsible for adding, changing,
        removing, and showing TileWidgets, and handling their mouse events.
        """
        super(MapWidget, self).__init__()

        self.setAutoFillBackground(True)
        self.map_grid = QGridLayout(self)
        self.spacing = 1
        self.map_grid.setSpacing(self.spacing)

        self.selected_ttype: Type[TType] = TTypeBasic
        self.start_point = QPoint()
        self.end_point = QPoint()
        self.rubber_band = QRubberBand(QRubberBand.Rectangle, self)
        self.selected_widgets: List[TileWidget] = []

    def change_background_color(self, color) -> None:
        palette = self.palette()
        palette.setColor(QPalette.Window, QColor(color))
        self.setPalette(palette)

    def add_tile_widget(self, tile_widget: TileWidget):
        y = tile_widget.tile.y
        x = tile_widget.tile.x
        self.map_grid.addWidget(tile_widget, y, x)

    def remove_tile_widget(self, tile_widget: TileWidget):
        self.map_grid.removeWidget(tile_widget)

    def clear_selection(self) -> None:
        for tile_widget in self.selected_widgets:
            pass
            tile_widget.toggle_highlight()
        self.selected_widgets.clear()

    @pyqtSlot(object)
    def on_ttype_selection(self, ttype: Type[TType]) -> None:
        self.selected_ttype = ttype

    @pyqtSlot(object)
    def on_action_received(self, widgets_and_ttypes: List[Tuple]) -> None:
        for widget, ttype in widgets_and_ttypes:
            widget.change_to_type(ttype)

    @pyqtSlot(QMouseEvent)
    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.left_button_clicked(event)
        if event.button() == Qt.RightButton:
            self.right_button_clicked(event)

    def get_clicked_tile_widget(self, pos: QPoint) -> Optional[TileWidget]:
        """
        Get the TileWidget which resides in the given position.

        Args:
            pos: a pixel position relevant to the MapWidget

        Returns:
            a TileWidget in the given position if there is one, otherwise None
        """
        tile_widgets = (self.map_grid.itemAt(i).widget() for i in
                        range(self.map_grid.count()))
        for tile_widget in tile_widgets:
            if pos in tile_widget.geometry():
                return tile_widget
        return None

    def select_tile_widgets_in_area(self, selection_area: QRect) -> None:
        """
        Mark all the TileWidgets which intersect with the given area as
        selected.

        Args:
            selection_area: a rectangle area in the MapWidget
        """
        tile_widgets = (self.map_grid.itemAt(i).widget() for i in
                        range(self.map_grid.count()))
        for tile_widget in tile_widgets:
            if tile_widget.geometry().intersects(selection_area):
                self.selected_widgets.append(tile_widget)
                tile_widget.toggle_highlight()

    def left_button_clicked(self, event: QMouseEvent) -> None:
        tile_widget = self.get_clicked_tile_widget(event.pos())
        action: List[TTypeChange] = []
        if tile_widget:

            # If a selection exists and it was left clicked, fill
            if self.selected_widgets and tile_widget in self.selected_widgets:
                for selected_widget in self.selected_widgets:
                    old_ttype = selected_widget.tile.ttype
                    if old_ttype == self.selected_ttype:
                        continue
                    selected_widget.change_to_type(self.selected_ttype)
                    action.append(TTypeChange(selected_widget, old_ttype, self.selected_ttype))

            # Change the type of the clicked tile
            elif not self.selected_widgets:
                old_ttype = tile_widget.tile.ttype
                if not old_ttype == self.selected_ttype:
                    tile_widget.change_to_type(self.selected_ttype)
                    action.append(TTypeChange(tile_widget, old_ttype, self.selected_ttype))

        self.clear_selection()
        if action:
            self.action_created.emit(action)

    def right_button_clicked(self, event: QMouseEvent):
        self.start_point = QPoint(event.pos())
        self.rubber_band.setGeometry(QRect(self.start_point, QSize()))
        self.rubber_band.show()

    @pyqtSlot(QMouseEvent)
    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        if event.buttons() == Qt.RightButton:
            self.right_button_moved(event)

    def right_button_moved(self, event: QMouseEvent) -> None:
        if not self.start_point.isNull():
            # Update the Rubberband
            self.end_point = event.pos()
            self.rubber_band.setGeometry(QRect(self.start_point, self.end_point).normalized())

    @pyqtSlot(QMouseEvent)
    def mouseReleaseEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.RightButton:
            self.right_button_released(event)

    def right_button_released(self, event: QMouseEvent) -> None:
        # Update the Rubberband
        self.end_point = QPoint(event.pos())
        self.rubber_band.setGeometry(QRect(self.start_point, self.end_point).normalized())
        self.rubber_band.hide()

        # Clear selection on right click (+ small jitter threshold)
        if (self.end_point - self.start_point).manhattanLength() < 2:
            self.clear_selection()

        # Create a selection
        else:
            self.select_tile_widgets_in_area(self.rubber_band.geometry())


class SelectableTType(QWidget):
    clicked = pyqtSignal(object)

    def __init__(self, ttype: Type[TType]):
        super(SelectableTType, self).__init__()

        self.ttype = ttype
        self.name = ttype.name

        self.rectangle = ColoredRectangle(self.ttype)
        self.rectangle.setFixedSize(20, 20)

        layout = QHBoxLayout()
        layout.addWidget(self.rectangle)
        layout.addWidget(QLabel(self.name.capitalize()))
        self.setLayout(layout)

    def refresh_color(self) -> None:
        self.rectangle.set_type_color(self.ttype)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self)


class TTypeContainer(QWidget):
    ttype_clicked = pyqtSignal(object)

    def __init__(self):
        """
        A widget that contains the all possible tile types.
        """
        super(TTypeContainer, self).__init__()

        layout = QVBoxLayout()

        ttypes = TTYPES.values()
        self.selectable_ttypes = np.empty(len(ttypes), SelectableTType)
        self.selected: Optional[SelectableTType] = None

        for idx, ttype in enumerate(ttypes):
            selectable_ttype = SelectableTType(ttype)
            selectable_ttype.clicked.connect(self.on_clicked)
            self.selectable_ttypes[idx] = selectable_ttype
            layout.addWidget(selectable_ttype)

        self.setLayout(layout)
        self.set_first_selection()

    def set_first_selection(self) -> None:
        """
        Set initially the first SelectableTType as selected. Only
        meant to be called by the TTypeContainer constructor.
        """
        if not self.selectable_ttypes.all():
            print('\nWarning: no selectable ttypes!\n')
            return
        selectable_ttype = self.selectable_ttypes[0]
        selectable_ttype.rectangle.toggle_highlight()
        self.selected = selectable_ttype
        self.ttype_clicked.emit(selectable_ttype.ttype)

    def refresh_selectable_ttype_colors(self) -> None:
        for selectable_ttype in self.selectable_ttypes:
            selectable_ttype.refresh_color()

    @pyqtSlot(object)
    def on_clicked(self, selectable_ttype: SelectableTType):
        if self.selected:
            self.selected.rectangle.toggle_highlight()
        selectable_ttype.rectangle.toggle_highlight()
        self.selected = selectable_ttype
        self.ttype_clicked.emit(selectable_ttype.ttype)


class ActionLogger(QWidget):
    do_action = pyqtSignal(object)

    def __init__(self):
        """
        Logs TType changes of TilesWidgets for undo and redo purposes.
        """
        super(ActionLogger, self).__init__()
        maximum_actions_logged = 10
        self.undo_stack: Deque[List[TTypeChange]] = deque(maxlen=maximum_actions_logged)
        self.redo_stack: Deque[List[TTypeChange]] = deque(maxlen=maximum_actions_logged)

    @pyqtSlot(object)
    def log_action(self, action):
        self.redo_stack.clear()
        if len(self.undo_stack) == self.undo_stack.maxlen:
            self.undo_stack.popleft()

        self.undo_stack.append(action)

    def undo(self):
        if not self.undo_stack:
            return

        action = self.undo_stack.pop()
        self.redo_stack.append(action)
        widgets_and_ttypes = [(ttype_change.widget, ttype_change.old_ttype) for
                              ttype_change in action]
        self.do_action.emit(widgets_and_ttypes)

    def redo(self):
        if not self.redo_stack:
            return

        action = self.redo_stack.pop()
        self.undo_stack.append(action)
        widgets_and_ttypes = [(ttype_change.widget, ttype_change.new_ttype) for
                              ttype_change in action]
        self.do_action.emit(widgets_and_ttypes)

    def clear(self) -> None:
        self.undo_stack.clear()
        self.redo_stack.clear()


class Window(QMainWindow):
    def __init__(self, map_validator: MapValidator):
        super().__init__()

        self.map_validator = map_validator
        self.colorer = Colorer()
        self.logger = ActionLogger()

        self.setGeometry(300, 300, 600, 400)
        self.setWindowTitle("TD maze builder")

        self.neighbor_group = QActionGroup(self)
        self.color_profile_group = QActionGroup(self)

        self.create_menubar()

        main_layout = QGridLayout()

        self.map_widget = MapWidget()
        self.map_widget.action_created.connect(self.logger.log_action)
        self.logger.do_action.connect(self.map_widget.on_action_received)
        main_layout.addWidget(self.map_widget, 0, 0, -1, 3)

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

        self.ttype_container = TTypeContainer()
        self.ttype_window = self.create_ttype_window(self.ttype_container)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.ttype_window)
        self.ttype_container.ttype_clicked.connect(self.map_widget.on_ttype_selection)

        self.setFocus()

    def create_menubar(self) -> None:
        menubar = self.menuBar()
        self.add_maze_menu(menubar)
        self.add_edit_menu(menubar)
        self.add_options_menu(menubar)
        self.add_view_menu(menubar)
        # self.add_help_menu(menubar)

    def add_maze_menu(self, menubar: QMenuBar) -> None:
        maze_menu = QMenu('Maze', self)
        menubar.addMenu(maze_menu)

        import_action = QAction('Import...', self)
        import_action.triggered.connect(self.import_maze)
        maze_menu.addAction(import_action)

        export_action = QAction('Export...', self)
        export_action.triggered.connect(self.export_maze)
        maze_menu.addAction(export_action)

    @pyqtSlot()
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

    @pyqtSlot()
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

    def add_edit_menu(self, menubar: QMenuBar) -> None:
        edit_menu = QMenu('Edit', self)
        menubar.addMenu(edit_menu)

        undo_action = QAction('Undo', self)
        undo_action.setShortcut(QKeySequence("Ctrl+z"))
        undo_action.triggered.connect(self.on_undo)
        edit_menu.addAction(undo_action)

        redo_action = QAction('Redo', self)
        redo_action.setShortcut(QKeySequence("Ctrl+Shift+z"))
        redo_action.triggered.connect(self.on_redo)
        edit_menu.addAction(redo_action)

    def on_undo(self) -> None:
        self.logger.undo()

    def on_redo(self) -> None:
        self.logger.redo()

    def add_options_menu(self, menubar: QMenuBar) -> None:
        options_menu = QMenu('Options', self)
        menubar.addMenu(options_menu)

        self.add_neighbors_submenu(options_menu)
        self.add_color_profile_submenu(options_menu)

    def add_neighbors_submenu(self, parent_menu: QMenu) -> None:
        """
        Add a submenu in which the number of neighbors for a Node is selected.

        Args:
            parent_menu: a QMenu that this submenu is part of
        """
        neighbors_submenu = parent_menu.addMenu('Neigbors')

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
        self.map_widget.change_background_color(color)

    @pyqtSlot()
    def change_color_profile(self) -> None:
        """
        Change the colors of the GUI to the currently selected color profile.
        """
        color_profile_name = self.color_profile_group.checkedAction().text()
        self.colorer.change_to_profile(color_profile_name)
        self.change_background_color(color_profile_name)

        # Refresh the map colors
        for tile_widget in self.tile_widgets.flatten():
            tile_widget.set_type_color(tile_widget.tile.ttype)

        # Refresh the ttype window colors
        self.ttype_container.refresh_selectable_ttype_colors()

    def add_view_menu(self, menubar: QMenuBar) -> None:
        view_menu = QMenu('View', self)
        menubar.addMenu(view_menu)

        view_menu.addAction(self.create_ttype_window_action())

    def create_ttype_window_action(self) -> QAction:
        ttype_window_action = QAction('Type Window', self)
        ttype_window_action.setCheckable(True)
        ttype_window_action.setChecked(True)
        ttype_window_action.triggered.connect(self.toggle_ttype_window)
        return ttype_window_action

    # todo: closing the ttype window (altf4, x) doesn't uncheck the action

    @pyqtSlot()
    def toggle_ttype_window(self) -> None:
        if self.ttype_window.isHidden():
            self.ttype_window.show()
        else:
            self.ttype_window.hide()

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

    def create_ttype_window(self, ttype_container: TTypeContainer) -> QDockWidget:
        ttype_window = QDockWidget('Types', parent=self)
        # Removes the close button, doesn't prevent alt+f4
        # ttype_window.setFeatures(QDockWidget.DockWidgetFloatable | QDockWidget.DockWidgetMovable)
        ttype_window.setWidget(ttype_container)
        return ttype_window

    @pyqtSlot()
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
                self.map_widget.add_tile_widget(tilew)
                self.tile_widgets[x, y] = tilew

    def build_from_tiles(self, tiles) -> None:
        """
        Build a rectangle area of TileWidgets with given coordinated_nodes.
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
            self.map_widget.add_tile_widget(tilew)
            self.tile_widgets[x, y] = tilew

    def clear_map(self) -> None:
        self.logger.clear()
        self.best_tower_coords = []

        if not self.tile_widgets.all():
            return

        for tilew in self.tile_widgets.flatten():
            self.map_widget.remove_tile_widget(tilew)

        self.tile_widgets = None

    def get_tiles(self) -> np.ndarray:
        tiles = np.empty(np.size(self.tile_widgets), Tile)
        for i, tilew in enumerate(self.tile_widgets.flatten()):
            tiles[i] = tilew.tile
        return tiles

    @pyqtSlot()
    def build_button_clicked(self) -> None:
        self.build()
        self.setFocus()

    @pyqtSlot()
    def run_button_clicked(self) -> None:
        self.disable_buttons(True)
        self.logger.clear()
        self.variation_box.setDisabled(True)
        t1 = threading.Thread(target=self.create_maze)
        t1.daemon = True
        t1.start()
        self.setFocus()

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
        coordinated_nodes = tiles_to_nodes(tiles)
        connect_all_neighboring_nodes(coordinated_nodes, neighbor_count)

        if self.initiate_map_validation(np.array(list(coordinated_nodes.values())),):
            self.initiate_optimal_mazing(coordinated_nodes)

    def initiate_map_validation(self, nodes: np.ndarray) -> bool:
        """
        Initiate the map validation.

        Args:
            nodes: an array of Nodes

        Returns:
            True if the map is valid, else False
        """
        print('\nValidating map ...')
        try:
            self.map_validator.validate_map(nodes)
            print(f'Map validation successful!')
            return True
        except ValidationError as e:
            print(f'Map validation failed: {e.message}!')
            self.disable_buttons(False)
            return False

    def initiate_optimal_mazing(self, coordinated_nodes: Dict[Coords, Node]) -> None:
        """
        Initiate the optimal mazing, and show one of the solutions.

        Args:
            coordinated_nodes: a dictionary with Coords as keys and Nodes as values
        """
        print('\nGenerating optimal maze ...')
        tower_limit = None
        if self.tower_limiter.isChecked():
            tower_limit = self.tower_limit_box.value()

        # builder = NaiveBuilder(coordinated_nodes, tower_limit)
        builder = CutoffBuilder(coordinated_nodes, tower_limit)
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
            # todo: after changing a variation and coordinated_nodes and running
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
