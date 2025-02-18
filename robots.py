from abc import ABC, abstractmethod
import numpy as np
from shape import Square, Triangle, Circle, Parallelogram

class Robot(ABC):
    def __init__(self, name, shape):
        self.name = name
        self.shape = shape  # Оригинальная фигура (экземпляр класса Shape)
        self.shape.generate_reference()  # Генерация точек при создании робота
        self.points = self.shape.points.astype(np.float64)  # Устанавливаем тип np.float64

    @abstractmethod
    def generate_distorted_shape(self):
        """
        Генерирует искажённую фигуру.
        """
        pass

    def thin_points(self, points, percent=10):
        """
        Прореживает точки на указанный процент.
        """
        num_points = len(points)
        num_to_remove = int(num_points * percent / 100)
        indices_to_remove = np.random.choice(num_points, num_to_remove, replace=False)
        return np.delete(points, indices_to_remove, axis=0)

    def add_noise(self, points, scale=0.1):
        """
        Добавляет шум к точкам.
        """
        noise = np.random.normal(0, scale, points.shape)
        return points + noise

    def rotate_points(self, points, angle):
        """
        Поворачивает точки на заданный угол (в градусах).
        """
        theta = np.radians(angle)
        rotation_matrix = np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)]
        ])
        return np.dot(points, rotation_matrix.T)

    def shift_points(self, points, shift_x, shift_y):
        """
        Смещает точки на заданные значения по осям X и Y.
        """
        return points + np.array([shift_x, shift_y])

    def send_data(self, queue, shm):
        """
        Отправляет данные через Shared Memory и очередь.
        """
        print(self.points)
        data = self.points.tobytes() # Сериализация данных
        print(data)
        shm.buf[:len(data)] = data  # Запись данных в Shared Memory
        queue.put(len(data))  # Отправка размера данных через очередь
        print(f"{self.name} отправил данные. Точки: {len(self.points)}")

    def receive_data(self, queue, shm):
        """
        Получает данные из Shared Memory и очереди.
        """
        size = queue.get()  # Получение размера данных
        data = bytes(shm.buf[:size])  # Чтение данных из Shared Memory
        self.points = np.frombuffer(data, dtype=np.float64).reshape(-1, 2)  # Десериализация данных
        print(f"{self.name} получил данные. Точки: {len(self.points)}")


class Glasha(Robot):
    def __init__(self):
        super().__init__("Глаша", Square(side_length=10))

    def generate_distorted_shape(self):
        # Генерация искажённого квадрата
        self.points = self.thin_points(self.points, percent=10)  # Прореживание
        self.points = self.add_noise(self.points, scale=0.1)  # Шум
        self.points = self.rotate_points(self.points, angle=np.random.uniform(0, 360))  # Поворот
        self.points = self.shift_points(self.points, shift_x=np.random.uniform(-5, 5), shift_y=np.random.uniform(-5, 5))  # Смещение


class Sasha(Robot):
    def __init__(self):
        super().__init__("Саша", Triangle(side_length=10))

    def generate_distorted_shape(self):
        # Генерация искажённого треугольника
        self.points = self.thin_points(self.points, percent=10)
        self.points = self.add_noise(self.points, scale=0.1)
        self.points = self.rotate_points(self.points, angle=np.random.uniform(0, 360))
        self.points = self.shift_points(self.points, shift_x=np.random.uniform(-5, 5), shift_y=np.random.uniform(-5, 5))


class Masha(Robot):
    def __init__(self):
        super().__init__("Маша", Circle(radius=5))

    def generate_distorted_shape(self):
        # Генерация искажённого круга
        self.points = self.thin_points(self.points, percent=10)
        self.points = self.add_noise(self.points, scale=0.1)
        self.points = self.rotate_points(self.points, angle=np.random.uniform(0, 360))
        self.points = self.shift_points(self.points, shift_x=np.random.uniform(-5, 5), shift_y=np.random.uniform(-5, 5))


class Natasha(Robot):
    def __init__(self):
        super().__init__("Наташа", Parallelogram(base=10, height=5, skew=2))

    def generate_distorted_shape(self):
        # Генерация искажённого параллелограмма
        self.points = self.thin_points(self.points, percent=10)
        self.points = self.add_noise(self.points, scale=0.1)
        self.points = self.rotate_points(self.points, angle=np.random.uniform(0, 360))
        self.points = self.shift_points(self.points, shift_x=np.random.uniform(-5, 5), shift_y=np.random.uniform(-5, 5))