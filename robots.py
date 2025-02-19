import json
import time
import numpy as np
from multiprocessing import Lock
from multiprocessing.managers import BaseManager
from multiprocessing.shared_memory import SharedMemory
from shape import Square, Triangle, Circle, Parallelogram

GENERATION_INTERVAL = 3

class Robot:
    def __init__(self, name, shape):
        self.name = name
        self.shape = shape
        self.shape.generate_reference()
        self.points = self.shape.points.astype(np.float64)

    def generate_distorted_shape(self):
        shape = self.shape.__class__()
        shape.generate_reference()
        self.points = shape.points.astype(np.float64)

        self.points = self.thin_points(self.points, percent=10)
        self.points = self.add_noise(self.points, scale=0.3)
        self.points = self.rotate_points(self.points, angle=np.random.uniform(0, 360))
        self.points = self.shift_points(
            self.points, shift_x=np.random.uniform(-50, 50),
            shift_y=np.random.uniform(-50, 50)
        )

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

class Robots:
    def __init__(self):
        self.robots = [
            Glasha(),
            Sasha(),
            Masha(),
            Natasha()
        ]
        self.lock = Lock()  # Добавляем Lock
        self.is_running = False

    def connect_to_server(self):
        BaseManager.register('get_data_queue')
        BaseManager.register('get_command_queue')

        while True:
            try:
                manager = BaseManager(address=('127.0.0.1', 50000), authkey=b'abracadabra')
                manager.connect()
                self.data_queue = manager.get_data_queue()
                self.command_queue = manager.get_command_queue()
                self.shm = SharedMemory(name="robot_memory")
                break
            except (ConnectionRefusedError, FileNotFoundError):
                print("Ожидание подключения к серверу...")
                time.sleep(1)

    def run(self):
        self.connect_to_server()
        print("Подключение к серверу установлено.")

        try:
            while True:
                if not self.command_queue.empty():
                    command = self.command_queue.get()
                    if command == "start":
                        self.is_running = True
                    elif command == "stop":
                        self.is_running = False

                if self.is_running:
                    for robot in self.robots:
                        robot.generate_distorted_shape()
                        robot.send_data(self.data_queue, self.shm)
                    time.sleep(GENERATION_INTERVAL)
        except KeyboardInterrupt:
            print("Завершение работы Robots...")
        finally:
            self.shm.close()

class Glasha(Robot):
    def __init__(self):
        super().__init__("Глаша", Square(side_length=20))

class Sasha(Robot):
    def __init__(self):
        super().__init__("Саша", Triangle(side_length=20))

class Masha(Robot):
    def __init__(self):
        super().__init__("Маша", Circle(radius=10))

class Natasha(Robot):
    def __init__(self):
        super().__init__("Наташа", Parallelogram(base=16, height=10, skew=4))

if __name__ == "__main__":
    robots = Robots()
    robots.run()