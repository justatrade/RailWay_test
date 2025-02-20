import sys
import json
import numpy as np
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton
from PyQt5.QtCore import QTimer
from multiprocessing.managers import BaseManager
from multiprocessing.shared_memory import SharedMemory
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
        self.start_button.clicked.connect(self.start_process)
        self.buttons_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Стоп")
        self.stop_button.clicked.connect(self.stop_process)
        self.buttons_layout.addWidget(self.stop_button)

        self.setup_manager()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_figures)
        self.timer.start(100)

    def setup_manager(self):
        from multiprocessing import Queue
        self.data_queue = Queue()
        self.command_queue = Queue()

        BaseManager.register('get_data_queue', callable=lambda: self.data_queue)
        BaseManager.register('get_command_queue', callable=lambda: self.command_queue)

        self.manager = BaseManager(address=('127.0.0.1', 50000), authkey=b'abracadabra')
        self.shm = SharedMemory(name="robot_memory", create=True, size=1048576)

        self.server_thread = threading.Thread(target=self.start_server)
        self.server_thread.daemon = True
        self.server_thread.start()

    def start_server(self):
        server = self.manager.get_server()
        print("Сервер запущен на 127.0.0.1:50000")
        server.serve_forever()

    def start_process(self):
        self.clear_figures()
        self.command_queue.put("start")

    def stop_process(self):
        self.command_queue.put("stop")

    def clear_figures(self):
        for widget in self.figure_widgets:
            widget.clear()
        self.winner_widget.clear()

    def update_figures(self):
        if not self.data_queue.empty():
            size = self.data_queue.get()
            try:
                raw_data = bytes(self.shm.buf[:size]).decode("utf-8")
                data = json.loads(raw_data)

                shape_name = data["shape"]
                points = data["points"]

                print(f"Получены данные: {shape_name}, точек: {len(points)}")

                points = np.array(points, dtype=np.float64)

                index = {"square": 0, "triangle": 1, "circle": 2, "parallelogram": 3}[shape_name]
                color = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 0, 255)][index]
                scatter = pg.ScatterPlotItem(points[:, 0], points[:, 1], pen=pg.mkPen(color=color), brush=pg.mkBrush(color), size=2)
                self.figure_widgets[index].addItem(scatter)
            except json.JSONDecodeError as e:
                print(f"Ошибка при десериализации JSON: {e}")
            except Exception as e:
                print(f"Неизвестная ошибка: {e}")

            # Отправляем команду "next" для подтверждения
            self.command_queue.put("next")

    def closeEvent(self, event):
        self.shm.close()
        self.shm.unlink()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommissionApp()
    window.show()
    sys.exit(app.exec_())