import json
from abc import ABC, abstractmethod
import numpy as np
import matplotlib.pyplot as plt

NUM_POINTS = 100


class Shape(ABC):
    def __init__(self, name):
        self.name = name
        self.points = []

    @abstractmethod
    def generate_reference(self):
        pass

    @abstractmethod
    def save_to_json(self):
        pass

    def print_json(self):
        data = {
            "shape": self.name,
            "points": self.points.tolist() if isinstance(self.points, np.ndarray) else self.points
        }
        print(json.dumps(data, indent=4))

    def plot(self, filename=None):
        """
        Отрисовывает фигуру с помощью matplotlib и сохраняет в файл.
        """
        plt.figure(figsize=(6, 6))  # Задаём квадратное изображение 6x6 дюймов
        plt.scatter(self.points[:, 0], self.points[:, 1], label=self.name, s=10)  # Уменьшаем размер точек (s=10)
        plt.title(self.name)
        plt.grid(True)
        plt.axhline(0, color='black', linewidth=0.5)
        plt.axvline(0, color='black', linewidth=0.5)
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.legend()

        # Устанавливаем одинаковый масштаб по осям X и Y
        plt.gca().set_aspect('equal', adjustable='box')

        if filename:
            plt.savefig(filename, dpi=100)  # Сохраняем с разрешением 100 dpi
        else:
            plt.savefig(f"{self.name}.png", dpi=100)  # Сохраняем с разрешением 100 dpi
        plt.close()


class Square(Shape):
    def __init__(self, side_length=10):
        super().__init__("square")
        self.side_length = side_length

    def generate_reference(self, num_points=NUM_POINTS):
        points_per_side = num_points // 4

        bottom_points = [(x, -self.side_length / 2) for x in
                         np.linspace(-self.side_length / 2, self.side_length / 2, points_per_side)]

        right_points = [
            (self.side_length / 2, y) for y in
            np.linspace(-self.side_length / 2, self.side_length / 2, points_per_side)
        ]
        top_points = [
            (x, self.side_length / 2) for x in
            np.linspace(self.side_length / 2, -self.side_length / 2, points_per_side)
        ]
        left_points = [
            (-self.side_length / 2, y) for y in
            np.linspace(self.side_length / 2, -self.side_length / 2, points_per_side)
        ]

        self.points = np.array(bottom_points + right_points + top_points + left_points)

    def save_to_json(self):
        self.print_json()


class Triangle(Shape):
    def __init__(self, side_length=10):
        super().__init__("triangle")
        self.side_length = side_length

    def generate_reference(self, num_points=NUM_POINTS):
        points_per_side = num_points // 3
        height = (np.sqrt(3) / 2 * self.side_length)

        base_points = [(x, -height / 3) for x in
                       np.linspace(-self.side_length / 2, self.side_length / 2, points_per_side)]

        right_points = [(x, y) for x, y in zip(
            np.linspace(self.side_length / 2, 0, points_per_side),
            np.linspace(-height / 3, 2 * height / 3, points_per_side)
        )]

        left_points = [(x, y) for x, y in zip(
            np.linspace(-self.side_length / 2, 0, points_per_side),
            np.linspace(-height / 3, 2 * height / 3, points_per_side)
        )]

        self.points = np.array(base_points + right_points + left_points)

    def save_to_json(self):
        self.print_json()


class Circle(Shape):
    def __init__(self, radius=5):
        super().__init__("circle")
        self.radius = radius

    def generate_reference(self, num_points=NUM_POINTS):
        angles = np.arange(0, 2 * np.pi, 2 * np.pi / num_points)
        self.points = np.array([(self.radius * np.cos(angle), self.radius * np.sin(angle)) for angle in angles])

    def save_to_json(self):
        self.print_json()


class Parallelogram(Shape):
    def __init__(self, base=10, height=5, skew=2):
        super().__init__("parallelogram")
        self.base = base
        self.height = height
        self.skew = skew

    def generate_reference(self, num_points=NUM_POINTS):
        # TODO: В идеале, рассчитывать количество точек пропорционально итоговой величине стороны
        points_per_side = num_points // 4

        bottom_left = (-self.base - self.skew) / 2
        bottom_right = (self.base - self.skew) / 2
        top_left = -(self.base - self.skew) / 2
        top_right = (self.base + self.skew) / 2
        base_points = [
            (x, -self.height / 2) for x in np.linspace(
                bottom_left, bottom_right, points_per_side
            )
        ]
        top_points = [
            (x, self.height / 2) for x in np.linspace(
                top_left, top_right, points_per_side
            )
        ]
        left_points = [(bottom_left + self.skew * t, y) for t, y in zip(
            np.linspace(0, 1, points_per_side),
            np.linspace(-self.height / 2, self.height / 2, points_per_side)
        )]
        right_points = [(bottom_right + self.skew * t, y) for t, y in zip(
            np.linspace(0, 1, points_per_side),
            np.linspace(-self.height / 2, self.height / 2, points_per_side)
        )]

        self.points = np.array(base_points + top_points + left_points + right_points)

    def save_to_json(self):
        self.print_json()


if __name__ == "__main__":
    shapes = [
        Square(side_length=10),
        Triangle(side_length=10),
        Circle(radius=5),
        Parallelogram(base=10, height=5, skew=2)
    ]

    for shape in shapes:
        shape.generate_reference()
        shape.save_to_json()
        shape.plot()
