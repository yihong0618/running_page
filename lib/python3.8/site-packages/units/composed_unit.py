"""Composed units are quotients of products of other units
(but not other composed units.)
Utility methods here for working with abstract fractions."""

from units.abstract import AbstractUnit
from units.compatibility import compatible

def unbox(numer, denom, multiplier):
    """Attempts to convert the fractional unit represented by the parameters
    into another, simpler type. Returns the simpler unit or None if no
    simplification is possible.
    """

    if not denom and not numer:
        return multiplier

    if not denom and len(numer) == 1 and multiplier == 1:
        return numer[0]

    return None

def cancel(numer, denom):
    """Cancel out compatible units in the given numerator and denominator.
    Return a triple of the new numerator, the new denominator, the implied
    quantity multiplier that has been squeezed out."""
    multiplier = 1

    simple_numer = numer[:]
    simple_denom = denom[:]

    for nleaf in numer:
        remaining_denom = simple_denom[:]
        for dleaf in remaining_denom:
            if compatible(nleaf, dleaf):
                multiplier *= nleaf.squeeze() / dleaf.squeeze()
                simple_numer.remove(nleaf)
                simple_denom.remove(dleaf)
                break

    return (simple_numer, simple_denom, multiplier)

def squeeze(numer, denom):
    """Simplify.

    Some units imply quantities. For example, a kilometre implies a quantity
    of a thousand metres. This 'squeezes' out these implied quantities,
    returning a modified multiplier and simpler units."""

    result_numer = []
    result_denom = []
    result_mult = 1

    for unit in numer:
        while hasattr(unit, 'composed_unit'):
            unit = unit.composed_unit

        if hasattr(unit, 'numer'):
            result_numer += unit.numer
            result_denom += unit.denom
            result_mult *= unit.squeeze()
        else:
            result_numer += [unit]

    for unit in denom:
        while hasattr(unit, 'composed_unit'):
            unit = unit.composed_unit

        if hasattr(unit, 'numer'):
            result_denom += unit.numer
            result_numer += unit.denom
            result_mult /= unit.squeeze()
        else:
            result_denom += [unit]

    result_numer.sort()
    result_denom.sort()

    (simpler_numer, simpler_denom, cancellation_mult) = cancel(result_numer,
                                                               result_denom)

    result_mult *= cancellation_mult

    return (simpler_numer, simpler_denom, result_mult)


class ComposedUnit(AbstractUnit):
    """A ComposedUnit is a quotient of products of units."""

    def __new__(cls, numer, denom, multiplier=1):
        """Construct a unit that is a quotient of products of units,
        including an implicit quantity multiplier."""

        (squeezed_numer, squeezed_denom, squeezed_multiplier) = squeeze(numer,
                                                                        denom)

        multiplier *= squeezed_multiplier

        unboxed = unbox(squeezed_numer, squeezed_denom, multiplier)
        if unboxed:
            return unboxed

        return super(ComposedUnit, cls).__new__(cls)

    def __init__(self, numer, denom, multiplier=1):
        super(ComposedUnit, self).__init__(is_si=False)

        (self.numer, self.denom, self.multiplier) = squeeze(numer,
                                                            denom)
        self.multiplier *= multiplier

        self.orig_numer = numer
        self.orig_denom = denom
        self.orig_multiplier = multiplier

    def __reduce__(self):
        return (
            ComposedUnit,
            (self.orig_numer, self.orig_denom, self.orig_multiplier)
        )

    def str_includes_multiplier(self):
        return self.orig_multiplier == 1

    def __str__(self):
        if self.str_includes_multiplier():
            # Safe to use original units, so use them, because they are
            # more expected
            numers = self.orig_numer
            denoms = self.orig_denom
        else:
            numers = self.numer
            denoms = self.denom

        if self.denom:
            return ((' * '.join([str(x) for x in numers]) or '1') +
                     " / " +
                     ' * '.join([str(x) for x in denoms]))
        else:
            return ' * '.join([str(x) for x in numers])


    def __repr__(self):
        return ("ComposedUnit(" +
                ", ".join([repr(x) for x in [self.orig_numer,
                                             self.orig_denom,
                                             self.orig_multiplier]]) +
                ")")

    def canonical(self):
        """Return an immutable, comparable version of this unit,
        dropping any multiplier."""
        if self.denom or len(self.numer) != 1:
            return (tuple(self.numer), tuple(self.denom))
        else:
            return self.numer[0]

    def squeeze(self):
        """Return this unit's implicit quantity multiplier."""
        return self.multiplier

    def __mul__(self, other):
        if hasattr(other, "numer"):
            assert hasattr(other, "denom")
            return ComposedUnit(self.numer + other.numer,
                                self.denom + other.denom,
                                self.squeeze() * other.squeeze())
        else:
            return ComposedUnit(self.numer + [other],
                                self.denom,
                                self.squeeze())

    def invert(self):
        """Return (this unit)^-1."""
        return ComposedUnit(self.denom, self.numer, 1 / self.squeeze())

    def __truediv__(self, other):
        if hasattr(other, "invert"):
            return self * other.invert()
        else:
            return ComposedUnit(self.numer,
                                self.denom + [other],
                                self.squeeze() / other.squeeze())

    # Backwards-compatibility for <= Python 2.7
    __div__ = __truediv__

    def __pow__(self, exponent):
        return ComposedUnit(self.numer * exponent,
                            self.denom * exponent,
                            self.squeeze() ** exponent)
