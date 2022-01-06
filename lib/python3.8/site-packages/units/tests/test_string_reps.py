"""Tests for string representations of Quantities and Units,
i.e. __repr__ and __str__"""

from units import unit
from units.predefined import define_units
from units.quantity import Quantity
from units.registry import REGISTRY

def test_quantity_repr():
    """Developer-friendly string representation of quantities."""
    assert repr(Quantity(1, unit('m'))) == "Quantity(1, LeafUnit('m', True))"

def test_quantity_str():
    """User-friendly string representation of quantities."""
    assert str(Quantity(1, unit('m'))) == "1.00 m"

def test_leaf_unit_repr():
    """Developer-friendly string representation of leaf units."""
    assert repr(unit('m')) == "LeafUnit('m', True)"

def test_leaf_unit_str():
    """User-friendly string representation of leaf units"""
    assert str(unit('s')) == "s"

def test_composed_unit_repr():
    """Developer-friendly string representation of composed units."""

    test_repr = (repr(unit('m') * unit('g') / unit('s')))

    # non-deterministic
    assert test_repr in ["ComposedUnit([LeafUnit('g', True), " +
                                       "LeafUnit('m', True)], " +
                         "[LeafUnit('s', True)], 1)",
                         "ComposedUnit([LeafUnit('m', True), " +
                                       "LeafUnit('g', True)], " +
                         "[LeafUnit('s', True)], 1)"]

def test_composed_unit_str():
    """User-friendly string representation of composed units."""
    test_str = (str(unit('m') * unit('g') / unit('s')))

    assert test_str in ["g * m / s", "m * g / s"] # non-deterministic.

def test_named_composed_unit_repr():
    """Developer-friendly string representation of named units."""
    assert (repr(unit('km')) == "NamedComposedUnit('km', " +
                                "ComposedUnit([LeafUnit('m', True)], " +
                                "[], 1000), False)")

def test_named_composed_unit_str():
    """User-friendly string representation of named units."""
    assert str(unit('mi')) == 'mi'

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
