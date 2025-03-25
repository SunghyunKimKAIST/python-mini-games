from math import sqrt, sin, cos, pi
from collections import namedtuple
import random as rd


def bound(x, lower, upper):
    return max(lower, min(x, upper))


class Vector(namedtuple('Vector', ['x', 'y'])):
    __slots__ = ()

    def rand():
        theta = rd.uniform(0, 2 * pi)
        return Vector(cos(theta), sin(theta))

    def rand_boundary(width, height):
        sign = rd.choice((0, 1))
        rng = rd.uniform(0, width + height)
        if rng < width:
            return Vector(rng, sign * height)
        else:
            return Vector(sign * width, rng - width)

    def __bool__(self):
        return bool(self.x or self.y)

    def __str__(self):
        return f'({self.x}, {self.y})'

    def __add__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x + other.x, self.y + other.y)
        else:
            return NotImplemented

    def __sub__(self, other):
        if isinstance(other, Vector):
            return Vector(self.x - other.x, self.y - other.y)
        else:
            return NotImplemented

    def __mul__(self, other):
        return Vector(self.x * other, self.y * other)

    """
    def __lt__(self, other):
        if isinstance(other, Vector):
            return abs(self) < abs(other)
        else:
            return NotImplemented"
    """

    def __abs__(self):
        return sqrt(self.x*self.x + self.y*self.y)

    def __mod__(self, other):
        if isinstance(other, tuple):
            if len(other) == 2:
                return Vector(self.x % other[0], self.y % other[1])
            if len(other) == 3:
                width, height, size = other
                return Vector((self.x + size) % (width + 2*size) - size,
                              (self.y + size) % (height + 2*size) - size)
        return NotImplemented

    def norm(self):
        _abs = abs(self)
        if not _abs:
            return Vector(0, 0)
        return Vector(self.x / _abs, self.y / _abs)

    def bbox(self, size):
        return self.x - size, self.y - size, self.x + size, self.y + size

    def isin(self, wl, hl, wh, hh):
        return wl <= self.x < wh and hl <= self.y < hh

    def bound(self, wl, hl, wh, hh):
        if self.isin(wl, hl, wh, hh):
            return self
        else:
            return Vector(bound(self.x, wl, wh), bound(self.y, hl, hh))

if __name__ == "__main__":
    print("vector.py")
