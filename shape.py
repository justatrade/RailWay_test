from abc import ABC, abstractmethod

import matplotlib.pyplot as plt
import numpy as np

NUM_POINTS = 1000


class Shape(ABC):
    def __init__(self, name):
        self.name = name
        self.points = []

    @abstractmethod
    def generate_reference(self):
        pass

    def plot(self, filename=None):
        plt.figure(figsize=(6, 6))
        plt.scatter(self.points[:, 0], self.points[:, 1], label=self.name, s=10)
        plt.title(self.name)
        plt.grid(True)
        plt.axhline(0, color="black", linewidth=0.5)
        plt.axvline(0, color="black", linewidth=0.5)
        plt.xlabel("X")
        plt.ylabel("Y")
        plt.legend()
        plt.gca().set_aspect("equal", adjustable="box")
        if filename:
            plt.savefig(filename, dpi=200)
        else:
            plt.savefig(f"{self.name}.png", dpi=200)
        plt.close()


class Square(Shape):
    def __init__(self, side_length=20):
        super().__init__("square")
        self.side_length = side_length

    def generate_reference(self, num_points=NUM_POINTS):
        points_per_side = num_points // 4
        bottom_points = [
            (x, -self.side_length / 2)
            for x in np.linspace(
                -self.side_length / 2, self.side_length / 2, points_per_side
            )
        ]
        right_points = [
            (self.side_length / 2, y)
            for y in np.linspace(
                -self.side_length / 2, self.side_length / 2, points_per_side
            )
        ]
        top_points = [
            (x, self.side_length / 2)
            for x in np.linspace(
                self.side_length / 2, -self.side_length / 2, points_per_side
            )
        ]
        left_points = [
            (-self.side_length / 2, y)
            for y in np.linspace(
                self.side_length / 2, -self.side_length / 2, points_per_side
            )
        ]
        self.points = np.array(bottom_points + right_points + top_points + left_points)


class Triangle(Shape):
    def __init__(self, side_length=20):
        super().__init__("triangle")
        self.side_length = side_length

    def generate_reference(self, num_points=NUM_POINTS):
        points_per_side = num_points // 3
        height = np.sqrt(3) / 2 * self.side_length
        base_points = [
            (x, -height / 3)
            for x in np.linspace(
                -self.side_length / 2, self.side_length / 2, points_per_side
            )
        ]
        right_points = [
            (x, y)
            for x, y in zip(
                np.linspace(self.side_length / 2, 0, points_per_side),
                np.linspace(-height / 3, 2 * height / 3, points_per_side),
            )
        ]
        left_points = [
            (x, y)
            for x, y in zip(
                np.linspace(-self.side_length / 2, 0, points_per_side),
                np.linspace(-height / 3, 2 * height / 3, points_per_side),
            )
        ]
        self.points = np.array(base_points + right_points + left_points)


class Circle(Shape):
    def __init__(self, radius=10):
        super().__init__("circle")
        self.radius = radius

    def generate_reference(self, num_points=NUM_POINTS):
        angles = np.arange(0, 2 * np.pi, 2 * np.pi / num_points)
        self.points = np.array(
            [
                (self.radius * np.cos(angle), self.radius * np.sin(angle))
                for angle in angles
            ]
        )


class Parallelogram(Shape):
    def __init__(self, base=16, height=10, skew=4):
        super().__init__("parallelogram")
        self.base = base
        self.height = height
        self.skew = skew

    def generate_reference(self, num_points=NUM_POINTS):
        points_per_side = num_points // 4
        bottom_left = (-self.base - self.skew) / 2
        bottom_right = (self.base - self.skew) / 2
        top_left = -(self.base - self.skew) / 2
        top_right = (self.base + self.skew) / 2
        base_points = [
            (x, -self.height / 2)
            for x in np.linspace(bottom_left, bottom_right, points_per_side)
        ]
        top_points = [
            (x, self.height / 2)
            for x in np.linspace(top_left, top_right, points_per_side)
        ]
        left_points = [
            (bottom_left + self.skew * t, y)
            for t, y in zip(
                np.linspace(0, 1, points_per_side),
                np.linspace(-self.height / 2, self.height / 2, points_per_side),
            )
        ]
        right_points = [
            (bottom_right + self.skew * t, y)
            for t, y in zip(
                np.linspace(0, 1, points_per_side),
                np.linspace(-self.height / 2, self.height / 2, points_per_side),
            )
        ]
        self.points = np.array(base_points + top_points + left_points + right_points)


if __name__ == "__main__":
    shapes = [
        Square(side_length=20),
        Triangle(side_length=20),
        Circle(radius=10),
        Parallelogram(base=16, height=10, skew=4),
    ]
    for shape in shapes:
        shape.generate_reference()
        shape.plot()
