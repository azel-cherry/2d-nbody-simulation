from typing import Tuple


Color = Tuple[int, int, int]

palette = {
    "white": (200, 220, 230),
    "pink": (224, 147, 136),
    "blue": (200, 190, 240),
    "green": (155, 209, 171),
    "yellow": (207, 178, 118),
    "bg": (40, 30, 50, 100)
}


def lerp(x: float, x0: float, x1: float, y0: float, y1: float) -> float:
    return y0 + (x - x0) * (y1 - y0) / (x1 - x0)


class Vect2:
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

    def __str__(self) -> str:
        return f"({self.x}, {self.y})"

    def normalized(self) -> 'Vect2':
        return self / self.mag()

    def perp(self) -> 'Vect2':
        return Vect2(-self.y, self.x)

    def mag(self) -> float:
        return (self.x**2 + self.y**2)**0.5

    def __add__(self, other: 'Vect2') -> 'Vect2':
        return Vect2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vect2') -> 'Vect2':
        return Vect2(self.x - other.x, self.y - other.y)

    def __mul__(self, k: float) -> 'Vect2':
        return Vect2(k * self.x, k * self.y)

    def __rmul__(self, k: float) -> 'Vect2':
        return Vect2(k * self.x, k * self.y)

    def __truediv__(self, k: float) -> 'Vect2':
        return Vect2(self.x / k, self.y / k)

    def to_tuple(self) -> tuple[float, float]:
        return self.x, self.y
