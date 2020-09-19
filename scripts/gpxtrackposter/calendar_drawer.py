"""Draw a calendar poster."""
# Copyright 2016-2019 Florian Pigorsch & Contributors. All rights reserved.
#
# Use of this source code is governed by a MIT-style
# license that can be found in the LICENSE file.

import calendar
import datetime
import locale
import svgwrite

from .utils import compute_grid, format_float
from .exceptions import PosterError
from .poster import Poster
from .tracks_drawer import TracksDrawer
from .xy import XY


class CalendarDrawer(TracksDrawer):
    """Draw a calendar poster."""

    def __init__(self, the_poster: Poster):
        super().__init__(the_poster)

    def draw(self, dr: svgwrite.Drawing, size: XY, offset: XY):
        """Iterate through the Poster's years, creating a calendar for each."""
        if self.poster.tracks is None:
            raise PosterError("No tracks to draw.")
        years = self.poster.years.count()
        _, counts = compute_grid(years, size)
        if counts is None:
            raise PosterError("Unable to compute grid.")
        count_x, count_y = counts[0], counts[1]
        x, y = 0, 0
        cell_size = size * XY(1 / count_x, 1 / count_y)
        margin = XY(4, 8)
        if count_x <= 1:
            margin.x = 0
        if count_y <= 1:
            margin.y = 0
        sub_size = cell_size - 2 * margin

        for year in range(self.poster.years.from_year, self.poster.years.to_year + 1):
            self._draw(dr, sub_size, offset + margin + cell_size * XY(x, y), year)
            x += 1
            if x >= count_x:
                x = 0
                y += 1

    def _draw(self, dr: svgwrite.Drawing, size: XY, offset: XY, year: int):
        min_size = min(size.x, size.y)
        year_size = min_size * 4.0 / 80.0
        year_style = f"font-size:{year_size}px; font-family:Arial;"
        month_style = f"font-size:{min_size * 3.0 / 80.0}px; font-family:Arial;"
        day_style = f"dominant-baseline: central; font-size:{min_size * 1.0 / 80.0}px; font-family:Arial;"
        day_length_style = f"font-size:{min_size * 1.0 / 80.0}px; font-family:Arial;"

        dr.add(
            dr.text(
                f"{year}",
                insert=offset.tuple(),
                fill=self.poster.colors["text"],
                alignment_baseline="hanging",
                style=year_style,
            )
        )
        offset.y += year_size
        size.y -= year_size
        count_x = 31
        for month in range(1, 13):
            date = datetime.date(year, month, 1)
            (_, last_day) = calendar.monthrange(year, month)
            count_x = max(count_x, date.weekday() + last_day)

        cell_size = min(size.x / count_x, size.y / 36)
        spacing = XY(
            (size.x - cell_size * count_x) / (count_x - 1),
            (size.y - cell_size * 3 * 12) / 11,
        )

        # chinese weekday key number is the third.
        keyword_num = 0
        if locale.getlocale()[0] == "zh_CN":
            keyword_num = 2
        # first character of localized day names, starting with Monday.
        dow = [
            locale.nl_langinfo(day)[keyword_num].upper()
            for day in [
                locale.DAY_2,
                locale.DAY_3,
                locale.DAY_4,
                locale.DAY_5,
                locale.DAY_6,
                locale.DAY_7,
                locale.DAY_1,
            ]
        ]

        for month in range(1, 13):
            date = datetime.date(year, month, 1)
            y = month - 1
            y_pos = offset.y + (y * 3 + 1) * cell_size + y * spacing.y
            dr.add(
                dr.text(
                    date.strftime("%B"),
                    insert=(offset.x, y_pos - 2),
                    fill=self.poster.colors["text"],
                    alignment_baseline="hanging",
                    style=month_style,
                )
            )

            day_offset = date.weekday()
            while date.month == month:
                x = date.day - 1
                x_pos = offset.x + (day_offset + x) * cell_size + x * spacing.x
                pos = (x_pos + 0.05 * cell_size, y_pos + 1.15 * cell_size)
                dim = (cell_size * 0.9, cell_size * 0.9)
                text_date = date.strftime("%Y-%m-%d")
                if text_date in self.poster.tracks_by_date:
                    tracks = self.poster.tracks_by_date[text_date]
                    length = sum([t.length for t in tracks])
                    has_special = len([t for t in tracks if t.special]) > 0
                    color = self.color(
                        self.poster.length_range_by_date, length, has_special
                    )
                    dr.add(dr.rect(pos, dim, fill=color))
                    dr.add(
                        dr.text(
                            format_float(self.poster.m2u(length)),
                            insert=(
                                pos[0] + cell_size / 2,
                                pos[1] + cell_size + cell_size / 2,
                            ),
                            text_anchor="middle",
                            style=day_length_style,
                            fill=self.poster.colors["text"],
                        )
                    )
                else:
                    dr.add(dr.rect(pos, dim, fill="#444444"))

                dr.add(
                    dr.text(
                        dow[date.weekday()],
                        insert=(
                            offset.x + (day_offset + x) * cell_size + cell_size / 2,
                            pos[1] + cell_size / 2,
                        ),
                        text_anchor="middle",
                        alignment_baseline="middle",
                        style=day_style,
                    )
                )
                date += datetime.timedelta(1)
