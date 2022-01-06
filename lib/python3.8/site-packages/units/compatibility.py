"""Check the compatibility of units."""

def compatible(unit1, unit2):
    """True iff quantities in the given units can be interchanged
    for some multiplier.
    """
    return unit1.canonical() == unit2.canonical()

def within_epsilon(quantity1, quantity2):
    """True iff the given quantities are close to each other within reason."""
    epsilon = 10 ** -9
    return abs(quantity1 - quantity2).num < epsilon
