import math

from numba import njit

PI = math.pi
PI2 = 2 * math.pi
RAD1 = PI / 180
DEG1 = 180 / PI


@njit(fastmath=True)
def normalize(angle):
    return angle % 360


class Angle:
    __slots__ = ('angle')

    def __init__(self, angle):
        self.angle = normalize(angle)

    def __repr__(self):
        return str(self.angle)

    def __add__(self, rhs):
        return Angle(self.angle + rhs)

    def __iadd__(self, rhs):
        return Angle(self.angle + rhs)

    def __radd__(self, lhs):
        return (self.angle + lhs)

    def __truediv__(self, rhs):
        return Angle(self.angle / rhs)

    def __mul__(self, rhs):
        return Angle(self.angle * rhs)

    def __sub__(self, rhs):
        return Angle(self.angle - rhs)

    def __isub__(self, rhs):
        return Angle(self.angle - rhs)

    def __rsub__(self, lhs):
        return (lhs - self.angle)

    def __neg__(self):
        return Angle(-self.angle)

    def __ge__(self, rhs):
        return self.angle >= rhs

    def __gt__(self, rhs):
        return self.angle > rhs

    def __lt__(self, rhs):
        return self.angle < rhs

    def __le__(self, rhs):
        return self.angle <= rhs

    def __int__(self):
        return int(self.angle)

    def __rshift__(self, rhs):
        return Angle(self.angle >> rhs)

    @property
    def cos(self):
        return math.cos(self.angle * RAD1)

    @property
    def sin(self):
        return math.sin(self.angle * RAD1)

    @property
    def tan(self):
        return math.tan(self.angle * RAD1)


