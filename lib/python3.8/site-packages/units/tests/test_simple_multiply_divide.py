"""Tests of simple multiplication and division of units and quantities."""

from units import unit
from units.quantity import Quantity
from units.named_composed_unit import NamedComposedUnit
from units.registry import REGISTRY

def test_simple_multiply():
    """Simple multiplication of units."""
    assert unit('m') * unit('s') / unit('s') == unit('m')

def test_simple_divide():
    """Simple division of units."""
    assert unit('m') / unit('s') * unit('s') == unit('m')

def test_commutative_multiply():
    """Commutative multiplication of units"""
    assert unit('m') * unit('s') / unit('m') == unit('s')

def test_simple_multiply_quantity():
    """Simple multiplication of quantities"""
    assert (Quantity(2, unit('m')) *
            Quantity(2, unit('s')) ==
            Quantity(4, unit('m') * unit('s')))

    assert (Quantity(2, unit('s')) *
            Quantity(2, unit('m')) ==
            Quantity(4, unit('m') * unit('s')))

def test_simple_divide_quantity():
    """Simple division of quantities"""
    assert (Quantity(8, unit('m')) /
            Quantity(2, unit('s')) ==
            Quantity(4, unit('m') / unit('s')))

def test_multiply_scalar():
    """Quantities * scalars"""
    assert (Quantity(8, unit('m')) * 2 ==
            Quantity(16, unit('m')))

def test_rmultiply_scalar():
    """Scalars * quantities"""
    assert (2 * Quantity(8, unit('m')) ==
            Quantity(16, unit('m')))

def test_divide_scalar():
    """Quantities / scalars"""
    assert (Quantity(8, unit('m')) / 2 ==
            Quantity(4, unit('m')))

def test_rdivide_scalar():
    """Scalars / quantities"""
    assert (4 / Quantity(2, unit('m')) ==
            Quantity(2, unit('m').invert()))

def test_multiply_composed_scalar():
    """Composed quantities * scalars"""
    m_per_s = unit('m') / unit('s')

    assert (Quantity(8, m_per_s) * 2 ==
            Quantity(16, m_per_s))

def test_rmultiply_composed_scalar():
    """Scalars * Composed quantities"""
    m_per_s = unit('m') / unit('s')

    assert (2 * Quantity(8, m_per_s) ==
            Quantity(16, m_per_s))

def test_divide_composed_scalar():
    """Composed quantities / scalars"""
    m_per_s = unit('m') / unit('s')

    assert (Quantity(8, m_per_s) / 2 ==
            Quantity(4, m_per_s))

def test_rdivide_composed_scalar():
    """Scalars / composed quantities"""
    m_per_s = unit('m') / unit('s')

    assert (4 / Quantity(2, m_per_s) ==
            Quantity(2, unit('s') / unit('m')))

def test_multiply_named_scalar():
    """Named quantities * scalars"""
    m_per_s = NamedComposedUnit('vel',
                                unit('m') / unit('s'))

    assert (Quantity(8, m_per_s) * 2 ==
            Quantity(16, m_per_s))

def test_rmultiply_named_scalar():
    """Scalars * Named quantities"""
    m_per_s = NamedComposedUnit('vel',
                                unit('m') / unit('s'))

    assert (2 * Quantity(8, m_per_s) ==
            Quantity(16, m_per_s))

def test_divide_named_scalar():
    """Named quantities / scalars"""
    m_per_s = NamedComposedUnit('vel',
                                unit('m') / unit('s'))

    assert (Quantity(8, m_per_s) / 2 ==
            Quantity(4, m_per_s))

def test_rdivide_named_scalar():
    """Scalars / Named quantities"""
    m_per_s = NamedComposedUnit('vel',
                                unit('m') / unit('s'))

    assert (4 / Quantity(2, m_per_s) ==
            Quantity(2, unit('s') / unit('m')))

def test_unboxing_multiply():
    """Multiplication causing an unboxing to number"""
    m_per_s = unit('m') / unit('s')
    s_per_m = unit('s') / unit('m')
    assert m_per_s(5) * s_per_m(5) == 25

def test_unboxing_divide():
    """Division causing an unboxing to number"""
    metre = unit('m')
    assert metre(10) / metre(5) == 2

def teardown_module(module):
    # Disable warning about not using module.
    # pylint: disable=W0613
    """Called after running all of the tests here."""
    REGISTRY.clear()
