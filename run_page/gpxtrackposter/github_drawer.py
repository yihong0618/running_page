import calendar
import datetime
import locale
import argparse

import svgwrite

from .exceptions import PosterError
from .poster import Poster
from .tracks_drawer import TracksDrawer
from .utils import format_float
from .xy import XY


class GithubDrawer(TracksDrawer):
    """Draw a github profile-like poster"""

    def __init__(self, the_poster: Poster):
        super().__init__(the_poster)
        self.empty_color = "#444444"

    def create_args(self, args_parser: argparse.ArgumentParser):
        """Add arguments specific to github drawer"""
        group = args_parser.add_argument_group("Github Type Options")
        group.add_argument(
            "--empty-data-color",
            dest="github_empty_data_color",
            metavar="COLOR",
            type=str,
            default=self.empty_color,
            help="Color for empty dates in github style poster (default: #444444)",
        )

    def fetch_args(self, args):
        self.empty_color = args.github_empty_data_color

    def draw(self, dr: svgwrite.Drawing, size: XY, offset: XY):
        if self.poster.tracks is None:
            raise PosterError("No tracks to draw")
        year_size = 200 * 4.0 / 80.0
        year_style = f"font-size:{year_size}px; font-family:Arial;"
        year_length_style = f"font-size:{110 * 3.0 / 80.0}px; font-family:Arial;"
        month_names_style = "font-size:2.5px; font-family:Arial"
        total_length_year_dict = self.poster.total_length_year_dict

        is_align_monday = self.poster.github_style == "align-monday"
        for year in range(self.poster.years.from_year, self.poster.years.to_year + 1)[
            ::-1
        ]:
            start_date_weekday, _ = calendar.monthrange(year, 1)
            github_rect_first_day = datetime.date(year, 1, 1)

            # default GitHub svg style:  the start day of each year always aligns with first day.
            github_rect_day = github_rect_first_day
            first_day_weekday = github_rect_first_day.weekday()

            if is_align_monday:
                # This is an earlier GitHub style: the start day of each year always aligns with Monday.
                # If you want to use this, please add the command-line argument "--github-style align-monday" .
                github_rect_day = github_rect_first_day + datetime.timedelta(
                    -start_date_weekday
                )
                first_day_weekday = 0

            year_length = total_length_year_dict.get(year, 0)
            year_length = format_float(self.poster.m2u(year_length))

            if str(year_length) == "0.0":
                continue
            try:
                month_names = [
                    locale.nl_langinfo(day)[:3]  # Get only first three letters
                    for day in [
                        locale.MON_1,
                        locale.MON_2,
                        locale.MON_3,
                        locale.MON_4,
                        locale.MON_5,
                        locale.MON_6,
                        locale.MON_7,
                        locale.MON_8,
                        locale.MON_9,
                        locale.MON_10,
                        locale.MON_11,
                        locale.MON_12,
                    ]
                ]
                # support windows or others doesn't support locale Name, by Hard code
            except Exception as e:
                print(str(e))
                month_names = [
                    "Jan",
                    "Feb",
                    "Mar",
                    "Apr",
                    "May",
                    "Jun",
                    "Jul",
                    "Aug",
                    "Sep",
                    "Oct",
                    "Nov",
                    "Dec",
                ]
            km_or_mi = "mi"
            if self.poster.units == "metric":
                km_or_mi = "km"
            dr.add(
                dr.text(
                    f"{year}",
                    insert=offset.tuple(),
                    fill=self.poster.colors["text"],
                    dominant_baseline="hanging",
                    style=year_style,
                )
            )

            dr.add(
                dr.text(
                    f"{year_length} {km_or_mi}",
                    insert=(offset.tuple()[0] + 165, offset.tuple()[1] + 5),
                    fill=self.poster.colors["text"],
                    dominant_baseline="hanging",
                    style=year_length_style,
                )
            )
            # add month name up to the poster one by one because of svg text auto trim the spaces.
            for num, name in enumerate(month_names):
                dr.add(
                    dr.text(
                        f"{name}",
                        insert=(offset.tuple()[0] + 15.5 * num, offset.tuple()[1] + 14),
                        fill=self.poster.colors["text"],
                        style=month_names_style,
                    )
                )

            rect_x = 10.0
            dom = (2.6, 2.6)

            # add every day of this year for 53 weeks and per week has 7 days
            for i in range(54):
                # the first day of the first week of the year may not Monday
                # so we need to skip some empty spaces
                if i == 0:
                    rect_y = offset.y + year_size + 2 + 3.5 * first_day_weekday
                else:
                    # the first day of the n week (n >1) must be  Monday
                    # so set first_day_weekday = 0
                    first_day_weekday = 0
                    rect_y = offset.y + year_size + 2
                for j in range(7 - first_day_weekday):
                    if int(github_rect_day.year) > year:
                        break
                    rect_y += 3.5
                    color = self.empty_color
                    date_title = str(github_rect_day)
                    if date_title in self.poster.tracks_by_date:
                        tracks = self.poster.tracks_by_date[date_title]
                        length = sum([t.length for t in tracks])
                        distance1 = self.poster.special_distance["special_distance"]
                        distance2 = self.poster.special_distance["special_distance2"]
                        has_special = distance1 < length / 1000 < distance2
                        color = self.color(
                            self.poster.length_range_by_date, length, has_special
                        )
                        if length / 1000 >= distance2:
                            color = self.poster.colors.get(
                                "special2"
                            ) or self.poster.colors.get("special")
                        str_length = format_float(self.poster.m2u(length))
                        date_title = f"{date_title} {str_length} {km_or_mi}"

                    rect = dr.rect((rect_x, rect_y), dom, fill=color)
                    rect.set_desc(title=date_title)
                    dr.add(rect)
                    github_rect_day += datetime.timedelta(1)
                rect_x += 3.5
            offset.y += 3.5 * 9 + year_size + 1.0
