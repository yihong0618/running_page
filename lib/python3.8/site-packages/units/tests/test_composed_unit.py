"""Tests specific to composed units and their complexities."""

from units import unit
from units.composed_unit import ComposedUnit
from units.registry import REGISTRY

def test_unbox_to_num():
    """Test that composed units collapse properly to numbers."""
    assert ComposedUnit([unit('m')], [unit('m')], 8) == 8

def test_unbox_to_leaf():
    """Test that composed units collaple properly to leaf units."""
    assert ComposedUnit([unit('m')], []) == unit('m')

def teardown_module(module):
    # Disable warning about not using module.
    # pylint: disable=W0613
    """Called after running all of the tests here."""
    REGISTRY.clear()
