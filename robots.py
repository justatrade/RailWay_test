import json
from abc import ABC, abstractmethod
import numpy as np
from shape import Square, Triangle, Circle, Parallelogram

class Robot(ABC):
    def __init__(self, name, shape):
        self.name = name
        self.shape = shape
        self.shape.generate_reference()
        self.points = self.shape.points.astype(np.float64)

    @abstractmethod
    def generate_distorted_shape(self):
        pass

    def thin_points(self, points, percent=10):
        num_points = len(points)
        num_to_remove = int(num_points * percent / 100)
        indices_to_remove = np.random.choice(num_points, num_to_remove, replace=False)
        return np.delete(points, indices_to_remove, axis=0)

    def add_noise(self, points, scale=0.3):
        noise = np.random.normal(0, scale, points.shape)
        return points + noise

    def rotate_points(self, points, angle):
        theta = np.radians(angle)
        rotation_matrix = np.array([
            [np.cos(theta), -np.sin(theta)],
            [np.sin(theta), np.cos(theta)]
        ])
        return np.dot(points, rotation_matrix.T)

    def shift_points(self, points, shift_x, shift_y):
        shifted_points = points + np.array([shift_x, shift_y])
        return np.clip(shifted_points, -100, 100)

    def send_data(self, queue, shm):
        data = {
            "shape": self.shape.name,
            "points": self.points.tolist()
        }
        serialized_data = json.dumps(data).encode("utf-8")
        shm.buf[:len(serialized_data)] = serialized_data
        queue.put(len(serialized_data))
        print(f"{self.name} отправил данные. Точки: {len(self.points)}")

class Glasha(Robot):
    def __init__(self):
        super().__init__("Глаша", Square(side_length=20))

    def generate_distorted_shape(self):
        self.points = self.thin_points(self.points, percent=10)
        self.points = self.add_noise(self.points, scale=0.3)
        self.points = self.rotate_points(self.points, angle=np.random.uniform(0, 360))
        self.points = self.shift_points(self.points, shift_x=np.random.uniform(-50, 50), shift_y=np.random.uniform(-50, 50))

class Sasha(Robot):
    def __init__(self):
        super().__init__("Саша", Triangle(side_length=20))

    def generate_distorted_shape(self):
        self.points = self.thin_points(self.points, percent=10)
        self.points = self.add_noise(self.points, scale=0.3)
        self.points = self.rotate_points(self.points, angle=np.random.uniform(0, 360))
        self.points = self.shift_points(self.points, shift_x=np.random.uniform(-50, 50), shift_y=np.random.uniform(-50, 50))

class Masha(Robot):
    def __init__(self):
        super().__init__("Маша", Circle(radius=10))

    def generate_distorted_shape(self):
        self.points = self.thin_points(self.points, percent=10)
        self.points = self.add_noise(self.points, scale=0.3)
        self.points = self.rotate_points(self.points, angle=np.random.uniform(0, 360))
        self.points = self.shift_points(self.points, shift_x=np.random.uniform(-50, 50), shift_y=np.random.uniform(-50, 50))

class Natasha(Robot):
    def __init__(self):
        super().__init__("Наташа", Parallelogram(base=16, height=10, skew=4))

    def generate_distorted_shape(self):
        self.points = self.thin_points(self.points, percent=10)
        self.points = self.add_noise(self.points, scale=0.3)
        self.points = self.rotate_points(self.points, angle=np.random.uniform(0, 360))
        self.points = self.shift_points(self.points, shift_x=np.random.uniform(-50, 50), shift_y=np.random.uniform(-50, 50))
