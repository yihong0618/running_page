"""Leaf units stand alone.
They are not compatible with any other kind of unit."""

from units.abstract import AbstractUnit
from units.registry import REGISTRY
from units.composed_unit import ComposedUnit

class LeafUnit(AbstractUnit):
    """Leaf units are not compatible with other units, but they can be
    composed to make other units."""

    def get_specifier(self):
        """Return the symbol of the unit."""
        return self._specifier
    specifier = property(get_specifier)

    def __new__(cls, specifier, is_si):
        # pylint: disable=W0613
        if specifier not in REGISTRY:
            REGISTRY[specifier] = super(LeafUnit, cls).__new__(cls)
        return REGISTRY[specifier]

    def __init__(self, specifier, is_si):
        """Make a new LeafUnit with the given unit specifier and
        SI-compatibility. A unit that is SI compatible can be prefixed,
        e.g. with k to mean 1000x.
        """
        super(LeafUnit, self).__init__(is_si)

        self._specifier = specifier

    def __reduce__(self):
        return (LeafUnit, (self._specifier, self.is_si()))

    __str__ = get_specifier

    def str_includes_multiplier(self):
        return True

    def __lt__(self, other):
        """In Python <= 2.7, objects without a __cmp__ method could be
        implicitly compared by their ids. It gave a consistent order within a
        single program run. The __lt__ method is now required for sorting, and
        here we just use the identity which should have the same effect.
        """
        return id(self) < id(other)

    def __repr__(self):
        return ("LeafUnit(" +
                ", ".join([repr(x) for x in [self.specifier,
                                             self.is_si()]]) +
                ")")

    def __mul__(self, other):
        if hasattr(other, "numer"):
            return other * self
        else:
            return ComposedUnit([self, other], [])

    def __truediv__(self, other):
        if hasattr(other, "invert"):
            return other.invert() * self
        else:
            return ComposedUnit([self], [other])

    # Backwards-compatibility for <= Python 2.7
    __div__ = __truediv__

    def invert(self):
        """Return (this unit)^-1"""
        return ComposedUnit([], [self])

    def canonical(self):
        """A LeafUnit is its own canonical form."""
        return self

    def squeeze(self):
        """A LeafUnit has no implicit quantity."""
        return 1

    def __pow__(self, exponent):
        return ComposedUnit([self] * exponent, [], 1)
