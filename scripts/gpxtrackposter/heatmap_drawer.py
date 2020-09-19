"""Draw a heatmap poster."""
# Copyright 2016-2019 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

import argparse
import logging
import math
import svgwrite
import s2sphere as s2

from .exceptions import ParameterError
from .poster import Poster
from .tracks_drawer import TracksDrawer
from .xy import XY
from .utils import project


log = logging.getLogger(__name__)


class HeatmapDrawer(TracksDrawer):
    """Draw a heatmap Poster based on the tracks.

    Attributes:
        center: Center of the heatmap.
        radius: Scale the heatmap so that a circle with radius (in KM) is visible.

    Methods:
        Create_args: Create arguments for heatmap.
        fetch_args: Get arguments passed.
        draw: Draw the heatmap based on the Poster's tracks.

    """

    def __init__(self, the_poster: Poster):
        super().__init__(the_poster)
        self._center = None
        self._radius = None

    def create_args(self, args_parser: argparse.ArgumentParser):
        group = args_parser.add_argument_group("Heatmap Type Options")
        group.add_argument(
            "--heatmap-center",
            dest="heatmap_center",
            metavar="LAT,LNG",
            type=str,
            help="Center of the heatmap (default: automatic).",
        )
        group.add_argument(
            "--heatmap-radius",
            dest="heatmap_radius",
            metavar="RADIUS_KM",
            type=float,
            help="Scale the heatmap such that at least a circle with radius=RADIUS_KM is visible "
            "(default: automatic).",
        )

    def fetch_args(self, args: argparse.Namespace):
        """Get arguments that were passed, and also perform basic validation on them.

        For example, make sure the center is an actual lat, lng , and make sure the radius is a
        positive number. Also, if radius is passed, then center must also be passed.

        Raises:
            ParameterError: Center was not a valid lat, lng coordinate, or radius was not positive.
        """
        self._center = None
        if args.heatmap_center:
            latlng_str = args.heatmap_center.split(",")
            if len(latlng_str) != 2:
                raise ParameterError(f"Not a valid LAT,LNG pair: {args.heatmap_center}")
            try:
                lat = float(latlng_str[0].strip())
                lng = float(latlng_str[1].strip())
            except ValueError as e:
                raise ParameterError(
                    f"Not a valid LAT,LNG pair: {args.heatmap_center}"
                ) from e
            if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                raise ParameterError(f"Not a valid LAT,LNG pair: {args.heatmap_center}")
            self._center = s2.LatLng.from_degrees(lat, lng)
        if args.heatmap_radius:
            if args.heatmap_radius <= 0:
                raise ParameterError(
                    f"Not a valid radius: {args.heatmap_radius} (must be > 0)"
                )
            if not args.heatmap_center:
                raise ParameterError("--heatmap-radius needs --heatmap-center")
            self._radius = args.heatmap_radius

    def _determine_bbox(self) -> s2.LatLngRect:
        if self._center:
            log.info(f"Forcing heatmap center to {self._center}")
            dlat, dlng = 0, 0
            if self._radius:
                er = 6378.1
                quarter = er * math.pi / 2
                dlat = 90 * self._radius / quarter
                scale = 1 / math.cos(self._center.lat().radians)
                dlng = scale * 90 * self._radius / quarter
            else:
                for tr in self.poster.tracks:
                    for line in tr.polylines:
                        for latlng in line:
                            d = abs(self._center.lat().degrees - latlng.lat().degrees)
                            dlat = max(dlat, d)
                            d = abs(self._center.lng().degrees - latlng.lng().degrees)
                            while d > 360:
                                d -= 360
                            if d > 180:
                                d = 360 - d
                            dlng = max(dlng, d)
            return s2.LatLngRect.from_center_size(
                self._center, s2.LatLng.from_degrees(2 * dlat, 2 * dlng)
            )

        tracks_bbox = s2.LatLngRect()
        for tr in self.poster.tracks:
            tracks_bbox = tracks_bbox.union(tr.bbox())
        return tracks_bbox

    def draw(self, dr: svgwrite.Drawing, size: XY, offset: XY):
        """Draw the heatmap based on tracks."""
        bbox = self._determine_bbox()
        for tr in self.poster.tracks:
            color = self.color(self.poster.length_range, tr.length, tr.special)
            for line in project(bbox, size, offset, tr.polylines):
                for opacity, width in [(0.1, 5.0), (0.2, 2.0), (1.0, 0.3)]:
                    dr.add(
                        dr.polyline(
                            points=line,
                            stroke=color,
                            stroke_opacity=opacity,
                            fill="none",
                            stroke_width=width,
                            stroke_linejoin="round",
                            stroke_linecap="round",
                        )
                    )
