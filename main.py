import sys

from PyQt5.QtWidgets import QApplication

from gui.map_builder import Window
from utils.map_validation import MapValidator2D

if __name__ == '__main__':
    app = QApplication(sys.argv)
    mv = MapValidator2D()
    window = Window(mv)
    window.build()
    window.show()
    sys.exit(app.exec_())
