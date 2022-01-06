"""Quantities are numbers with units.
The combination of quantities is dependent on the compatibilities
of their units."""

from units.compatibility import compatible
from units.exception import IncompatibleUnitsError

class Quantity(object):
    """A number with a unit attached."""

    def __new__(cls, num, unit):
        if hasattr(unit, 'is_si'):
            return super(Quantity, cls).__new__(cls)
        else:
            return num * unit

    def __init__(self, num, unit):
        self._num, self._unit = num, unit

    def __getnewargs__(self):
        return (self._num, self._unit)

    def get_num(self):
        """The scalar number of this quantity"""
        return self._num
    num = property(get_num)

    def get_unit(self):
        """The standalone unit of this quantity"""
        return self._unit
    unit = property(get_unit)

    def _ensure_same_type(self, other):
        """docstring for ensure_same_type"""
        if not compatible(self.unit, other.unit):
            raise IncompatibleUnitsError()

    def __abs__(self):
        """Absolute value of a quantity."""
        if self.num < 0:
            return -self
        else:
            return self

    def __add__(self, other):
        self._ensure_same_type(other)
        return Quantity(self.num +
                        ((other.num * other.unit.squeeze()) /
                         self.unit.squeeze()),
                        self.unit)

    def __sub__(self, other):
        self._ensure_same_type(other)
        return Quantity(self.num -
                        ((other.num * other.unit.squeeze()) /
                         self.unit.squeeze()),
                        self.unit)

    def __mul__(self, other):
        if hasattr(other, 'num'):
            new_unit = self.unit * other.unit
            if hasattr(new_unit, "squeeze"):
                return Quantity(self.num * other.num, new_unit)
            else:
                # The unit multiplication unboxed
                return self.num * other.num * new_unit

        else:
            return Quantity(self.num * other, self.unit)

    def __rmul__(self, other):
        return self * other

    def __truediv__(self, other):
        if hasattr(other, 'num'):
            new_unit = self.unit / other.unit
            if hasattr(new_unit, "squeeze"):
                return Quantity(self.num / other.num, new_unit)
            else:
                # The unit division unboxed
                return self.num / other.num * new_unit

        else:
            return Quantity(self.num / other, self.unit)

    __floordiv__ = __truediv__
    # Backwards-compatibility for <= Python 2.7
    __div__ = __truediv__

    def __rtruediv__(self, other):
        return Quantity(other / self.num, self.unit.invert())

    # Backwards-compatibility for <= Python 2.7
    __rdiv__ = __rtruediv__

    def __eq__(self, other):
        if not compatible(self.unit, other.unit):
            return False
        else:
            return cmp(self, other) == 0

    def __ne__(self, other):
        return not self == other

    def __lt__(self, other):
        self._ensure_same_type(other)
        return self.num * self.unit.squeeze() < \
                other.num * other.unit.squeeze()

    def __cmp__(self, other):
        self._ensure_same_type(other)
        return cmp(self.num * self.unit.squeeze(),
                   other.num * other.unit.squeeze())

    def __le__(self, other):
        return self == other or self < other

    def __complex__(self):
        return complex(self.num)

    def __float__(self):
        return float(self.num)

    def __index__(self):
        return self.num

    def __hex__(self):
        """Backwards-compatibility with Python <= 2.7."""
        return hex(self.__index__())

    def __int__(self):
        return int(self.num)

    def __neg__(self):
        return Quantity(-self.num, self.unit)

    def __nonzero__(self):
        return bool(self.num)
    __bool__ = __nonzero__

    def __oct__(self):
        return oct(self.num)

    def __pos__(self):
        return self.num > 0

    def __pow__(self, exponent):
        return Quantity(self.num ** exponent, self.unit ** exponent)

    def __str__(self):
        num = self.num
        if not self.unit.str_includes_multiplier():
            num *= self.unit.squeeze()
        return '%0.2f %s' % (num, self.unit)

    def __repr__(self):
        return ("Quantity(" +
                ", ".join([repr(x) for x in [self.num, self.unit]]) +
                ")")

try:
    cmp
except NameError:
    def cmp(a, b):
        return (a > b) - (a < b)
