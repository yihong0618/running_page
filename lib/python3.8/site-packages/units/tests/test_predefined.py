"""Tests for predefined units."""

from units import unit
from units.predefined import define_units
from units.quantity import Quantity
from units.registry import REGISTRY

def test_volume():
    """Volume units should interchange correctly with cubed area units."""
    litres = unit('L')
    millilitres = unit('mL')
    centimetres = unit('cm')
    cm_cubed = centimetres * centimetres * centimetres

    assert Quantity(1, litres) == Quantity(1000, millilitres)
    assert Quantity(1, millilitres) == Quantity(1, cm_cubed)

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
