import json
import sys
import threading
import time
from multiprocessing import Queue
from multiprocessing.managers import BaseManager
from multiprocessing.shared_memory import SharedMemory

import numpy as np
import pyqtgraph as pg
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)
from sklearn.neighbors import NearestNeighbors

from shape import Circle, Parallelogram, Square, Triangle


class ShapeComparator:
    @staticmethod
    def find_closest_points(original_points, distorted_points):
        """
        Находит ближайшие точки между двумя наборами с использованием NearestNeighbors.
        :param original_points: Оригинальные точки (N x 2).
        :param distorted_points: Искажённые точки (M x 2).
        :return: Ближайшие точки из оригинального набора.
        """
        nbrs = NearestNeighbors(n_neighbors=1, algorithm="auto").fit(original_points)

        _, indices = nbrs.kneighbors(distorted_points)

        return original_points[indices.flatten()]

    @staticmethod
    def calculate_mse(original_points, distorted_points):
        """
        Вычисляет среднеквадратичную ошибку (MSE).
        :param original_points: Оригинальные точки (N x 2).
        :param distorted_points: Искажённые точки (M x 2).
        :return: Среднеквадратичная ошибка.
        """
        closest_points = ShapeComparator.find_closest_points(
            original_points, distorted_points
        )
        squared_errors = np.sum((closest_points - distorted_points) ** 2, axis=1)
        return np.mean(squared_errors)


class ICP:
    @staticmethod
    def icp_align(
        original_points, distorted_points, max_iterations=50, mse_threshold=0.10
    ):
        """
        Выравнивает искажённые точки относительно оригинальных с использованием ICP.
        :param original_points: Оригинальные точки (N x 2).
        :param distorted_points: Искажённые точки (M x 2).
        :param max_iterations: Максимальное число итераций.
        :param mse_threshold: Порог MSE для остановки.
        :return: Выровненные точки и MSE.
        """
        mse = float("inf")
        aligned_points = distorted_points.copy()

        for iteration in range(max_iterations):
            closest_points = ShapeComparator.find_closest_points(
                original_points, aligned_points
            )

            mse = ShapeComparator.calculate_mse(original_points, aligned_points)

            if mse < mse_threshold:
                break

            centroid_original = np.mean(closest_points, axis=0)
            centroid_distorted = np.mean(aligned_points, axis=0)

            centered_original = closest_points - centroid_original
            centered_distorted = aligned_points - centroid_distorted

            H = np.dot(centered_distorted.T, centered_original)

            U, _, Vt = np.linalg.svd(H)

            R = np.dot(Vt.T, U.T)

            t = centroid_original - np.dot(R, centroid_distorted)

            aligned_points = np.dot(aligned_points, R.T) + t

        return aligned_points, mse


class CommissionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_queue = Queue()
        self.command_queue = Queue()
        self.manager = None
        self.shm = None
        self.server_thread = None

        self.setWindowTitle("Комиссия: Фестиваль рисунков")
        self.setGeometry(100, 100, 1600, 900)

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.graphs_layout = QHBoxLayout()
        self.main_layout.addLayout(self.graphs_layout)

        self.figure_widgets = []
        self.metric_labels = []
        self.shape_names = ["Квадрат", "Треугольник", "Круг", "Параллелограмм"]
        self.current_results = {}

        for i in range(4):
            container = QVBoxLayout()

            plot_widget = pg.PlotWidget()
            plot_widget.setAspectLocked(True)
            plot_widget.setBackground("w")
            plot_widget.setXRange(-15, 15)
            plot_widget.setYRange(-15, 15)
            plot_widget.showGrid(x=True, y=True)
            plot_widget.enableAutoRange()
            self.figure_widgets.append(plot_widget)
            container.addWidget(plot_widget)

            metric_label = QLabel(f"{self.shape_names[i]}\nMSE: -")
            metric_label.setAlignment(Qt.AlignCenter)
            self.metric_labels.append(metric_label)
            container.addWidget(metric_label)

            self.graphs_layout.addLayout(container)

        self.winner_container = QVBoxLayout()
        self.winner_plot_widget = pg.PlotWidget()
        self.winner_plot_widget.setAspectLocked(True)
        self.winner_plot_widget.setBackground("w")
        self.winner_plot_widget.setXRange(-15, 15)
        self.winner_plot_widget.setYRange(-15, 15)
        self.winner_plot_widget.showGrid(x=True, y=True)
        self.winner_plot_widget.enableAutoRange()
        self.winner_container.addWidget(self.winner_plot_widget)

        self.winner_metric_label = QLabel("Победитель: -\nMSE: -")
        self.winner_metric_label.setAlignment(Qt.AlignCenter)
        self.winner_container.addWidget(self.winner_metric_label)

        self.main_layout.addLayout(self.winner_container)

        self.buttons_layout = QHBoxLayout()
        self.main_layout.addLayout(self.buttons_layout)

        self.start_button = QPushButton("Старт")
        self.start_button.clicked.connect(self.start_process)  # type: ignore
        self.buttons_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Стоп")
        self.stop_button.clicked.connect(self.stop_process)  # type: ignore
        self.buttons_layout.addWidget(self.stop_button)

        self.setup_manager()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_figures)  # type: ignore
        self.timer.start(1)

    def setup_manager(self):
        BaseManager.register("get_data_queue", callable=lambda: self.data_queue)
        BaseManager.register("get_command_queue", callable=lambda: self.command_queue)

        self.manager = BaseManager(address=("127.0.0.1", 50000), authkey=b"abracadabra")
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
        self.winner_plot_widget.clear()

    def update_figures(self):
        if not self.data_queue.empty():
            size = self.data_queue.get()
            try:
                st_time = time.time()
                raw_data = bytes(self.shm.buf[:size]).decode("utf-8")
                data = json.loads(raw_data)

                shape_name = data["shape"]
                points = data["points"]

                points = np.array(points, dtype=np.float64)

                index = {"square": 0, "triangle": 1, "circle": 2, "parallelogram": 3}[
                    shape_name
                ]

                original_shape = self.get_original_shape(shape_name)
                original_shape.generate_reference()
                original_points = original_shape.points

                aligned_points, mse = ICP.icp_align(original_points, points)

                self.figure_widgets[index].clear()
                self.figure_widgets[index].plot(
                    original_points[:, 0],
                    original_points[:, 1],
                    pen=None,
                    symbol="o",
                    symbolBrush=(0, 0, 255),
                    name="Оригинал",
                )

                self.figure_widgets[index].plot(
                    points[:, 0],
                    points[:, 1],
                    pen=None,
                    symbol="x",
                    symbolBrush=(255, 0, 0),
                    name="Искажённые",
                )

                self.figure_widgets[index].plot(
                    aligned_points[:, 0],
                    aligned_points[:, 1],
                    pen=None,
                    symbol="+",
                    symbolBrush=(0, 255, 0),
                    name="Нормализованные",
                )

                self.metric_labels[index].setText(
                    f"{self.shape_names[index]}\nMSE: {mse:.4f}"
                )
                self.current_results[shape_name] = {
                    "original_points": original_points,
                    "distorted_points": points,
                    "aligned_points": aligned_points,
                    "mse": mse,
                }
                f_time = time.time() - st_time
                print(
                    f"{shape_name.capitalize()} processed in: {f_time:.4f}s.{'!!!' if f_time > 0.2 else ''} "
                    f"with MSE: {mse:.4f}"
                )
                if len(self.current_results) == 4:
                    winner_shape = min(
                        self.current_results.keys(),
                        key=lambda x: self.current_results[x]["mse"],
                    )
                    winner_data = self.current_results[winner_shape]
                    self.update_winner(
                        winner_shape,
                        winner_data,
                    )
                    self.current_results = {}
            except Exception as e:
                print(f"Ошибка при обработке данных: {e}")
            else:
                self.command_queue.put("next")

    def update_winner(self, shape_name, figure_data):
        """
        Обновляет виджет победителя.
        :param shape_name:
        :param figure_data:
        :return:
        """
        original_points = figure_data["original_points"]
        distorted_points = figure_data["distorted_points"]
        aligned_points = figure_data["aligned_points"]
        mse = figure_data["mse"]

        self.winner_plot_widget.clear()

        self.winner_plot_widget.plot(
            original_points[:, 0],
            original_points[:, 1],
            pen=None,
            symbol="o",
            symbolBrush=(0, 0, 255),
            name="Оригинал",
        )

        self.winner_plot_widget.plot(
            distorted_points[:, 0],
            distorted_points[:, 1],
            pen=None,
            symbol="x",
            symbolBrush=(255, 0, 0),
            name="Искажённые",
        )

        self.winner_plot_widget.plot(
            aligned_points[:, 0],
            aligned_points[:, 1],
            pen=None,
            symbol="+",
            symbolBrush=(0, 255, 0),
            name="Нормализованные",
        )
        self.winner_metric_label.setText(f"Победитель: {shape_name}\nMSE: {mse:.4f}")

    def get_original_shape(self, shape_name):
        """
        Возвращает оригинальную фигуру по её имени.
        :param shape_name:
        :return:
        """
        match shape_name:
            case "square":
                return Square()
            case "triangle":
                return Triangle()
            case "circle":
                return Circle()
            case "parallelogram":
                return Parallelogram()

    def closeEvent(self, event):
        """
        Обработчик события закрытия окна.
        :param event:
        :return:
        """
        self.shm.close()
        self.shm.unlink()
        super().closeEvent(event)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CommissionApp()
    window.show()
    sys.exit(app.exec_())
