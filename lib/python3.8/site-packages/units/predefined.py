"""Predefined units."""
from units.composed_unit import ComposedUnit
from units.leaf_unit import LeafUnit
from units.named_composed_unit import NamedComposedUnit
from units import unit, named_unit, scaled_unit

def define_units():
    """Define built-in units.

    >>> define_units()
    >>> unit('Hz').is_si()
    True
    >>> unit('m').is_si()
    True
    >>> unit('h').is_si()
    False
    """
    define_base_si_units()
    define_complex_si_units()
    define_time_units()
    define_volumes()
    define_imperial_units()
    define_astronomical_units()
    define_computer_units()
    define_ridiculous_units()

def define_base_si_units():
    """Define the basic SI units.

    >>> define_base_si_units()
    >>> unit('m').is_si()
    True
    """
    # meter, gram, second, ampere, kelvin, mole, candela
    for sym in ["m", "g", "s", "A", "K", "mol", "cd"]:
        LeafUnit(sym, is_si=True)

    scaled_unit('tonne', 'kg', 1000) # == 1Mg.

def define_complex_si_units():
    """Define SI units that are built on other SI units.

    >>> define_complex_si_units()
    >>> unit('Hz').is_si()
    True
    """
    for sym in ["rad", "sr"]:
        LeafUnit(sym, is_si=True)

    named_unit("Hz", [], ["s"]) #hertz
    named_unit("N", ["m", "kg"], ["s", "s"]) #Newton
    named_unit("Pa", ["N"], ["m", "m"]) #pascal
    named_unit("J", ["N", "m"], []) #Joule # Dangerous, 3J is a complex number
    named_unit("W", ["J"], ["s"]) # Watt
    named_unit("C", ["s", "A"], []) # Coulomb
    named_unit("V", ["W"], ["A"]) # Volt
    named_unit("F", ["C"], ["V"]) # Farad
    named_unit("Ohm", ["V"], ["A"])
    named_unit("S", ["A"], ["V"])   #Siemens
    named_unit("Wb", ["V", "s"], []) # Weber
    named_unit("T", ["Wb"], ["m", "m"]) # Tesla
    named_unit("H", ["Wb"], ["A"]) # Henry
    named_unit("lm", ["cd", "sr"], []) # lumen
    named_unit("lx", ["lm"], ["m", "m"]) #lux
    named_unit("Bq", [], ["s"]) # Becquerel
    named_unit("Gy", ["J"], ["kg"]) # Gray
    named_unit("Sv", ["J"], ["kg"]) # Sievert
    named_unit("kat", ["mol"], ["s"]) # Katal

def define_time_units():
    """Define some common time units.

    >>> from units.compatibility import within_epsilon
    >>> define_base_si_units()
    >>> define_time_units()
    >>> hour = unit('h')
    >>> hour.is_si()
    False
    >>> from units.quantity import Quantity
    >>> half_hour = Quantity(0.5, hour)
    >>> few_secs = Quantity(60.0, unit('s'))
    >>> sum = half_hour + few_secs

    >>> mins = unit('min')
    >>> thirty_one = Quantity(31, mins)
    >>> within_epsilon(thirty_one, sum)
    True
    """
    assert unit('s').is_si() # Ensure SI units already defined.

    scaled_unit('min', 's', 60.)
    scaled_unit('h', 'min', 60.)
    scaled_unit('day', 'h', 24.)
    scaled_unit('wk', 'day', 7.)

def define_volumes():
    """Define some common kitchen volumes.


    >>> from units.quantity import Quantity
    >>> define_base_si_units()
    >>> define_volumes()
    >>> one_litre = Quantity(520, unit('mL')) + Quantity(2, unit('cups'))
    >>> one_litre == Quantity(1, unit('L'))
    True
    """
    # Dangerous unit, 3L gives a long int.
    assert unit('m').is_si()
    NamedComposedUnit("L", unit("dm") ** 3, is_si=True)

    scaled_unit('tsp', 'mL', 5)
    scaled_unit('tbsp', 'mL', 15)
    scaled_unit('cups', 'mL', 240)

