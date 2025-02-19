import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import pyqtgraph as pg
from pyqtgraph import PlotWidget
from shape import Square, Triangle, Circle, Parallelogram

class CommissionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Комиссия: Фестиваль рисунков")
        self.setGeometry(100, 100, 800, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        self.plot_widget = PlotWidget()
        self.layout.addWidget(self.plot_widget)

        self.plot_widget.setBackground('w')
        self.plot_widget.setXRange(-100, 100)
        self.plot_widget.setYRange(-100, 100)
        self.plot_widget.showGrid(x=True, y=True)

        self.load_shapes()

    def load_shapes(self):
        shapes = [
            Square(side_length=20),
            Triangle(side_length=20),
            Circle(radius=10),
            Parallelogram(base=16, height=10, skew=4)
        ]

        for shape in shapes:
            shape.generate_reference()
            self.plot_widget.plot(shape.points[:, 0], shape.points[:, 1], pen=pg.mkPen(color=(0, 0, 255), width=2), name=shape.name)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommissionApp()
    window.show()
    sys.exit(app.exec_())