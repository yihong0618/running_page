import math
import datetime

import svgwrite

from .exceptions import PosterError
from .tracks_drawer import TracksDrawer
from .utils import format_float
from .xy import XY


class MonthOfLifeDrawer(TracksDrawer):
    """Draw a Month of Life poster with 1000 months as circles"""

    def __init__(self, the_poster):
        super().__init__(the_poster)
        self.birth_year = None
        self.birth_month = None

    def create_args(self, args_parser):
        # Add argument for birth date
        args_parser.add_argument(
            "--birth",
            dest="birth",
            metavar="YYYY-MM",
            type=str,
            default=None,
            help="Birth date in format YYYY-MM",
        )

    def fetch_args(self, args):
        # Parse birth date
        if args.type == "monthoflife":
            if not args.birth:
                raise PosterError(
                    "Birth date parameter --birth is required in format YYYY-MM"
                )
            try:
                parts = args.birth.split("-")
                self.birth_year = int(parts[0])
                self.birth_month = int(parts[1])
                if not (1 <= self.birth_month <= 12):
                    raise ValueError
            except Exception:
                raise PosterError("Invalid birth date format, must be YYYY-MM")

    def draw(self, dr: svgwrite.Drawing, size: XY, offset: XY):
        if self.poster.tracks is None:
            raise PosterError("No tracks to draw")
        total_months = 1200
        # calculate grid: columns and rows
        cols = max(1, int(size.x / size.y * math.sqrt(total_months)))
        rows = math.ceil(total_months / cols)
        spacing_x = size.x / cols
        spacing_y = size.y / rows
        radius = min(spacing_x, spacing_y) / 2 * 0.85
        # prepare distance data by month
        month_distances = []  # in meters
        for idx in range(total_months):
            y = self.birth_year + (self.birth_month - 1 + idx) // 12
            m = (self.birth_month - 1 + idx) % 12 + 1
            # sum distances for this month
            dist = 0
            for tr in self.poster.tracks:
                dt = tr.start_time_local
                if dt.year == y and dt.month == m:
                    dist += tr.length
            month_distances.append((y, m, dist))
        # draw circles
        for idx, (y, m, dist) in enumerate(month_distances):
            x_idx = idx % cols
            y_idx = idx // cols
            cx = offset.x + spacing_x * x_idx + spacing_x / 2
            cy = offset.y + spacing_y * y_idx + spacing_y / 2

            current_date = datetime.datetime.now()
            month_date = datetime.datetime(y, m, 1)
            is_past = month_date < current_date

            color = "gray" if is_past else "#444444"
            age = (y - self.birth_year) + ((m - self.birth_month) / 12)
            title = f"{y}-{m:02d} ({int(age)} years old)"
            if dist > 0:
                # Set color based on special distance ranges and generate gradients or use special colors
                sd1 = self.poster.special_distance["special_distance"]
                sd2 = self.poster.special_distance["special_distance2"]
                dist_units = self.poster.m2u(dist)
                if sd1 < dist_units < sd2:
                    color = self.color(self.poster.length_range_by_date, dist, True)
                elif dist_units >= sd2:
                    color = self.poster.colors.get(
                        "special2"
                    ) or self.poster.colors.get("special")
                else:
                    color = self.color(self.poster.length_range_by_date, dist, False)
                val = format_float(dist_units)
                title = f"{title} {val} {self.poster.u()}"
            circle = dr.circle(center=(cx, cy), r=radius, fill=color)
            circle.set_desc(title=title)
            dr.add(circle)
