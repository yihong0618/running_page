import datetime
from collections import defaultdict
import svgwrite
from .tracks_drawer import TracksDrawer
from .xy import XY

class YearSummaryDrawer(TracksDrawer):
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

    # Revert to standard signature (remove 'poster' argument)
    def draw(self, dr: svgwrite.Drawing, size: XY, offset: XY):
        text_color = self.poster.colors.get("text", "#FFFFFF")
        track_color = self.poster.colors.get("track", "#4DD2FF")
        special_color = self.poster.colors.get("special", "#FFFF00")
        dim_color = "#555555"

        year_tracks = [
            t for t in self.poster.tracks if t.start_time_local.year == self.year
        ]

        # Use internal helper (no arguments needed)
        stats = self._calculate_stats(year_tracks)

        left_margin = offset.x + 6
        left_width = size.x * 0.40
        right_section_start = offset.x + left_width

        first_run_date = self._get_first_run_date()
        if first_run_date:
            days_ago = (datetime.datetime.now() - first_run_date).days
            header_text = f"Running for {days_ago} Days"
        else:
            header_text = f"Year {self.year}"

        dr.add(dr.text(header_text, insert=(left_margin, offset.y + 14), fill=dim_color, style="font-size:6px; font-family:Arial;"))
        dr.add(dr.text("Races", insert=(left_margin, offset.y + 34), fill=dim_color, style="font-size:6px; font-family:Arial;"))

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
                dr.add(dr.text(str(race_num), insert=(left_margin, y_pos), fill=dim_color, style="font-size:8px; font-family:Arial;"))
                dr.add(dr.text(name, insert=(left_margin + 12, y_pos), fill=text_color, style="font-size:10px; font-family:Arial; font-weight:bold;"))
                dr.add(dr.text(f"{count}x", insert=(left_margin + 38, y_pos), fill=dim_color, style="font-size:6px; font-family:Arial;"))
                y_pos += 18
                race_num += 1
                race_count += 1

        if race_count == 0:
            stats_start_y = offset.y + 72
        else:
            stats_start_y = offset.y + 54 + race_count * 18 + 26

        dr.add(dr.text("Stats", insert=(left_margin, stats_start_y - 6), fill=dim_color, style="font-size:6px; font-family:Arial;"))

        total_hours = int(stats["total_time"] // 3600)

        # Use self.poster.u() for unit label
        stat_items = [
            ("Distance", f"{int(stats['total_distance'])}", self.poster.u()),
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

            dr.add(dr.text(label, insert=(x, y), fill=dim_color, style="font-size:5px; font-family:Arial;"))
            dr.add(dr.text(value, insert=(x, y + 11), fill=text_color, style="font-size:10px; font-family:Arial; font-weight:bold;"))
            if unit:
                value_width = len(value) * 6
                dr.add(dr.text(unit, insert=(x + value_width, y + 11), fill=dim_color, style="font-size:6px; font-family:Arial;"))

        dots_y_start = offset.y + 8
        dots_height = size.y - 16
        dots_spacing_y = dots_height / 31
        runner_row_center = dots_y_start + 27.5 * dots_spacing_y
        runner_name = self.poster.athlete if self.poster.athlete else "Runner"
        
        dr.add(dr.text("Runner", insert=(left_margin, runner_row_center - 4), fill=dim_color, style="font-size:5px; font-family:Arial;"))
        dr.add(dr.text(runner_name, insert=(left_margin, runner_row_center + 6), fill=text_color, style="font-size:8px; font-family:Arial; font-weight:bold;"))

        dots_last_row_center = dots_y_start + 30.5 * dots_spacing_y
        footer_y = dots_last_row_center + 3
        dr.add(dr.text(f"running_page/{self.year}", insert=(left_margin, footer_y), fill=dim_color, style="font-size:7px; font-family:Arial;"))

        self._draw_monthly_grid_vertical(dr, year_tracks, right_section_start, offset.y + 8, size.x - (right_section_start - offset.x) - 8, size.y - 16, track_color, special_color, dim_color)

    def _calculate_stats(self, tracks):
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
            # Use m2u for race detection? 
            # NOTE: Races are usually defined by standard km/miles. 
            # 42km is 42km regardless of display units. 
            # It is safer to keep race detection in metric (km), or convert carefully.
            # Here we keep km for detection to avoid logic bugs:
            dist_km = t.length / 1000 
            
            if t.length > longest_run_m:
                longest_run_m = t.length

            if dist_km >= 42.0: stats["marathon_count"] += 1
            elif dist_km >= 21.0: stats["half_marathon_count"] += 1
            elif dist_km >= 10.0: stats["10k_count"] += 1

            if t.moving_dict and "moving_time" in t.moving_dict:
                moving_time = t.moving_dict["moving_time"]
                if isinstance(moving_time, datetime.timedelta):
                    total_time_s += moving_time.total_seconds()
                else:
                    total_time_s += float(moving_time)
            elif t.end_time and t.start_time:
                if isinstance(t.end_time, datetime.datetime) and isinstance(t.start_time, datetime.datetime):
                    total_time_s += (t.end_time - t.start_time).total_seconds()

        # USE SELF.POSTER.M2U HERE
        stats["total_distance"] = self.poster.m2u(total_distance_m)
        stats["total_time"] = total_time_s
        stats["longest_run"] = self.poster.m2u(longest_run_m)

        # Calculate average pace (min per Unit)
        if total_distance_m > 0 and total_time_s > 0:
            # Time / Distance(in units)
            pace_s_per_unit = total_time_s / self.poster.m2u(total_distance_m)
            pace_min = int(pace_s_per_unit // 60)
            pace_sec = int(pace_s_per_unit % 60)
            stats["avg_pace"] = f"{pace_min}'{pace_sec:02d}\""

        stats["streak"] = self._calculate_streak(tracks)
        return stats

    def _calculate_streak(self, tracks):
        if not tracks: return 0
        dates = sorted(set(t.start_time_local.date() for t in tracks))
        if not dates: return 0
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
        if not self.poster.tracks: return None
        return min(t.start_time_local for t in self.poster.tracks)

    def _draw_monthly_grid_vertical(self, dr, tracks, x_start, y_start, width, height, track_color, special_color, dim_color):
        month_data = defaultdict(lambda: defaultdict(float))
        for t in tracks:
            month = t.start_time_local.month
            day = t.start_time_local.day
            # USE M2U HERE
            month_data[month][day] += self.poster.m2u(t.length)

        cols = 12
        rows = 31
        spacing_x = width / cols
        spacing_y = height / rows
        radius = min(spacing_x, spacing_y) / 2 * 0.75

        special_distance = self.poster.special_distance.get("special_distance", 10)

        for month in range(1, 13):
            for day in range(1, 32):
                try:
                    datetime.date(self.year, month, day)
                except ValueError:
                    continue

                cx = x_start + (month - 1) * spacing_x + spacing_x / 2
                cy = y_start + (day - 1) * spacing_y + spacing_y / 2
                dist = month_data[month].get(day, 0)

                if dist > 0:
                    if dist >= special_distance:
                        color = special_color
                    else:
                        intensity = min(dist / special_distance, 1.0)
                        color = self._interpolate_color(dim_color, track_color, intensity)
                else:
                    color = dim_color

                circle = dr.circle(center=(cx, cy), r=radius, fill=color)
                title = f"{self.year}-{month:02d}-{day:02d}"
                if dist > 0:
                    # USE SELF.POSTER.U() HERE
                    title += f": {int(dist) if dist >= 1 else round(dist, 1)} {self.poster.u()}"
                circle.set_desc(title=title)
                dr.add(circle)

    def _interpolate_color(self, color1, color2, t):
        def hex_to_rgb(hex_color):
            hex_color = hex_color.lstrip("#")
            return tuple(int(hex_color[i : i + 2], 16) for i in (0, 2, 4))
        def rgb_to_hex(rgb):
            return "#{:02x}{:02x}{:02x}".format(*rgb)
        rgb1 = hex_to_rgb(color1)
        rgb2 = hex_to_rgb(color2)
        rgb = tuple(int(rgb1[i] + (rgb2[i] - rgb1[i]) * t) for i in range(3))
        return rgb_to_hex(rgb)