"""Create a poster from track data."""

import gettext
import locale
from collections import defaultdict
from datetime import datetime

import pytz
import svgwrite

from .utils import format_float
from .value_range import ValueRange
from .xy import XY
from .year_range import YearRange


class Poster:
    """Create a poster from track data.

    Attributes:
        athlete: Name of athlete to be displayed on poster.
        title: Title of poster.
        tracks_by_date: Tracks organized temporally if needed.
        tracks: List of tracks to be used in the poster.
        length_range: Range of lengths of tracks in poster.
        length_range_by_date: Range of lengths organized temporally.
        units: Length units to be used in poster.
        colors: Colors for various components of the poster.
        width: Poster width.
        height: Poster height.
        years: Years included in the poster.
        tracks_drawer: drawer used to draw the poster.

    Methods:
        set_tracks: Associate the Poster with a set of tracks
        draw: Draw the tracks on the poster.
        m2u: Convert meters to kilometers or miles based on units
        u: Return distance unit (km or mi)
    """

    def __init__(self):
        self.athlete = None
        self.title = None
        self.tracks_by_date = {}
        self.tracks = []
        self.length_range = None
        self.length_range_by_date = None
        self.units = "metric"
        self.colors = {
            "background": "#222222",
            "text": "#FFFFFF",
            "special": "#FFFF00",
            "track": "#4DD2FF",
        }
        self.special_distance = {"special_distance": 10, "special_distance2": 20}
        self.width = 200
        self.height = 300
        self.years = None
        self.tracks_drawer = None
        self.trans = None
        self.set_language(None)
        self.tc_offset = datetime.now(pytz.timezone("Asia/Shanghai")).utcoffset()
        self.github_style = "align-firstday"

    def set_language(self, language):
        if language:
            try:
                locale.setlocale(locale.LC_ALL, f"{language}.utf8")
            except locale.Error as e:
                print(f'Cannot set locale to "{language}": {e}')
                language = None
                pass

        # Fall-back to NullTranslations, if the specified language translation cannot be found.
        if language:
            lang = gettext.translation(
                "gpxposter", localedir="locale", languages=[language], fallback=True
            )
        else:
            lang = gettext.NullTranslations()
        self.trans = lang.gettext

    def set_tracks(self, tracks):
        """Associate the set of tracks with this poster.

        In addition to setting self.tracks, also compute the necessary attributes for the Poster
        based on this set of tracks.
        """
        self.tracks = tracks
        self.tracks_by_date = {}
        self.length_range = ValueRange()
        self.length_range_by_date = ValueRange()
        self.__compute_years(tracks)
        for track in tracks:
            if not self.years.contains(track.start_time_local):
                continue
            text_date = track.start_time_local.strftime("%Y-%m-%d")
            if text_date in self.tracks_by_date:
                self.tracks_by_date[text_date].append(track)
            else:
                self.tracks_by_date[text_date] = [track]
            self.length_range.extend(track.length)
        for tracks in self.tracks_by_date.values():
            length = sum([t.length for t in tracks])
            self.length_range_by_date.extend(length)

    def draw(self, drawer, output):
        """Set the Poster's drawer and draw the tracks."""
        self.tracks_drawer = drawer
        height = self.height
        width = self.width
        if self.drawer_type == "plain":
            height = height - 100
            self.colors["background"] = "#1a1a1a"
            self.colors["track"] = "red"
            self.colors["special"] = "yellow"
            self.colors["text"] = "#e1ed5e"
        d = svgwrite.Drawing(output, (f"{width}mm", f"{height}mm"))
        d.viewbox(0, 0, self.width, height)
        d.add(d.rect((0, 0), (width, height), fill=self.colors["background"]))
        if not self.drawer_type == "plain":
            self.__draw_header(d)
            self.__draw_footer(d)
            self.__draw_tracks(d, XY(width - 20, height - 30 - 30), XY(10, 30))
        else:
            self.__draw_tracks(d, XY(width - 20, height), XY(10, 0))
        d.save()

    def m2u(self, m):
        """Convert meters to kilometers or miles, according to units."""
        if self.units == "metric":
            return 0.001 * m
        return 0.001 * m / 1.609344

    def u(self):
        """Return the unit of distance being used on the Poster."""
        if self.units == "metric":
            return "km"
        return "mi"

    def format_distance(self, d: float) -> str:
        """Formats a distance using the locale specific float format and the selected unit."""
        return format_float(self.m2u(d)) + " " + self.u()

    def __draw_tracks(self, d, size: XY, offset: XY):
        self.tracks_drawer.draw(d, size, offset)

    def __draw_header(self, d):
        text_color = self.colors["text"]
        title_style = "font-size:12px; font-family:Arial; font-weight:bold;"
        d.add(d.text(self.title, insert=(10, 20), fill=text_color, style=title_style))

    def __draw_footer(self, d):
        text_color = self.colors["text"]
        header_style = "font-size:4px; font-family:Arial"
        value_style = "font-size:9px; font-family:Arial"
        small_value_style = "font-size:3px; font-family:Arial"

        special_distance1 = self.special_distance["special_distance"]
        special_distance2 = self.special_distance["special_distance2"]

        (
            total_length,
            average_length,
            min_length,
            max_length,
            weeks,
        ) = self.__compute_track_statistics()

        d.add(
            d.text(
                self.trans("ATHLETE"),
                insert=(10, self.height - 20),
                fill=text_color,
                style=header_style,
            )
        )
        d.add(
            d.text(
                self.athlete,
                insert=(10, self.height - 10),
                fill=text_color,
                style=value_style,
            )
        )

        d.add(
            d.text(
                self.trans("SPECIAL TRACKS"),
                insert=(65, self.height - 20),
                fill=text_color,
                style=header_style,
            )
        )

        d.add(d.rect((65, self.height - 17), (2.6, 2.6), fill=self.colors["special"]))

        d.add(
            d.text(
                f"Over {special_distance1:.1f} km",
                insert=(70, self.height - 14.5),
                fill=text_color,
                style=small_value_style,
            )
        )

        d.add(d.rect((65, self.height - 13), (2.6, 2.6), fill=self.colors["special2"]))

        d.add(
            d.text(
                f"Over {special_distance2:.1f} km",
                insert=(70, self.height - 10.5),
                fill=text_color,
                style=small_value_style,
            )
        )

        d.add(
            d.text(
                self.trans("STATISTICS"),
                insert=(120, self.height - 20),
                fill=text_color,
                style=header_style,
            )
        )
        d.add(
            d.text(
                self.trans("Number") + f": {len(self.tracks)}",
                insert=(120, self.height - 15),
                fill=text_color,
                style=small_value_style,
            )
        )
        d.add(
            d.text(
                self.trans("Weekly") + ": " + format_float(len(self.tracks) / weeks),
                insert=(120, self.height - 10),
                fill=text_color,
                style=small_value_style,
            )
        )
        d.add(
            d.text(
                self.trans("Total") + ": " + self.format_distance(total_length),
                insert=(141, self.height - 15),
                fill=text_color,
                style=small_value_style,
            )
        )
        d.add(
            d.text(
                self.trans("Avg") + ": " + self.format_distance(average_length),
                insert=(141, self.height - 10),
                fill=text_color,
                style=small_value_style,
            )
        )
        d.add(
            d.text(
                self.trans("Min") + ": " + self.format_distance(min_length),
                insert=(167, self.height - 15),
                fill=text_color,
                style=small_value_style,
            )
        )
        d.add(
            d.text(
                self.trans("Max") + ": " + self.format_distance(max_length),
                insert=(167, self.height - 10),
                fill=text_color,
                style=small_value_style,
            )
        )

    def __compute_track_statistics(self):
        length_range = ValueRange()
        total_length = 0
        total_length_year_dict = defaultdict(int)
        weeks = {}
        for t in self.tracks:
            total_length += t.length
            total_length_year_dict[t.start_time_local.year] += t.length
            length_range.extend(t.length)
            # time.isocalendar()[1] -> week number
            weeks[(t.start_time_local.year, t.start_time_local.isocalendar()[1])] = 1
        self.total_length_year_dict = total_length_year_dict
        return (
            total_length,
            total_length / len(self.tracks),
            length_range.lower(),
            length_range.upper(),
            len(weeks),
        )

    def __compute_years(self, tracks):
        if self.years is not None:
            return
        self.years = YearRange()
        for t in tracks:
            self.years.add(t.start_time_local)
