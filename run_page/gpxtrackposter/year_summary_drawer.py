"""Draw a Year Summary poster similar to Cursor stats style."""

import datetime
from collections import defaultdict

import svgwrite

from .tracks_drawer import TracksDrawer
from .xy import XY


class YearSummaryDrawer(TracksDrawer):
    """Draw a Year Summary poster with monthly activity dots and statistics"""

    def __init__(self, the_poster):
        super().__init__(the_poster)
        self.year = None

    def create_args(self, args_parser):
        args_parser.add_argument(
            "--summary-year",
            dest="summary_year",
            metavar="YEAR",
            type=int,
            default=None,
            help="Year to generate summary for (default: current year)",
        )

    def fetch_args(self, args):
        if args.type == "year_summary":
            self.year = args.summary_year or datetime.datetime.now().year

    def draw(self, dr: svgwrite.Drawing, size: XY, offset: XY):
        """Draw the year summary poster"""
        # Colors - use running_page default colors
        text_color = self.poster.colors.get("text", "#FFFFFF")
        track_color = self.poster.colors.get("track", "#4DD2FF")
        special_color = self.poster.colors.get("special", "#FFFF00")
        dim_color = "#555555"

        # Filter tracks for the specified year
        year_tracks = [
            t for t in self.poster.tracks if t.start_time_local.year == self.year
        ]

        # Calculate statistics
        stats = self._calculate_stats(year_tracks)

        # Layout settings - left side takes about 40% width
        left_margin = offset.x + 6
        left_width = size.x * 0.40
        right_section_start = offset.x + left_width

        # Draw "Running for X Days" header - align with top of dots (offset.y + 8)
        first_run_date = self._get_first_run_date()
        if first_run_date:
            days_ago = (datetime.datetime.now() - first_run_date).days
            header_text = f"Running for {days_ago} Days"
        else:
            header_text = f"Year {self.year}"

        dr.add(
            dr.text(
                header_text,
                insert=(left_margin, offset.y + 14),
                fill=dim_color,
                style="font-size:6px; font-family:Arial;",
            )
        )

        # Draw race categories
        dr.add(
            dr.text(
                "Races",
                insert=(left_margin, offset.y + 34),
                fill=dim_color,
                style="font-size:6px; font-family:Arial;",
            )
        )

        # Race format: "1  Full  2x" style - bigger font like Cursor
        race_categories = [
            ("Full", stats["marathon_count"]),
            ("Half", stats["half_marathon_count"]),
            ("10K", stats["10k_count"]),
        ]

        y_pos = offset.y + 54
        race_num = 1
        race_count = 0
        for name, count in race_categories:
            if count > 0:
                # Number - small gray
                dr.add(
                    dr.text(
                        str(race_num),
                        insert=(left_margin, y_pos),
                        fill=dim_color,
                        style="font-size:8px; font-family:Arial;",
                    )
                )
                # Race name - big white bold
                dr.add(
                    dr.text(
                        name,
                        insert=(left_margin + 12, y_pos),
                        fill=text_color,
                        style="font-size:10px; font-family:Arial; font-weight:bold;",
                    )
                )
                # Count - small gray
                dr.add(
                    dr.text(
                        f"{count}x",
                        insert=(left_margin + 38, y_pos),
                        fill=dim_color,
                        style="font-size:6px; font-family:Arial;",
                    )
                )
                y_pos += 18
                race_num += 1
                race_count += 1

        # Draw main stats in 2x2 grid - position based on race count
        # If no races, start earlier; otherwise position after races
        if race_count == 0:
            stats_start_y = offset.y + 72
        else:
            stats_start_y = offset.y + 54 + race_count * 18 + 26

        # Stats title
        dr.add(
            dr.text(
                "Stats",
                insert=(left_margin, stats_start_y - 6),
                fill=dim_color,
                style="font-size:6px; font-family:Arial;",
            )
        )

        # Format total time
        total_hours = int(stats["total_time"] // 3600)

        # Stats with separate value and unit for better layout
        stat_items = [
            ("Distance", f"{int(stats['total_distance'])}", "km"),
            ("Runs", f"{stats['total_runs']}", ""),
            ("Avg Pace", stats["avg_pace"], ""),
            ("Streak", f"{stats['streak']}", "d"),
            ("Time", f"{total_hours}", "h"),
            ("Longest", f"{stats['longest_run']:.1f}", ""),
        ]

        col1_x = left_margin
        col2_x = left_margin + 42

        for i, (label, value, unit) in enumerate(stat_items):
            x = col1_x if i % 2 == 0 else col2_x
            y = stats_start_y + (i // 2) * 28

            # Label - small gray
            dr.add(
                dr.text(
                    label,
                    insert=(x, y),
                    fill=dim_color,
                    style="font-size:5px; font-family:Arial;",
                )
            )
            # Value - big white bold
            dr.add(
                dr.text(
                    value,
                    insert=(x, y + 11),
                    fill=text_color,
                    style="font-size:10px; font-family:Arial; font-weight:bold;",
                )
            )
            # Unit - small gray, next to value
            if unit:
                # Estimate value width based on character count
                value_width = len(value) * 6
                dr.add(
                    dr.text(
                        unit,
                        insert=(x + value_width, y + 11),
                        fill=dim_color,
                        style="font-size:6px; font-family:Arial;",
                    )
                )

        # Draw Runner name and footer at bottom
        # Calculate positions to align with bottom rows of dots
        # Dots: y_start = offset.y + 8, height = size.y - 16, rows = 31
        dots_y_start = offset.y + 8
        dots_height = size.y - 16
        dots_spacing_y = dots_height / 31

        # Runner aligns with ~4th row from bottom
        runner_row_center = dots_y_start + 27.5 * dots_spacing_y
        runner_name = self.poster.athlete if self.poster.athlete else "Runner"
        dr.add(
            dr.text(
                "Runner",
                insert=(left_margin, runner_row_center - 4),
                fill=dim_color,
                style="font-size:5px; font-family:Arial;",
            )
        )
        dr.add(
            dr.text(
                runner_name,
                insert=(left_margin, runner_row_center + 6),
                fill=text_color,
                style="font-size:8px; font-family:Arial; font-weight:bold;",
            )
        )

        # Footer aligns with last row of dots
        dots_last_row_center = dots_y_start + 30.5 * dots_spacing_y
        footer_y = dots_last_row_center + 3
        dr.add(
            dr.text(
                f"running_page/{self.year}",
                insert=(left_margin, footer_y),
                fill=dim_color,
                style="font-size:7px; font-family:Arial;",
            )
        )

        # Draw monthly dots grid on right side - VERTICAL layout like Cursor
        self._draw_monthly_grid_vertical(
            dr,
            year_tracks,
            right_section_start,
            offset.y + 8,
            size.x - (right_section_start - offset.x) - 8,
            size.y - 16,
            track_color,
            special_color,
            dim_color,
        )

    def _calculate_stats(self, tracks):
        """Calculate running statistics for the year"""
        stats = {
            "total_runs": len(tracks),
            "total_distance": 0,
            "marathon_count": 0,
            "half_marathon_count": 0,
            "10k_count": 0,
            "avg_pace": "0'00\"",
            "streak": 0,
            "total_time": 0,
            "longest_run": 0,
        }

        if not tracks:
            return stats

        total_distance_m = sum(t.length for t in tracks)
        total_time_s = 0
        longest_run_m = 0

        for t in tracks:
            dist_km = t.length / 1000
            # Track longest run
            if t.length > longest_run_m:
                longest_run_m = t.length

            # Count race distances
            if dist_km >= 42.0:
                stats["marathon_count"] += 1
            elif dist_km >= 21.0:
                stats["half_marathon_count"] += 1
            elif dist_km >= 10.0:
                stats["10k_count"] += 1

            # Calculate total moving time
            if t.moving_dict and "moving_time" in t.moving_dict:
                moving_time = t.moving_dict["moving_time"]
                if isinstance(moving_time, datetime.timedelta):
                    total_time_s += moving_time.total_seconds()
                else:
                    total_time_s += float(moving_time)
            elif t.end_time and t.start_time:
                if isinstance(t.end_time, datetime.datetime) and isinstance(
                    t.start_time, datetime.datetime
                ):
                    total_time_s += (t.end_time - t.start_time).total_seconds()

        stats["total_distance"] = total_distance_m / 1000
        stats["total_time"] = total_time_s
        stats["longest_run"] = longest_run_m / 1000

        # Calculate average pace (min/km)
        if total_distance_m > 0 and total_time_s > 0:
            pace_s_per_km = total_time_s / (total_distance_m / 1000)
            pace_min = int(pace_s_per_km // 60)
            pace_sec = int(pace_s_per_km % 60)
            stats["avg_pace"] = f"{pace_min}'{pace_sec:02d}\""

        # Calculate streak (consecutive days)
        stats["streak"] = self._calculate_streak(tracks)

        return stats

    def _calculate_streak(self, tracks):
        """Calculate the longest running streak in days"""
        if not tracks:
            return 0

        # Get unique dates
        dates = sorted(set(t.start_time_local.date() for t in tracks))
        if not dates:
            return 0

        max_streak = 1
        current_streak = 1

        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days == 1:
                current_streak += 1
                max_streak = max(max_streak, current_streak)
            else:
                current_streak = 1

        return max_streak

    def _get_first_run_date(self):
        """Get the date of the first run ever"""
        if not self.poster.tracks:
            return None
        return min(t.start_time_local for t in self.poster.tracks)

    def _draw_monthly_grid_vertical(
        self,
        dr,
        tracks,
        x_start,
        y_start,
        width,
        height,
        track_color,
        special_color,
        dim_color,
    ):
        """Draw the monthly activity grid - 12 columns (months), 31 rows (days)"""
        # Group tracks by month and day
        month_data = defaultdict(lambda: defaultdict(float))
        for t in tracks:
            month = t.start_time_local.month
            day = t.start_time_local.day
            month_data[month][day] += t.length / 1000  # km

        # Grid parameters - 12 columns (months), 31 rows (days)
        cols = 12  # months
        rows = 31  # max days

        # Calculate spacing - make dots bigger with tighter spacing
        spacing_x = width / cols
        spacing_y = height / rows
        radius = min(spacing_x, spacing_y) / 2 * 0.75

        # Find max distance for color scaling
        max_dist = 1
        for month_days in month_data.values():
            for dist in month_days.values():
                max_dist = max(max_dist, dist)

        special_distance = self.poster.special_distance.get("special_distance", 10)

        # Draw dots - each column is a month, each row is a day
        for month in range(1, 13):
            for day in range(1, 32):
                # Check if this day exists in this month
                try:
                    datetime.date(self.year, month, day)
                except ValueError:
                    continue  # Invalid date (e.g., Feb 30)

                # Position: x = month (column), y = day (row)
                cx = x_start + (month - 1) * spacing_x + spacing_x / 2
                cy = y_start + (day - 1) * spacing_y + spacing_y / 2

                dist = month_data[month].get(day, 0)

                if dist > 0:
                    # Activity day - color based on distance
                    if dist >= special_distance:
                        color = special_color
                    else:
                        # Interpolate between dim and track color based on distance
                        intensity = min(dist / special_distance, 1.0)
                        color = self._interpolate_color(
                            dim_color, track_color, intensity
                        )
                else:
                    # No activity - dim dot
                    color = dim_color

                circle = dr.circle(center=(cx, cy), r=radius, fill=color)
                title = f"{self.year}-{month:02d}-{day:02d}"
                if dist > 0:
                    title += f": {int(dist) if dist >= 1 else round(dist, 1)} km"
                circle.set_desc(title=title)
                dr.add(circle)

    def _interpolate_color(self, color1, color2, t):
        """Interpolate between two hex colors"""

        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip("#")
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))

        def rgb_to_hex(rgb):
            return "#{:02x}{:02x}{:02x}".format(*rgb)

        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)

        rgb = tuple(int(rgb1[i] + (rgb2[i] - rgb1[i]) * t) for i in range(3))
        return rgb_to_hex(rgb)
