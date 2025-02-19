import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
import pyqtgraph as pg
from shape import Square, Triangle, Circle, Parallelogram


class CommissionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Комиссия: Фестиваль рисунков")
        self.setGeometry(100, 100, 1200, 800)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.graphs_layout = QHBoxLayout()
        self.main_layout.addLayout(self.graphs_layout)

        self.figure_widgets = []
        for _ in range(4):
            plot_widget = pg.PlotWidget()
            plot_widget.setAspectLocked(True)
            plot_widget.setBackground('w')
            plot_widget.setXRange(-15, 15)
            plot_widget.setYRange(-15, 15)
            plot_widget.showGrid(x=True, y=True)
            self.figure_widgets.append(plot_widget)
            self.graphs_layout.addWidget(plot_widget)

        self.winner_widget = pg.PlotWidget()
        self.winner_widget.setAspectLocked(True)
        self.winner_widget.setBackground('w')
        self.winner_widget.setXRange(-15, 15)
        self.winner_widget.setYRange(-15, 15)
        self.winner_widget.showGrid(x=True, y=True)
        self.main_layout.addWidget(self.winner_widget)

        self.buttons_layout = QHBoxLayout()
        self.main_layout.addLayout(self.buttons_layout)

        self.start_button = QPushButton("Старт")
        self.start_button.clicked.connect(self.show_figures)  # type: ignore
        self.buttons_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Стоп")
        self.stop_button.clicked.connect(self.clear_figures)  # type: ignore
        self.buttons_layout.addWidget(self.stop_button)

        self.shapes = [
            Square(side_length=20),
            Triangle(side_length=20),
            Circle(radius=10),
            Parallelogram(base=16, height=10, skew=4)
        ]

    def show_figures(self):
        colors = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 0, 255)]

        for i, (shape, color) in enumerate(zip(self.shapes, colors)):
            shape.generate_reference()
            scatter = pg.ScatterPlotItem(shape.points[:, 0], shape.points[:, 1], pen=pg.mkPen(color=color), brush=pg.mkBrush(color), size=2)
            self.figure_widgets[i].addItem(scatter)

    def clear_figures(self):
        for widget in self.figure_widgets:
            widget.clear()
        self.winner_widget.clear()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommissionApp()
    window.show()
    sys.exit(app.exec_())