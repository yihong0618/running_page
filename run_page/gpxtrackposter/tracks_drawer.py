"""Contains the base class TracksDrawer, which other Drawers inherit from."""

# Copyright 2016-2019 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

import argparse

import svgwrite

from .poster import Poster
from .utils import interpolate_color
from .value_range import ValueRange
from .xy import XY


class TracksDrawer:
    """Base class that other drawer classes inherit from."""

    def __init__(self, the_poster: Poster):
        self.poster = the_poster

    def create_args(self, args_parser: argparse.ArgumentParser):
        pass

    def fetch_args(self, args):
        pass

    def draw(self, dr: svgwrite.Drawing, size: XY, offset: XY):
        pass

    def color(
        self, length_range: ValueRange, length: float
    ) -> str:
        assert length_range.is_valid()

        lower = length_range.lower()
        topper = length_range.upper()

        length -= lower
        d1 = self.poster.special_distance["special_distance"] * 1000 - lower
        d2 = self.poster.special_distance["special_distance2"] * 1000 - lower

        special = 1 if length > self.poster.special_distance["special_distance"] * 1000 else 0
        if length > self.poster.special_distance["special_distance2"] * 1000:
            special = 2

        if special == 1:
            return interpolate_color(self.poster.colors["special"], self.poster.colors["special2"], \
                              (length - d1) / (d2 - d1))
        elif special == 2:
            return interpolate_color(self.poster.colors["special2"], self.poster.colors["track2"], \
                              (length - d2) / (topper - d2) )
        else:
            return interpolate_color(self.poster.colors["track"], self.poster.colors["special"], \
                              length / d1)
