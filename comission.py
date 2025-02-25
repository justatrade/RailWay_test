import json
import sys
import threading

import numpy as np
import pyqtgraph as pg
from multiprocessing import Queue
from multiprocessing.managers import BaseManager
from multiprocessing.shared_memory import SharedMemory
from PyQt5.QtCore import QTimer, Qt
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel
from scipy.spatial.distance import cdist
from shape import Square, Triangle, Circle, Parallelogram
from sklearn.decomposition import PCA


class ShapeNormalizer:
    @staticmethod
    def align_centers(distorted_points):
        """
        Выравнивает центры масс искажённой фигуры относительно (0, 0).
        :param distorted_points:
        :return:
        """
        distorted_center = np.mean(distorted_points, axis=0)
        return distorted_points - distorted_center

    @staticmethod
    def find_rotation_angle(original_points, distorted_points):
        """
        Определяет угол поворота искажённой фигуры относительно оригинальной.
        :param original_points:
        :param distorted_points:
        :return:
        """
        pca_original = PCA(n_components=2).fit(original_points)
        pca_distorted = PCA(n_components=2).fit(distorted_points)
        angle = np.arctan2(pca_distorted.components_[0, 1], pca_distorted.components_[0, 0]) - \
                np.arctan2(pca_original.components_[0, 1], pca_original.components_[0, 0])
        return np.degrees(angle)

    @staticmethod
    def rotate_points(points, angle):
        """
        Поворачивает точки на заданный угол.
        :param points:
        :param angle:
        :return:
        """
        theta = np.radians(angle)
        rotation_matrix = np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)]
        ])
        return np.dot(points, rotation_matrix.T)

    def normalize(self, original_points, distorted_points):
        """
        Нормализует искажённую фигуру (выравнивание и поворот).
        :param original_points:
        :param distorted_points:
        :return:
        """
        aligned_points = self.align_centers(distorted_points)
        if original_points.shape[0] > 0 and not np.allclose(original_points, original_points[0]):
            angle = self.find_rotation_angle(original_points, aligned_points)
            rotated_points = self.rotate_points(aligned_points, -angle)
            return rotated_points
        return aligned_points


class ShapeComparator:
    @staticmethod
    def find_closest_points(original_points, distorted_points):
        """
        Находит ближайшие точки между двумя наборами.
        :param original_points:
        :param distorted_points:
        :return:
        """
        distances = cdist(original_points, distorted_points)
        closest_indices = np.argmin(distances, axis=0)
        return original_points[closest_indices]

    @staticmethod
    def calculate_mse(original_points, distorted_points):
        """
        Вычисляет среднеквадратичную ошибку (MSE).
        :param original_points:
        :param distorted_points:
        :return:
        """
        closest_points = ShapeComparator.find_closest_points(original_points, distorted_points)
        squared_errors = np.sum((closest_points - distorted_points) ** 2, axis=1)
        return np.mean(squared_errors)

    def compare(self, original_points, distorted_points):
        """
        Сравнивает две фигуры и возвращает MSE.
        :param original_points:
        :param distorted_points:
        :return:
        """
        # normalized_points = distorted_points
        normalized_points = ShapeNormalizer().normalize(original_points, distorted_points)
        return self.calculate_mse(original_points, normalized_points)


class CommissionApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.data_queue = Queue()
        self.command_queue = Queue()
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
            plot_widget.setBackground('w')
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
        self.winner_plot_widget.setBackground('w')
        self.winner_plot_widget.setXRange(-15, 15)
        self.winner_plot_widget.setYRange(-15, 15)
        self.winner_plot_widget.showGrid(x=True, y=True)
        self.winner_plot_widget.enableAutoRange()  # Включаем автомасштабирование
        self.winner_container.addWidget(self.winner_plot_widget)

        self.winner_metric_label = QLabel("Победитель: -\nMSE: -")
        self.winner_metric_label.setAlignment(Qt.AlignCenter)
        self.winner_container.addWidget(self.winner_metric_label)

        self.main_layout.addLayout(self.winner_container)

        self.buttons_layout = QHBoxLayout()
        self.main_layout.addLayout(self.buttons_layout)

        self.start_button = QPushButton("Старт")
        self.start_button.clicked.connect(self.start_process) # type: ignore
        self.buttons_layout.addWidget(self.start_button)

        self.stop_button = QPushButton("Стоп")
        self.stop_button.clicked.connect(self.stop_process) # type: ignore
        self.buttons_layout.addWidget(self.stop_button)

        self.setup_manager()

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_figures) # type: ignore
        self.timer.start(1)

    def setup_manager(self):
        BaseManager.register('get_data_queue', callable=lambda: self.data_queue)
        BaseManager.register('get_command_queue', callable=lambda: self.command_queue)

        self.manager = BaseManager(address=('127.0.0.1', 50000), authkey=b'abracadabra')
        self.shm = SharedMemory(name="robot_memory", create=True, size=104857600)

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
                raw_data = bytes(self.shm.buf[:size]).decode("utf-8")
                data = json.loads(raw_data)

                shape_name = data["shape"]
                points = data["points"]

                print(f"Получены данные: {shape_name}, точек: {len(points)}")

                points = np.array(points, dtype=np.float64)

                index = {"square": 0, "triangle": 1, "circle": 2, "parallelogram": 3}[shape_name]
                color = [(0, 0, 255), (0, 255, 0), (255, 0, 0), (255, 0, 255)][index]

                # Получаем оригинальную фигуру
                original_shape = self.get_original_shape(shape_name)
                original_shape.generate_reference()  # Генерация точек
                original_points = original_shape.points

                normalized_points = ShapeNormalizer().normalize(original_points, points)

                # Отрисовка оригинальной фигуры
                self.figure_widgets[index].clear()
                self.figure_widgets[index].plot(original_points[:, 0], original_points[:, 1], pen=None, symbol='o', symbolBrush=color, name="Оригинал")

                # Отрисовка искажённой фигуры
                self.figure_widgets[index].plot(points[:, 0], points[:, 1], pen=None, symbol='p', symbolBrush=color, name="Робот")

                self.figure_widgets[index].plot(normalized_points[:, 0], normalized_points[:, 1], pen=None, symbol="x", symbolBrush=color, name="Нормированный")

                # Вычисление MSE
                mse = ShapeComparator().compare(original_points, points)
                self.metric_labels[index].setText(f"{self.shape_names[index]}\nMSE: {mse:.4f}")
                self.current_results[shape_name] = {
                    "original_points": original_points,
                    "distorted_points": points,
                    "mse": mse,
                }
                if len(self.current_results) == 4:
                    winner_shape = min(self.current_results.keys(), key=lambda x: self.current_results[x]["mse"])
                    # Обновляем победителя
                    self.update_winner(
                        winner_shape,
                        self.current_results[winner_shape]["original_points"],
                        self.current_results[winner_shape]["distorted_points"],
                        self.current_results[winner_shape]["mse"],
                    )
                    self.current_results = {}

            except Exception as e:
                print(f"Ошибка при обработке данных: {e}")
            else:
                self.command_queue.put("next")

    def update_winner(self, shape_name, original_points, distorted_points, mse):
        """
        Обновляет виджет победителя.
        :param shape_name:
        :param original_points:
        :param distorted_points:
        :param mse:
        :return:
        """
        self.winner_plot_widget.clear()

        self.winner_plot_widget.plot(original_points[:, 0], original_points[:, 1], pen=None, symbol='o', symbolBrush=(0, 0, 0), name="Оригинал")

        self.winner_plot_widget.plot(distorted_points[:, 0], distorted_points[:, 1], pen=None, symbol='p', symbolBrush=(255, 0, 0), name="Робот")

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
        return None

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