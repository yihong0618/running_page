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
        self, length_range: ValueRange, length: float, is_special: bool = False
    ) -> str:
        assert length_range.is_valid()

        color1 = (
            self.poster.colors["special"] if is_special else self.poster.colors["track"]
        )
        color2 = (
            self.poster.colors["special2"]
            if is_special
            else self.poster.colors["track2"]
        )

        diff = length_range.diameter()
        if diff == 0:
            return color1

        return interpolate_color(color1, color2, (length - length_range.lower()) / diff)