def define_imperial_units():
    """Define some common imperial units."""

    assert unit('m').is_si() # Ensure SI units already defined

    # scaled_unit measures
    scaled_unit('inch', 'cm', 2.54) # 'in' is a python keyword
    scaled_unit('ft', 'inch', 12) # foot
    scaled_unit('yd', 'ft', 3) # yard
    scaled_unit('fathom', 'ft', 6)
    scaled_unit('rd', 'yd', 5.5) # rod
    scaled_unit('fur', 'rd', 40) # furlong
    scaled_unit('mi', 'fur', 8) # mile
    scaled_unit('league', 'mi', 3)

    # nautical scaled_unit measures
    scaled_unit('NM', 'm', 1852) # Nautical mile
    scaled_unit('cable', 'NM', 0.1)

    # chain measure
    scaled_unit('li', 'inch', 7.92) # link
    scaled_unit('ch', 'li', 100) # chain

    # area measure
    NamedComposedUnit('acre',
                      ComposedUnit([unit('rd'), unit('rd')],
                                   [],
                                   160))

    # liquid measures
    NamedComposedUnit('pt',
                      ComposedUnit([unit('inch')] * 3,
                                   [],
                                   28.875)) # pint

    scaled_unit('gi', 'pt', 0.25) # gills
    scaled_unit('qt', 'pt', 2) # quarts
    scaled_unit('gal', 'qt', 4) # gallons

    scaled_unit('fl oz', 'pt', 1.0 / 16)
    scaled_unit('fl dr', 'fl oz', 1.0 / 8)
    scaled_unit('minim', 'fl dr', 1.0 / 60)

    # weight

    scaled_unit('oz', 'g', 28.375)
    scaled_unit('lb', 'oz', 16)
    scaled_unit('ton', 'lb', 2000)
    scaled_unit('grain', 'lb', 1.0 / 7000)
    scaled_unit('dr', 'lb', 1.0 / 256) # dram
    scaled_unit('cwt', 'lb', 100) # hundredweight

    scaled_unit('dwt', 'grain', 24) # pennyweight
    scaled_unit('oz t', 'dwt', 20) # ounce troy
    scaled_unit('lb t', 'oz t', 12) # pound troy

    # power
    scaled_unit('hpl', 'W', 746.9999) # mechanical
    scaled_unit('hpm', 'W', 735.49875) # metric horsepower
    scaled_unit('hpe', 'W', 746) # electric horsepower.

    # energy
    scaled_unit('BTU', 'J', 1055.056, is_si=True) # ISO BTU

def define_astronomical_units():
    """Define some astronomical units."""
    scaled_unit('ly', 'm', 9460730472580800) # light-year
    scaled_unit('AU', 'm', 149597870691) # Astronomical unit
    scaled_unit('pc', 'm', 3.08568025 * 10 ** 16, is_si=True) # parsec

def define_computer_units():
    """Define some units for technology.

    >>> define_units()
    >>> unit('GiB')(200) > unit('GB')(200) # bastard marketers
    True
    """

    NamedComposedUnit('flop', unit('operation') / unit('s'), is_si=True)
    scaled_unit('B', 'bit', 8, is_si=True)  # byte
    scaled_unit('KiB', 'B', 1024)
    scaled_unit('MiB', 'KiB', 1024)
    scaled_unit('GiB', 'MiB', 1024)
    scaled_unit('TiB', 'GiB', 1024)
    scaled_unit('PiB', 'TiB', 1024)

def define_ridiculous_units():
    """Define some silly units.

    >>> define_units()
    >>> from units.quantity import Quantity
    >>> Quantity(1, unit('keg')) / Quantity(1, unit('bottle'))
    140.8450704225352
    """

    scaled_unit('firkin', 'lb', 90)
    scaled_unit('fortnight', 'day', 14)

    scaled_unit('smoot', 'cm', 170)

    scaled_unit('hiroshima', 'J', 6.3 * 10 ** 13)

    scaled_unit('bottle', 'mL', 355)
    scaled_unit('keg', 'L', 50)
