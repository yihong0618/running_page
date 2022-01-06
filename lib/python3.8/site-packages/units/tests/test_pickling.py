"""Test serialization and deserialization of quantities via pickle."""
from pickle import dumps, loads
from units import unit, named_unit
from units.compatibility import within_epsilon
from units.registry import REGISTRY

def test_unit_pickle():
    """Pickling is reversible on units themselves"""
    arbitrary = unit('arbitrary')
    unpickled = loads(dumps(arbitrary))
    assert id(arbitrary) == id(unpickled)
    assert arbitrary == unpickled

def test_leaf_pickle():
    """Pickling is reversible on quantities backed by leaf units"""
    arbitrary = unit('arbitrary')
    arbitrary_quantity = arbitrary(3.0)
    pickled = dumps(arbitrary_quantity)
    unpickled = loads(pickled)
    assert within_epsilon(arbitrary_quantity, unpickled)

def test_composed_pickle():
    """Pickling is reversible on quantities backed by composed units"""
    arbitrary = unit('arbitrary')
    arbitrary_quantity = arbitrary(3.0) * arbitrary(3.0)
    pickled = dumps(arbitrary_quantity)
    unpickled = loads(pickled)
    assert within_epsilon(arbitrary_quantity, unpickled)

def test_named_pickle():
    """Pickling is reversible on quantities backed by named units"""
    named = named_unit('S', 'N', 'D')
    arbitrary_quantity = named(3.0)
    pickled = dumps(arbitrary_quantity)
    unpickled = loads(pickled)
    assert within_epsilon(arbitrary_quantity, unpickled)

def teardown_module(module):
    # Disable warning about not using module.
    # pylint: disable=W0613
    """Called after running all of the tests here."""
    REGISTRY.clear()
