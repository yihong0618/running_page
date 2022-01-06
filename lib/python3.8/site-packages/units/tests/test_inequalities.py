"""Test inequality comparisons between QUANTITIES, such as
quantity < quantity
quantity <= quantity
quantity > quantity
quantity >= quantity

...
each of these * {leaf units, the various composed units, named units},
and each combination therein
...

each of these * valid and invalid comparisons

...
"""

# Disable pylint and figleaf warnings about not being able to import pytest.
# pylint: disable=F0401,C0321
try:
    import pytest
except ImportError:
    pass
# pylint: enable=F0401,C0321

from units import unit
from units.composed_unit import ComposedUnit
from units.exception import IncompatibleUnitsError
from units.named_composed_unit import NamedComposedUnit
from units.quantity import Quantity
from units.registry import REGISTRY

CVEL = unit('m') / unit('s')

VEL = NamedComposedUnit("VEL", CVEL)

COMPATIBLE_QUANTITIES = [[Quantity(0, VEL), Quantity(1, VEL)],
                         [Quantity(0, CVEL), Quantity(1, CVEL)]]

ALL_UNITS = [unit('m') / unit('s'),
             unit('m') * unit('s'),
             unit('m'), unit('s'),
             NamedComposedUnit("Hz", ComposedUnit([], [unit('s')])),
             NamedComposedUnit("L",
                               ComposedUnit([unit('m')] * 3,
                                            [],
                                            multiplier=0.001))]

QUANTITIES = [[Quantity(n, u) for n in [0, 1]] for u in ALL_UNITS]
FLAT_QUANTITIES = sum(QUANTITIES, [])

def less_than(quant1, quant2):
    """Binary function to call the operator"""
    return quant1 < quant2

def less_than_or_eq(quant1, quant2):
    """Binary function to call the operator"""
    return quant1 <= quant2

def greater_than_or_eq(quant1, quant2):
    """Binary function to call the operator"""
    return quant1 >= quant2

def greater_than(quant1, quant2):
    """Binary function to call the operator"""
    return quant1 > quant2

def equal(quant1, quant2):
    """Binary function to call the operator"""
    return quant1 == quant2

def not_equal(quant1, quant2):
    """Binary function to call the operator"""
    return quant1 != quant2 and quant2 != quant1

def test_lt(quant1, quant2):
    """Binary function to assert the operator's result"""
    assert less_than(quant1, quant2)

def test_lte(quant1, quant2):
    """Binary function to assert the operator's result"""
    assert less_than_or_eq(quant1, quant2)

def test_gte(quant1, quant2):
    """Binary function to assert the operator's result"""
    assert greater_than_or_eq(quant2, quant1)

def test_gt(quant1, quant2):
    """Binary function to assert the operator's result"""
    assert greater_than(quant2, quant1)

def test_eq(quant1, quant2):
    """Binary function to assert the operator's result"""
    assert equal(quant1, quant2)

def test_ne(quant1, quant2):
    """Binary function to assert the operator's result"""
    assert not_equal(quant1, quant2)

def test_invalid_lt(quant1, quant2):
    """Binary function to assert the operator's exception"""
    # Disable warning about missing pytest.raises.
    # pylint: disable=E1101
    pytest.raises(IncompatibleUnitsError, less_than, quant1, quant2)
    # pylint: enable=E1101

def test_invalid_lte(quant1, quant2):
    """Binary function to assert the operator's exception"""
    # Disable warning about missing pytest.raises.
    # pylint: disable=E1101
    pytest.raises(IncompatibleUnitsError, less_than_or_eq, quant1, quant2)
    # pylint: enable=E1101

def test_invalid_gte(quant1, quant2):
    """Binary function to assert the operator's exception"""
    # Disable warning about missing pytest.raises.
    # pylint: disable=E1101
    pytest.raises(IncompatibleUnitsError,
                  greater_than_or_eq,
                  quant1,
                  quant2)
    # pylint: enable=E1101

def test_invalid_gt(quant1, quant2):
    """Binary function to assert the operator's exception"""
    # Disable warning about missing pytest.raises.
    # pylint: disable=E1101
    pytest.raises(IncompatibleUnitsError, greater_than, quant1, quant2)
    # pylint: enable=E1101

def test_invalid_eq(quant1, quant2):
    """Binary function to assert no exception raised."""
    assert not equal(quant1, quant2)


def pytest_generate_tests(metafunc):
    """Pytest test case generation."""

    if metafunc.function in [test_eq, test_gte, test_lte]:
        for quant in FLAT_QUANTITIES:
            metafunc.addcall(funcargs=dict(quant1=quant, quant2=quant))


    # Valid comparisons
    if metafunc.function == test_eq:
        metafunc.addcall(funcargs=dict(quant1=COMPATIBLE_QUANTITIES[0][0],
                                       quant2=COMPATIBLE_QUANTITIES[1][0]))
        metafunc.addcall(funcargs=dict(quant1=COMPATIBLE_QUANTITIES[1][0],
                                       quant2=COMPATIBLE_QUANTITIES[0][0]))


    if metafunc.function in [test_ne, test_invalid_eq]:
        for i, elem1 in enumerate(FLAT_QUANTITIES):
            for j in range(i + 1, len(FLAT_QUANTITIES)):
                elem2 = FLAT_QUANTITIES[j]
                metafunc.addcall(funcargs=dict(quant1=elem1, quant2=elem2))

    if metafunc.function in [test_lte, test_lt, test_gte, test_gt]:
        for q_group in QUANTITIES:
            lesser, greater = tuple(q_group)
            metafunc.addcall(funcargs=dict(quant1=lesser, quant2=greater))

        metafunc.addcall(funcargs=dict(quant1=COMPATIBLE_QUANTITIES[1][0],
                                       quant2=COMPATIBLE_QUANTITIES[0][1]))
        metafunc.addcall(funcargs=dict(quant1=COMPATIBLE_QUANTITIES[0][0],
                                       quant2=COMPATIBLE_QUANTITIES[1][1]))

    if metafunc.function in [test_invalid_gte,
                             test_invalid_gt,
                             test_invalid_lte,
                             test_invalid_lt]:
        for i, q_group1 in enumerate(QUANTITIES):
            for j in range(i + 1, len(QUANTITIES)):
                q_group2 = QUANTITIES[j]
                metafunc.addcall(funcargs=dict(quant1=q_group1[0],
                                               quant2=q_group2[0]))

def teardown_module(module):
    # Disable warning about not using module.
    # pylint: disable=W0613
    """Called after running all of the tests here."""
    REGISTRY.clear()
