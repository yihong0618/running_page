"""Tests for addition and subtraction of Quantities"""

# Disable pylint and figleaf warnings about not being able to import py.test.
# pylint: disable=F0401,C0321
try: import pytest
except ImportError: pass
# pylint: enable=F0401,C0321

from units import unit
from units.compatibility import within_epsilon
from units.composed_unit import ComposedUnit
from units.exception import IncompatibleUnitsError
from units.named_composed_unit import NamedComposedUnit
from units.predefined import define_units
from units.quantity import Quantity
from units.registry import REGISTRY

def test_good_simple_add():
    """Two quantities with the same unit should add together."""

    assert (Quantity(2, unit('m')) +
            Quantity(2, unit('m')) ==
            Quantity(4, unit('m')))

def add_bad():
    """Incompatible leaf units should not add together."""

    metres = Quantity(2, unit('m'))
    seconds = Quantity(2, unit('s'))
    return metres + seconds

def test_bad_simple_add():
    """Two quantities with different units should not add together."""
    # Disable warning about missing pytest.raises.
    # pylint: disable=E1101
    pytest.raises(IncompatibleUnitsError, add_bad)
    # pylint: enable=E1101

def test_good_simple_sub():
    """Should be able to subtract compatible Quantities."""

    assert (Quantity(4, unit('m')) -
            Quantity(2, unit('m')) ==
            Quantity(2, unit('m')))

def subtract_bad():
    """Incompatible leaf units should not subtract from one another."""

    metres = Quantity(2, unit('m'))
    seconds = Quantity(2, unit('s'))
    return metres - seconds

def test_bad_simple_sub():
    """Two quantities with different units should not allow subtraction."""
    # Disable warning about missing pytest.raises.
    # pylint: disable=E1101
    pytest.raises(IncompatibleUnitsError, subtract_bad)
    # pylint: enable=E1101

def test_good_composed_add():
    """Two quantities with the same complex units should add together"""

    assert (Quantity(2, unit('m') /
                        unit('s')) +
            Quantity(3, unit('m') /
                        unit('s')) ==
            Quantity(5, unit('m') /
                        unit('s')))

def test_good_named_add():
    """Two quantities with the same named complex units should add together"""

    furlong = NamedComposedUnit('furlong',
                                ComposedUnit([unit('m')],
                                             [],
                                             multiplier=201.168),
                                is_si=False)

    assert (Quantity(2, furlong) +
            Quantity(2, furlong) ==
            Quantity(4, furlong))


def test_good_mixed_add():
    """Two quantities with the same units should add together
    even if one is named"""

    gray = NamedComposedUnit('gray',
                             ComposedUnit([unit('J'),
                                           unit('kg')],
                                          []),
                             is_si=True)

    sievert = ComposedUnit([unit('J'),
                            unit('kg')],
                           [])

    assert(Quantity(2, gray) +
           Quantity(2, sievert) ==
           Quantity(4, gray))

    assert(Quantity(2, sievert) +
           Quantity(2, gray) ==
           Quantity(4, sievert))

    assert Quantity(2, sievert) == Quantity(2, gray)

def test_good_add_w_mult():
    """Two quantities with same units should add together when
    they have the same multiplier"""


    moon = ComposedUnit([unit('day')],
                        [],
                        multiplier=28)
    lunar_cycle = ComposedUnit([unit('day')],
                               [],
                               multiplier=28)

    assert(Quantity(1, moon) +
           Quantity(1, lunar_cycle) ==
           Quantity(2, moon))

    assert(Quantity(1, lunar_cycle) +
           Quantity(1, moon) ==
           Quantity(2, lunar_cycle))

    assert Quantity(1, moon) == Quantity(1, lunar_cycle)

def test_good_add_w_mults():
    """Two quantities with compatible units should add together
    even when they have different multipliers"""


    mile = ComposedUnit([unit('m')],
                        [],
                        multiplier=1609.344)
    kilometre = ComposedUnit([unit('m')],
                             [],
                             multiplier=1000)

    m_on_left = Quantity(1, mile) + Quantity(1, kilometre)
    km_on_left = Quantity(1, kilometre) + Quantity(1, mile)
    manual_sum = Quantity(2609.344, unit('m'))

    assert within_epsilon(m_on_left, km_on_left)
    assert within_epsilon(km_on_left, m_on_left)
    assert within_epsilon(manual_sum, m_on_left)
    assert within_epsilon(manual_sum, km_on_left)
    assert within_epsilon(m_on_left, manual_sum)
    assert within_epsilon(km_on_left, manual_sum)

