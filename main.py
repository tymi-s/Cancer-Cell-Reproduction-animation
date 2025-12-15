import sys
from PyQt6.QtWidgets import (QApplication)
from CancerCellSimulator import *




def main():
    app = QApplication(sys.argv)
    window = CancerCellSimulator()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()