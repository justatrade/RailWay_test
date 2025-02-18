import json
from abc import ABC, abstractmethod
import numpy as np


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
        side = np.linspace(-self.side_length / 2, self.side_length / 2, points_per_side)
        height = (np.sqrt(3) / 2 * self.side_length)
        self.points = np.array(
            [(x, -height / 2) for x in side] +
            [(self.side_length / 2, y) for y in np.linspace(-height / 2, height, points_per_side)] +
            [(-self.side_length / 2, y) for y in np.linspace(height, -height / 2, points_per_side)]
        )

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
        points_per_side = num_points // 4
        base = np.linspace(-self.base / 2, self.base / 2, points_per_side)
        self.points = np.array(
            [(x, -self.height / 2) for x in base] +
            [(x + self.skew, self.height / 2) for x in base[::-1]] +
            [(-self.base / 2 + self.skew, y) for y in np.linspace(-self.height / 2, self.height / 2, points_per_side)] +
            [(self.base / 2, y) for y in np.linspace(self.height / 2, -self.height / 2, points_per_side)]
        )

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