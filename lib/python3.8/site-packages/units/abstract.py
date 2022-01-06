"""An abstract base class to define the interface for all units."""

from units.compatibility import compatible
from units.exception import IncompatibleUnitsError
from units.quantity import Quantity

class AbstractUnit(object):
    """Parent class/interface for units."""

    def __init__(self, is_si):
        self._si = is_si

    def __call__(self, quantity):
        """Overload the function call operator to convert units."""
        if not hasattr(quantity, 'unit'):
            return Quantity(quantity, self)
        elif compatible(self, quantity.unit):
            return Quantity(quantity.num *
                            quantity.unit.squeeze() /
                            self.squeeze(),
                            self)
        else:
            raise IncompatibleUnitsError()

    def canonical(self):
        """Return an immutable, comparable derivative of this unit"""
        raise NotImplementedError

    def invert(self):
        """Return (this unit)^-1."""
        raise NotImplementedError

    def is_si(self):
        """Whether it makes sense to give this unit an SI prefix."""
        return self._si

    def squeeze(self):
        """Return this unit's implicit quantity multiplier."""
        raise NotImplementedError

    def str_includes_multiplier(self):
        """Whether the string name of the unit already encapsulates
        the unit's multiplier."""
        raise NotImplementedError
