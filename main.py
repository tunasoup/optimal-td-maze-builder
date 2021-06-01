import sys

from PyQt5.QtWidgets import QApplication

from gui.map_builder import Window

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = Window()
    window.build()
    window.show()
    sys.exit(app.exec_())
