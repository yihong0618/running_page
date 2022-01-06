"""Exception classes for operations involving quantities and units."""

class IncompatibleUnitsError(Exception):
    """Raised when an invalid operation is performed on
        quantities with incompatible units."""
    pass
