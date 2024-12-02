"""Represent a range of numerical values"""

# Copyright 2016-2019 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.


class ValueRange:
    """Represent a range of numerical values.

    Attributes:
        _lower: Lower bound of range.
        _upper: Upper bound of range.

    Methods:
        from_pair: Return a new ValueRange object from a pair of floats.
        is_valid: Return True if lower bound is set, else False.
        lower: Return lower bound.
        upper: Return upper bound.
        diameter: Return difference between upper and lower bounds if valid, else 0.
        contains: Returns True if the range contains value.
        extend: Adjust the range to include value.

    """

    def __init__(self):
        self._lower = None
        self._upper = None

    @classmethod
    def from_pair(cls, value1: float, value2: float) -> "ValueRange":
        r = cls()
        r.extend(value1)
        r.extend(value2)
        return r

    def is_valid(self) -> bool:
        return self._lower is not None

    def lower(self) -> float:
        return self._lower

    def upper(self) -> float:
        return self._upper

    def diameter(self) -> float:
        if self.is_valid():
            return self.upper() - self.lower()
        return 0

    def contains(self, value: float) -> bool:
        return self.is_valid() and (self.lower() <= value <= self.upper())

    def extend(self, value: float):
        if not self.is_valid():
            self._lower = value
            self._upper = value
        else:
            self._lower = min(self._lower, value)
            self._upper = max(self._upper, value)