def test_good_named_add_w_mults():
    """Two quantities with compatible but differently-named and
    differently-multiplied units should add together."""

    mile = unit('mi')
    kilometre = unit('km')

    assert within_epsilon(Quantity(1, mile) + Quantity(1, kilometre),
                          Quantity(1, kilometre) + Quantity(1, mile))
    assert within_epsilon(Quantity(2609.344, unit('m')),
                          Quantity(1, kilometre) + Quantity(1, mile))




def test_good_named_add_w_mult():
    """A quantity with a named composed unit that carries a multiplier
    should add to a composed unit that has a multiplier"""

    mile = unit('mi').composed_unit
    kilometre = unit('km')

    assert within_epsilon(Quantity(1, mile) + Quantity(1, kilometre),
                          Quantity(1, kilometre) + Quantity(1, mile))
    assert within_epsilon(Quantity(2609.344, unit('m')),
                          Quantity(1, kilometre) + Quantity(1, mile))

def test_good_composed_sub():
    """Two quantities with the same complex units should sub together"""

    assert (Quantity(5, unit('m') /
                        unit('s')) -
            Quantity(3, unit('m') /
                        unit('s')) ==
            Quantity(2, unit('m') /
                        unit('s')))

def test_good_named_sub():
    """Two quantities with the same named complex units should sub together"""

    furlong = unit('fur')

    assert (Quantity(4, furlong) -
            Quantity(2, furlong) ==
            Quantity(2, furlong))


def test_good_mixed_sub():
    """Two quantities with the same units should sub together
    even if one is named"""

    gray = unit('Gy')

    sievert = unit('Sv').composed_unit

    assert(Quantity(4, gray) -
           Quantity(2, sievert) ==
           Quantity(2, gray))

    assert(Quantity(4, sievert) -
           Quantity(2, gray) ==
           Quantity(2, sievert))

    assert Quantity(2, sievert) == Quantity(2, gray)

def test_good_sub_w_mult():
    """Two quantities with same units should sub together when
    they have the same multiplier"""


    moon = ComposedUnit([unit('day')],
                        [],
                        multiplier=28)
    lunar_cycle = ComposedUnit([unit('day')],
                               [],
                               multiplier=28)

    assert(Quantity(2, moon) -
           Quantity(1, lunar_cycle) ==
           Quantity(1, moon))

    assert(Quantity(2, lunar_cycle) -
           Quantity(1, moon) ==
           Quantity(1, lunar_cycle))

    assert Quantity(1, moon) == Quantity(1, lunar_cycle)

def test_good_sub_w_mults():
    """Two quantities with compatible units should sub together
    even when they have different multipliers"""

    mile = unit('mi').composed_unit
    kilometre = unit('km').composed_unit

    m_on_left = Quantity(1, mile) - Quantity(1, kilometre)
    km_on_left = Quantity(1, kilometre) - Quantity(1, mile)
    m_on_left_diff = Quantity(609.344, unit('m'))
    km_on_left_diff = Quantity(-609.344, unit('m'))

    assert within_epsilon(m_on_left, m_on_left_diff)
    assert within_epsilon(km_on_left, km_on_left_diff)
    assert within_epsilon(m_on_left_diff, -km_on_left_diff)

def test_good_named_sub_w_mults():
    """Two quantities with compatible but differently-named and
    differently-multiplied units should sub together."""

    mile = unit('mi')
    kilometre = unit('km')

    assert within_epsilon(Quantity(1, mile) - Quantity(1, kilometre),
                          Quantity(609.344, unit('m')))

    assert within_epsilon(Quantity(1, kilometre) - Quantity(1, mile),
                          Quantity(-609.344, unit('m')))

def test_good_named_sub_w_mult():
    """A quantity with a named composed unit that carries a multiplier
    should sub to a composed unit that has a multiplier"""

    mile = unit('mi').composed_unit
    kilometre = unit('km')

    assert within_epsilon(Quantity(1, mile) - Quantity(1, kilometre),
                          Quantity(609.344, unit('m')))

    assert within_epsilon(Quantity(1, kilometre) - Quantity(1, mile),
                          Quantity(-609.344, unit('m')))

def setup_module(module):
    # Disable warning about not using module.
    # pylint: disable=W0613
    """Called by py.test before running any of the tests here."""
    define_units()

def teardown_module(module):
    # Disable warning about not using module.
    # pylint: disable=W0613
    """Called after running all of the tests here."""
    REGISTRY.clear()
