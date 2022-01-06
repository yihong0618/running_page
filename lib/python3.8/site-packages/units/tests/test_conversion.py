"""Test conversion between units using the 'in' operator"""

from units import unit
from units.compatibility import within_epsilon
from units.predefined import define_units
from units.quantity import Quantity
from units.registry import REGISTRY

def test_valid_named_to_basic():
    """Named units should convert to their basic equivalents"""

    kilometre = unit('km')
    one_km_in_m = unit('m')(Quantity(1, kilometre))

    assert one_km_in_m == Quantity(1000, unit('m'))
    assert one_km_in_m.unit == unit('m')
    assert str(one_km_in_m) == '1000.00 m'

def test_valid_named_to_composed():
    """Named units should convert to the composed equivalents."""

    hertz = unit('Hz')
    one_hz_in_per_second = hertz.composed_unit(Quantity(1, hertz))

    assert one_hz_in_per_second == Quantity(1, hertz)
    assert str(one_hz_in_per_second) == '1.00 1 / s'

def test_valid_named_to_named():
    """Named units should convert to named equivalents."""

    gray = unit('Gy')
    sievert = unit('Sv')

    one_gray_in_sievert = sievert(Quantity(1, gray))
    assert one_gray_in_sievert == Quantity(1, gray)
    assert str(one_gray_in_sievert) == '1.00 Sv'

def test_valid_basic_to_basic():
    """Test idempotent conversion."""
    metre = unit('m')

    assert metre(Quantity(1, metre)) == Quantity(1, metre)

def test_valid_basic_to_composed():
    """Test conversion to composed units."""
    composed_cm = unit('cm').composed_unit

    one_m_in_cm = composed_cm(Quantity(1, unit('m')))

    assert one_m_in_cm == Quantity(1, unit('m'))

def test_valid_basic_to_named():
    """Basic units should convert into named equivalents."""
    metre = unit('m')
    thousand_m_in_km = unit('km')(Quantity(1000, metre))

    assert thousand_m_in_km == Quantity(1, unit('km'))
    assert thousand_m_in_km.unit == unit('km')
    assert str(thousand_m_in_km) == '1.00 km'

def test_valid_composed_to_basic():
    """Composed units should convert to basic equivalents."""
    metre = unit('m')

    hundred_cm_in_metres = metre(Quantity(100, unit('cm')))
    assert hundred_cm_in_metres == Quantity(1.0, metre)
    assert str(hundred_cm_in_metres) == '1.00 m'

def test_valid_composed_to_composed():
    """Valid composed units in terms of others."""
    metric_vel = unit('km') / unit('h')
    imp_vel = unit('mi') / unit('h')

    highway_kph = Quantity(100, metric_vel)
    highway_mph = Quantity(62.1371192237334, imp_vel)

    assert str(highway_kph) == '100.00 km / h'
    assert str(highway_mph) == '62.14 mi / h'

    assert within_epsilon(imp_vel(highway_kph),
                          highway_mph)

    assert str(imp_vel(highway_kph)) == '62.14 mi / h'

def test_valid_composed_to_named():
    """Composed units should convert to named equivalents."""
    hertz = unit('Hz')
    per_second = hertz.composed_unit

    one_hz = hertz(Quantity(1, per_second))

    assert one_hz == Quantity(1, hertz)
    assert str(one_hz) == '1.00 Hz'

def test_convert_from_num():
    """Nums should convert into quantities."""

    metre = unit('m')
    assert metre(3) == Quantity(3, metre)

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
