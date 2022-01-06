"""Assign arbitrary new symbols to composed units."""

from units.abstract import AbstractUnit
from units.composed_unit import ComposedUnit
from units.registry import REGISTRY

class NamedComposedUnit(AbstractUnit):
    """A NamedComposedUnit is a composed unit with its own symbol."""

    def get_name(self):
        """The label for the composed unit"""
        return self._name
    name = property(get_name)

    def get_composed_unit(self):
        """The labeled composed unit"""
        return self._composed_unit
    composed_unit = property(get_composed_unit)

    def __new__(cls,
                name,
                composed_unit,
                is_si=False):
        """Give a composed unit a new symbol."""
        # pylint: disable=W0613

        if name not in REGISTRY:
            REGISTRY[name] = super(NamedComposedUnit,
                                   cls).__new__(cls)
        return REGISTRY[name]

    def __init__(self, name, composed_unit, is_si=False):
        super(NamedComposedUnit, self).__init__(is_si)
        self._name = name
        self._composed_unit = composed_unit

    def __reduce__(self):
        return (
            NamedComposedUnit,
            (self._name, self._composed_unit, self.is_si())
        )

    def invert(self):
        """Return the invert of the underlying composed unit."""
        return self.composed_unit.invert()

    def canonical(self):
        """Return the canonical of the underlying composed unit."""
        return self.composed_unit.canonical()

    def squeeze(self):
        """Return the squeeze of the underlying composed unit."""
        return self.composed_unit.squeeze()

    def __mul__(self, other):
        return ComposedUnit([self, other], [])

    def __truediv__(self, other):
        return ComposedUnit([self], [other])

    # Backwards-compatibility for <= Python 2.7
    __div__ = __truediv__

    __str__ = get_name

    def str_includes_multiplier(self):
        return True

    def __repr__(self):
        return ("NamedComposedUnit(" +
                ", ".join([repr(x) for x in [self.name,
                                             self.composed_unit,
                                             self.is_si()]])+
                ")")

    def __eq__(self, other):
        return self.composed_unit == other or other == self.composed_unit

    def __pow__(self, exponent):
        return self.composed_unit ** exponent
