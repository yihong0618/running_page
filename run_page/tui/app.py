"""running_page TUI — full-featured terminal UI for browsing running activities."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Group as RichGroup
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text as RichText
from textual import events
from textual.app import App, ComposeResult
from textual.message import Message
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, DataTable, Label, Static

from .braille import render_polyline
from .data import (
    Activity,
    AggregatedData,
    FilterFunc,
    YearStats,
    aggregate_activities,
    find_data_file,
    load_activities,
    make_type_filter,
    make_year_filter,
)

# ── colour palette ─────────────────────────────────────────

# Keep the TUI aligned with the web dark theme in src/styles/index.css.
BG_COLOR = "#171717"  # neutral-900 / --color-bg
SURFACE_COLOR = "#262626"  # neutral-800 / --color-run-row-hover-background
CARD_BORDER_COLOR = "#404040"  # neutral-700 / --color-activity-card
TEXT_COLOR = "#d4d4d8"  # zinc-300 / --color-run-table-thead
MUTED_TEXT_COLOR = "#d4d4d4"  # neutral-300 / --color-run-date
PRIMARY_COLOR = "#e0ed5e"  # --color-brand
SECONDARY_COLOR = "#ccd94a"  # --color-secondary
ACTIVE_CELL_COLOR = "#4dd2ff"  # --svg-color-active-cell
SPECIAL_COLOR = "#f7d02c"  # --svg-special-color
SPECIAL_COLOR_2 = "#f56c6c"  # --svg-special-color2
SINGLE_RUN_COLOR = "#ff4d4f"  # SINGLE_RUN_COLOR_DARK
FOCUS_SURFACE_COLOR = "#3a3a22"

TYPE_COLORS = {
    "Run": PRIMARY_COLOR,
    "Ride": SECONDARY_COLOR,
    "Hike": SPECIAL_COLOR,
    "Walk": TEXT_COLOR,
    "Swim": SPECIAL_COLOR_2,
    "Workout": MUTED_TEXT_COLOR,
}

INDOOR_COLOR = MUTED_TEXT_COLOR
TRAIL_COLOR = SPECIAL_COLOR


def _type_color(activity: Activity) -> str:
    if activity.subtype in ("indoor", "treadmill", "virtualrun"):
        return INDOOR_COLOR
    if activity.subtype == "trail":
        return TRAIL_COLOR
    return TYPE_COLORS.get(activity.sport_type_normalized, PRIMARY_COLOR)


def fmt_num(n: float, decimals: int = 2) -> str:
    s = f"{n:,.{decimals}f}"
    if decimals > 0:
        int_part, dec_part = s.split(".")
        return int_part + "." + dec_part
    return s


def fmt_duration(seconds: float) -> str:
    seconds = int(seconds)
    days = seconds // 86400
    hours = (seconds % 86400) // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    parts = []
    if days > 0:
        parts.append(f"{days}d")
    if hours > 0:
        parts.append(f"{hours}h")
    if minutes > 0:
        parts.append(f"{minutes}m")
    if secs > 0 and not days:
        parts.append(f"{secs}s")
    return " ".join(parts) if parts else "0s"


def _monthly_distances(year_stats: YearStats) -> list[float]:
    totals = [0.0] * 12
    for date_str, distance_km in year_stats.daily_distances.items():
        try:
            month = int(date_str[5:7])
        except (TypeError, ValueError, IndexError):
            continue
        if 1 <= month <= 12:
            totals[month - 1] += distance_km
    return totals


def _monthly_counts(activities: list[Activity], year: str) -> list[int]:
    totals = [0] * 12
    for activity in activities:
        if activity.year != year:
            continue
        try:
            month = int(activity.date_local[5:7])
        except (TypeError, ValueError, IndexError):
            continue
        if 1 <= month <= 12:
            totals[month - 1] += 1
    return totals


def _render_bar_chart(
    title: str,
    labels: list[str],
    values: list[float | int],
    *,
    width: int,
    color: str,
    suffix: str,
) -> Panel | None:
    if not values or not any(values):
        return None

    max_value = max(values)
    bar_width = max(8, min(22, width - 22))
    text = RichText()

    for label, value in zip(labels, values):
        filled = (
            0
            if max_value <= 0
            else int(round(float(value) / float(max_value) * bar_width))
        )
        if value > 0:
            filled = max(1, filled)
        empty = max(0, bar_width - filled)
        text.append(f"{label} ", style=MUTED_TEXT_COLOR)
        text.append("█" * filled, style=color)
        text.append("·" * empty, style=CARD_BORDER_COLOR)
        text.append(f"  {value:>5}{suffix}\n", style=TEXT_COLOR)

    return Panel(text, title=title, title_align="left", border_style=CARD_BORDER_COLOR)


def _render_monthly_chart(year: str, totals: list[float], width: int) -> Panel | None:
    if not totals or not any(totals):
        return None
    return _render_bar_chart(
        f"Monthly Distance ({year})",
        [f"{month:02d}" for month in range(1, 13)],
        [round(total, 1) for total in totals],
        width=width,
        color=PRIMARY_COLOR,
        suffix=" km",
    )


def _render_stats_cards(data: AggregatedData, width: int) -> RichTable:
    def metric_panel(title: str, value: str, accent: str = TEXT_COLOR) -> Panel:
        body = RichText()
        body.append(title + "\n", style=MUTED_TEXT_COLOR)
        body.append(value, style=f"bold {accent}")
        return Panel(body, border_style=CARD_BORDER_COLOR, padding=(0, 1))

    cols = 4 if width >= 140 else (3 if width >= 100 else 2)

    metrics: list[tuple[str, str, str]] = [
        ("Distance", f"{fmt_num(data.total_distance, 1)} km", PRIMARY_COLOR),
        ("Runs", f"{data.total_count}", TEXT_COLOR),
        ("Total Time", fmt_duration(data.total_time_sec), TEXT_COLOR),
        ("Avg Pace", f"{data.overall_avg_pace or '-'} /km", TEXT_COLOR),
        ("Max Distance", f"{data.total_max_distance:.1f} km", TEXT_COLOR),
        (
            "Avg Heart Rate",
            f"{data.overall_avg_hr:.0f} bpm" if data.overall_avg_hr else "-",
            TEXT_COLOR,
        ),
        ("Total Elevation", f"{fmt_num(data.total_elevation, 0)} m", TEXT_COLOR),
        ("Cities", f"{len(data.city_details)}", TEXT_COLOR),
        ("Countries", f"{len(data.countries)}", TEXT_COLOR),
    ]

    grid = RichTable.grid(expand=True, padding=(0, 1))
    for _ in range(cols):
        grid.add_column(ratio=1)

    for i in range(0, len(metrics), cols):
        row = metrics[i : i + cols]
        while len(row) < cols:
            row.append(("", "", TEXT_COLOR))
        grid.add_row(
            *[
                metric_panel(title, value, accent) if title else ""
                for title, value, accent in row
            ]
        )

    return grid


def _render_distribution_panel(data: AggregatedData, focus_year: str) -> Panel:
    lines = RichText()
    if data.periods:
        lines.append("Periods\n", style=f"bold {PRIMARY_COLOR}")
        for name, count in list(data.periods.items())[:5]:
            lines.append(f"{name:<12}", style=MUTED_TEXT_COLOR)
            lines.append(f"{count}\n", style=TEXT_COLOR)
    lines.append("\n")
    if data.year_stats and focus_year in data.year_stats:
        ys = data.year_stats[focus_year]
        monthly = _monthly_distances(ys)
        best_month = (
            max(range(12), key=lambda idx: monthly[idx]) if any(monthly) else None
        )
        lines.append("Highlights\n", style=f"bold {PRIMARY_COLOR}")
        if best_month is not None:
            lines.append("Best Month   ", style=MUTED_TEXT_COLOR)
            lines.append(
                f"{best_month + 1:02d}  {monthly[best_month]:.1f} km\n",
                style=TEXT_COLOR,
            )
        lines.append("Longest Run  ", style=MUTED_TEXT_COLOR)
        lines.append(f"{ys.max_distance:.1f} km\n", style=TEXT_COLOR)
        lines.append("Avg HR       ", style=MUTED_TEXT_COLOR)
        lines.append(
            (f"{ys.avg_heart_rate:.0f} bpm" if ys.avg_heart_rate else "-") + "\n",
            style=TEXT_COLOR,
        )
        lines.append("Elevation    ", style=MUTED_TEXT_COLOR)
        lines.append(f"{ys.total_elevation:.0f} m\n", style=TEXT_COLOR)
    return Panel(
        lines, title="Distribution", title_align="left", border_style=CARD_BORDER_COLOR
    )


def _render_cities_panel(data: AggregatedData) -> Panel | None:
    """Render a table of top cities by distance."""
    if not data.city_details:
        return None

    t = RichTable(
        show_header=True,
        header_style=f"bold {PRIMARY_COLOR}",
        border_style=CARD_BORDER_COLOR,
        padding=(0, 1),
    )
    t.add_column("City", style="bold")
    t.add_column("Runs", justify="right")
    t.add_column("Distance", justify="right")
    for city, stats in list(data.city_details.items())[:10]:
        t.add_row(
            city,
            str(stats.count),
            f"{stats.total_distance:.1f} km",
        )

    return Panel(
        t,
        title=f"Cities ({len(data.city_details)})",
        title_align="left",
        border_style=CARD_BORDER_COLOR,
    )


def _section_title(title: str) -> RichText:
    return RichText(title, style=f"bold {PRIMARY_COLOR}")


def _stats_layout_flags(
    width: int, height: int, data: AggregatedData
) -> dict[str, bool]:
    compact = height <= 54 or width <= 140
    tight = height <= 38
    single_year = len(data.years) <= 1
    single_type = len(data.type_counts) <= 1
    return {
        "compact": compact,
        "tight": tight,
        "single_column": width < 120,
        "show_type_breakdown": not (compact and single_type),
        "show_year_breakdown": not single_year and not tight,
        "show_monthly_runs": not tight,
        "show_distribution": height >= 58 and width >= 140 and not compact,
    }


# ── widgets ─────────────────────────────────────────────────


class RouteMapWidget(Widget):
    """Renders a running route as braille art."""

    polyline_str = reactive("")
    activity_name = reactive("")
    distance_km = reactive(0.0)

    def render(self) -> RichText:
        if not self.polyline_str:
            return RichText("  No route data", style=f"dim {MUTED_TEXT_COLOR}")
        w, h = self.size.width, self.size.height
        if w < 10 or h < 4:
            return RichText("  terminal too small", style=f"dim {MUTED_TEXT_COLOR}")
        map_h = h - 1
        lines = render_polyline(self.polyline_str, w, map_h)
        if not lines:
            return RichText("  could not render route", style=f"dim {MUTED_TEXT_COLOR}")
        while len(lines) < map_h:
            lines.append(" " * w)
        lines = [line[:w].ljust(w) for line in lines[:map_h]]
        header = f"  {self.activity_name or 'Route'}  ({self.distance_km:.2f} km)"
        text = RichText(header + "\n", style=f"bold {PRIMARY_COLOR}")
        text.append("\n".join(lines), style=SINGLE_RUN_COLOR)
        return text


class RunDetailPanel(Widget):
    """Metadata for the selected activity."""

    activity: Optional[Activity] = reactive(None)
    data: Optional[AggregatedData] = reactive(None)

    def _rows(self, activity: Activity) -> list[tuple[str, str]]:
        rows: list[tuple[str, str]] = [
            ("Name", activity.name or "-"),
            ("Date", activity.date_local),
            ("Distance", f"{activity.distance_km:.2f} km"),
            ("Time", activity.formatted_time),
            ("Pace", f"{activity.pace_min_km} /km" if activity.pace_min_km else "-"),
        ]
        if activity.average_heartrate:
            rows.append(("Heart Rate", f"{activity.average_heartrate:.0f} bpm"))
        if activity.elevation_gain:
            rows.append(("Elevation", f"{activity.elevation_gain:.0f} m"))
        rows.append(("Speed", f"{activity.average_speed:.2f} m/s"))
        if activity.city:
            rows.append(("Location", activity.city))
        return rows

    def _extra_rows(self, activity: Activity) -> list[tuple[str, str]]:
        """All contextual info (Day/Period/Streak/Race + progress + ranking)."""
        rows: list[tuple[str, str]] = []

        weekdays = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        rows.append(("Day", weekdays[activity.date_obj.weekday()]))
        rows.append(("Period", activity.period))

        if activity.streak > 1:
            rows.append(("Streak", f"🔥 {activity.streak} days"))
        if activity.race_label:
            rows.append(("Race", f"[bold {SPECIAL_COLOR}]{activity.race_label}[/]"))

        if not self.data:
            return rows

        year_acts = sorted(
            [a for a in self.data.activities if a.year == activity.year],
            key=lambda a: (a.date_local, a.run_id),
        )
        month = activity.date_local[:7]
        month_acts = [a for a in year_acts if a.date_local.startswith(month)]

        ytd_distance = 0.0
        mtd_distance = 0.0
        week_distance = 0.0
        iso_year, iso_week, _ = activity.date_obj.isocalendar()

        for idx, run in enumerate(year_acts, 1):
            if run.date_local > activity.date_local or (
                run.date_local == activity.date_local and run.run_id > activity.run_id
            ):
                break
            ytd_distance += run.distance_km
            run_iso_year, run_iso_week, _ = run.date_obj.isocalendar()
            if run.date_local.startswith(month):
                mtd_distance += run.distance_km
            if run_iso_year == iso_year and run_iso_week == iso_week:
                week_distance += run.distance_km

        rows.append(("Week", f"{iso_week:02d}"))
        rows.append(("Week km", f"{week_distance:.1f} km"))
        rows.append(("MTD", f"{mtd_distance:.1f} km"))
        rows.append(("YTD", f"{ytd_distance:.1f} km"))

        for idx, run in enumerate(year_acts, 1):
            if run.run_id == activity.run_id:
                rows.append(("Year #", f"{idx} / {len(year_acts)}"))
                break

        for idx, run in enumerate(month_acts, 1):
            if run.run_id == activity.run_id:
                rows.append(("Month #", f"{idx} / {len(month_acts)}"))
                break

        return rows

    def render(self) -> RichTable | RichText:
        if self.activity is None:
            return RichText(
                "  Select a run to view details", style=f"dim {MUTED_TEXT_COLOR}"
            )
        a = self.activity

        left = RichTable(show_header=False, padding=(0, 1))
        left.add_column("", style=f"bold {PRIMARY_COLOR}")
        left.add_column("")
        for label, value in self._rows(a):
            left.add_row(label, value)

        extra = self._extra_rows(a)
        if self.size.width >= 72 and extra:
            right = RichTable(show_header=False, padding=(0, 1))
            right.add_column("", style=f"bold {SECONDARY_COLOR}")
            right.add_column("")
            for label, value in extra:
                right.add_row(label, value)

            grid = RichTable.grid(expand=True, padding=(0, 1))
            grid.add_column(ratio=5)
            grid.add_column(ratio=4)
            grid.add_row(left, right)
            return grid

        return left


# ── filter bar ─────────────────────────────────────────────


class FilterBar(Widget):
    """Top bar with summary plus year and type filters."""

    class FilterChanged(Message):
        pass

    def __init__(self, years: list[str], types: list[str], **kwargs) -> None:
        super().__init__(**kwargs)
        self._years = ["All"] + years
        self._types = ["All"] + types
        self._year_idx = 0
        self._type_idx = 0

    def compose(self) -> ComposeResult:
        with Horizontal(id="filter-row"):
            yield Label("running_page", id="fl-brand")
            yield Label("0 activities", id="fl-summary")
            yield Button(self._format_year_label(), id="fl-year", classes="filter-chip")
            yield Button(self._format_type_label(), id="fl-type", classes="filter-chip")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fl-year":
            self.cycle_year()
            self.post_message(self.FilterChanged())
        elif event.button.id == "fl-type":
            self.next_type()
            self.post_message(self.FilterChanged())

    @property
    def selected_year(self) -> str:
        return self._years[self._year_idx]

    @property
    def selected_type(self) -> str:
        return self._types[self._type_idx]

    def _format_year_label(self) -> str:
        return self.selected_year

    def _format_type_label(self) -> str:
        return self.selected_type

    def _set_selected_year(self, year: str) -> None:
        if year in self._years:
            self._year_idx = self._years.index(year)
        self._refresh_year_controls()

    def _refresh_year_controls(self) -> None:
        self.query_one("#fl-year", Button).label = self._format_year_label()

    def cycle_year(self) -> None:
        self._year_idx = (self._year_idx + 1) % len(self._years)
        self._refresh_year_controls()

    def previous_year(self) -> None:
        year_values = self._years[1:]
        if not year_values or self.selected_year == "All":
            if year_values:
                self._set_selected_year(year_values[0])
            return
        idx = year_values.index(self.selected_year)
        if idx < len(year_values) - 1:
            self._set_selected_year(year_values[idx + 1])

    def next_type(self) -> None:
        self._type_idx = (self._type_idx + 1) % len(self._types)
        self.query_one("#fl-type", Button).label = self._format_type_label()

    def next_year(self) -> None:
        year_values = self._years[1:]
        if not year_values or self.selected_year == "All":
            if year_values:
                self._set_selected_year(year_values[0])
            return
        idx = year_values.index(self.selected_year)
        if idx > 0:
            self._set_selected_year(year_values[idx - 1])

    def set_options(
        self,
        years: list[str],
        types: list[str],
        *,
        selected_year: str = "All",
        selected_type: str = "All",
    ) -> None:
        self._years = ["All"] + years
        self._types = ["All"] + types
        self._year_idx = (
            self._years.index(selected_year)
            if selected_year in self._years
            else (1 if years else 0)
        )
        self._type_idx = (
            self._types.index(selected_type) if selected_type in self._types else 0
        )
        self._refresh_year_controls()
        self.query_one("#fl-type", Button).label = self._format_type_label()

    def set_summary(self, text: str) -> None:
        self.query_one("#fl-summary", Label).update(text)


# ── nav sidebar ────────────────────────────────────────────


class NavSidebar(Widget):
    """Navigation sidebar with styled buttons."""

    class ViewSelected(Message):
        def __init__(self, view_name: str) -> None:
            super().__init__()
            self.view_name = view_name

    ITEMS = [
        ("list", "1  List"),
        ("stats", "2  Stats"),
    ]

    def compose(self) -> ComposeResult:
        with Vertical(id="nav-sidebar"):
            for key, label in self.ITEMS:
                yield Button(label, id=f"nav-{key}", variant="default")

    def on_mount(self) -> None:
        self.styles.width = 18
        self.styles.min_width = 18
        self.styles.background = BG_COLOR
        self.styles.border = ("solid", CARD_BORDER_COLOR)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        for key, _ in self.ITEMS:
            if event.button.id == f"nav-{key}":
                self.post_message(self.ViewSelected(key))
                break

    def highlight(self, active: str) -> None:
        for key, _ in self.ITEMS:
            btn = self.query_one(f"#nav-{key}", Button)
            if key == active:
                btn.classes = "nav-active"
            else:
                btn.classes = ""


# ── stats view ─────────────────────────────────────────────


class StatsView(VerticalScroll):
    """Overall and per-year statistics."""

    data: Optional[AggregatedData] = reactive(None)
    period_label = reactive("")

    def compose(self) -> ComposeResult:
        yield Static(id="stats-body")

    def on_mount(self) -> None:
        self._refresh_body(reset_scroll=False)

    def watch_data(self, _: Optional[AggregatedData]) -> None:
        self._refresh_body(reset_scroll=True)

    def watch_period_label(self, _: str) -> None:
        self._refresh_body(reset_scroll=False)

    def on_resize(self, event: events.Resize) -> None:
        del event
        self._refresh_body(reset_scroll=False)

    def _refresh_body(self, *, reset_scroll: bool) -> None:
        if not self.is_mounted:
            return
        self.query_one("#stats-body", Static).update(self._build_renderable())
        if reset_scroll:
            self.scroll_home(animate=False)

    def _build_renderable(self) -> RichText | RichGroup:
        if self.data is None:
            return RichText("  Loading...", style=f"dim {MUTED_TEXT_COLOR}")

        d = self.data
        layout = _stats_layout_flags(self.size.width, self.size.height, d)
        parts: list = [
            _section_title("Overview"),
            _render_stats_cards(d, self.size.width),
        ]

        # overall stats
        tbl = RichTable(
            show_header=False, border_style=CARD_BORDER_COLOR, padding=(0, 1)
        )
        tbl.add_column("", style="bold")
        tbl.add_column("")
        tbl.add_row("Total Distance", f"[bold]{fmt_num(d.total_distance, 1)}[/] km")
        tbl.add_row("Activities", f"[bold]{fmt_num(d.total_count, 0)}[/]")
        tbl.add_row("Total Time", fmt_duration(d.total_time_sec))
        if d.overall_avg_pace:
            tbl.add_row("Avg Pace", f"{d.overall_avg_pace} /km")
        if d.overall_avg_hr:
            tbl.add_row("Avg Heart Rate", f"{d.overall_avg_hr:.0f} bpm")
        tbl.add_row("Total Elevation", f"{fmt_num(d.total_elevation, 0)} m")
        tbl.add_row("Max Distance", f"{d.total_max_distance:.2f} km")
        period_label = self.period_label or (
            f"{d.first_date[:4]}-{d.last_date[:4]}"
            if d.first_date and d.last_date
            else ""
        )
        if period_label:
            tbl.add_row("Period", period_label)
        races = d.races
        if any(races.values()):
            tbl.add_section()
            tbl.add_row("Full Marathons", str(races["全程马拉松"]))
            tbl.add_row("Half Marathons", str(races["半程马拉松"]))
            tbl.add_row("10K+ Runs", str(races["10K"]))
        overall_block = RichGroup(_section_title("Overall Statistics"), tbl)

        # trends
        trends_items: list = []
        if d.year_stats and d.years:
            focus_year = d.years[0]
            monthly_distance_chart = _render_monthly_chart(
                focus_year,
                _monthly_distances(d.year_stats[focus_year]),
                self.size.width,
            )
            monthly_count_chart = _render_bar_chart(
                f"Monthly Runs ({focus_year})",
                [f"{month:02d}" for month in range(1, 13)],
                _monthly_counts(d.activities, focus_year),
                width=self.size.width,
                color=SECONDARY_COLOR,
                suffix=" r",
            )
            distribution_panel = _render_distribution_panel(d, focus_year)
            if monthly_distance_chart is not None:
                trends_items.append(monthly_distance_chart)
            if monthly_count_chart is not None and layout["show_monthly_runs"]:
                trends_items.append(monthly_count_chart)
            if distribution_panel is not None and layout["show_distribution"]:
                trends_items.append(distribution_panel)
        trends_block = (
            RichGroup(_section_title("Trends"), *trends_items) if trends_items else None
        )

        # geography
        cities_panel = _render_cities_panel(d)
        geography_block = (
            RichGroup(_section_title("Geography"), cities_panel)
            if cities_panel is not None
            else None
        )

        # Build main three-column layout
        main_blocks: list = []
        extra_parts: list = []
        main_blocks.append(overall_block)
        if trends_block is not None:
            main_blocks.append(trends_block)
        if geography_block is not None:
            main_blocks.append(geography_block)

        # Extra content below the main columns
        if d.type_counts and layout["show_type_breakdown"]:
            extra_parts.append(_section_title("By Activity Type"))
            tt = RichTable(
                show_header=False, border_style=CARD_BORDER_COLOR, padding=(0, 1)
            )
            tt.add_column("Type", style="bold")
            tt.add_column("Count")
            tt.add_column("Distance (km)")
            for tname in sorted(d.type_counts, key=lambda x: -d.type_counts[x]):
                color = TYPE_COLORS.get(tname, TEXT_COLOR)
                tt.add_row(
                    f"[{color}]{tname}[/]",
                    str(d.type_counts[tname]),
                    f"{d.type_distances[tname]:.1f}",
                )
            extra_parts.append(tt)

        if d.year_stats and layout["show_year_breakdown"]:
            extra_parts.append(_section_title("Per-Year Breakdown"))
            yt = RichTable(
                show_header=True,
                header_style=f"bold {PRIMARY_COLOR}",
                border_style=CARD_BORDER_COLOR,
                padding=(0, 1),
            )
            yt.add_column("Year")
            yt.add_column("Cnt")
            yt.add_column("Dist")
            yt.add_column("Pace")
            yt.add_column("HR")
            yt.add_column("Elev")
            yt.add_column("MaxD")
            for yname in d.years:
                ys = d.year_stats[yname]
                p = ys.avg_pace or "-"
                hr = f"{ys.avg_heart_rate:.0f}" if ys.avg_heart_rate else "-"
                yt.add_row(
                    yname,
                    str(ys.count),
                    f"{ys.total_distance:.0f}",
                    p,
                    hr,
                    f"{ys.total_elevation:.0f}",
                    f"{ys.max_distance:.1f}",
                )
            extra_parts.append(yt)

        # Layout: 3-col, 2-col, or single column based on width
        if len(main_blocks) >= 3 and self.size.width >= 120:
            content_grid = RichTable.grid(expand=True, padding=(0, 1))
            for _ in main_blocks:
                content_grid.add_column(ratio=1)
            content_grid.add_row(*main_blocks)
            parts.append(content_grid)
        elif len(main_blocks) >= 2 and not layout["single_column"]:
            content_grid = RichTable.grid(expand=True, padding=(0, 1))
            content_grid.add_column(ratio=1)
            content_grid.add_column(ratio=1)
            content_grid.add_row(*main_blocks[:2])
            parts.append(content_grid)
            parts.extend(main_blocks[2:])
        else:
            parts.extend(main_blocks)

        parts.extend(extra_parts)

        return RichGroup(*parts)


# ── main app ───────────────────────────────────────────────


class RunningTUI(App):
    """running_page TUI — browse your running history in the terminal."""

    CSS = """
    Screen { background: #171717; color: #d4d4d8; }

    /* ── nav sidebar ─────────────────────────────────── */
    #nav-sidebar { width: 18; min-width: 18; padding: 1 1; }
    #nav-sidebar > Button {
        background: transparent;
        border: none;
        text-style: none;
        color: #d4d4d8;
        height: 3;
        width: 1fr;
        content-align: left middle;
        padding: 0 2;
        margin: 0 0 1 0;
    }
    #nav-sidebar > Button:hover {
        background: #262626;
        border-left: thick #ccd94a;
    }
    #nav-sidebar > Button:focus {
        background: #3a3a22;
        color: #e0ed5e;
        border-left: thick #e0ed5e;
    }
    #nav-sidebar > Button.nav-active {
        background: #3a3a22;
        color: #e0ed5e;
        text-style: bold;
        border-left: thick #e0ed5e;
    }

    /* ── filter bar ──────────────────────────────────── */
    #filter-bar {
        dock: top;
        height: 4;
        padding: 0 2;
        background: #171717;
        border: none;
    }
    #filter-row {
        height: 3;
        align: left middle;
        padding: 0;
    }
    #fl-brand, #fl-summary {
        height: 3;
        margin: 0 1 0 0;
        padding: 0 2;
        background: #202020;
        border: round #303030;
        content-align: center middle;
    }
    #fl-brand {
        width: 20;
        color: #e0ed5e;
        text-style: bold;
        content-align: left middle;
    }
    #fl-summary {
        width: 18;
        color: #8a8a8a;
        content-align: left middle;
    }
    .filter-chip {
        width: 9;
        height: 3;
        padding: 0 2;
        margin: 0 1 0 0;
        background: #202020;
        color: #d4d4d8;
        border: round #343434;
        text-style: bold;
        content-align: center middle;
    }
    #fl-year {
        width: 10;
        background: #2b3016;
        color: #e0ed5e;
        border: round #636a2d;
    }
    #fl-type { width: 8; }
    .filter-chip:hover {
        background: #2b2b2b;
        color: #f0f777;
        border: round #5b5b5b;
    }
    .filter-chip:focus {
        background: #323717;
        color: #f0f777;
        border: round #8d9740;
    }

    #list-left { width: 45%; min-width: 40; border: solid #404040; background: #171717; }
    #list-right { width: 55%; min-width: 30; }

    #detail-panel {
        height: auto;
        border: solid #404040; background: #171717;
        padding: 0 1;
    }
    #route-panel { border: solid #404040; background: #171717; }
    DataTable { height: 100%; }

    DataTable > .datatable--header { background: #262626; color: #d4d4d8; }
    DataTable > .datatable--cursor { background: #3a3a22; color: #e0ed5e; }
    DataTable > .datatable--hover { background: #262626; }

    /* ── detail / stats / places / grid views ────────── */
    #main-area { height: 1fr; }
    #view-list { height: 1fr; padding: 1 2 0 2; }
    #view-stats { height: 1fr; overflow-y: auto; padding: 1 2 0 2; }
    #stats-body { height: auto; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "toggle_sort", "Sort"),
        Binding("n", "next_run", "Next"),
        Binding("p", "prev_run", "Prev"),
        Binding("left", "older_year", "Older Year", priority=True),
        Binding("right", "newer_year", "Newer Year", priority=True),
        Binding("y", "next_year", "Year"),
        Binding("t", "next_type", "Type"),
        Binding("1", "view_list", "List"),
        Binding("2", "view_stats", "Stats"),
    ]

    def __init__(self, data_path: str | Path | None = None) -> None:
        super().__init__()
        self.data_path = Path(data_path) if data_path else find_data_file()
        self.activities: list[Activity] = []
        self._displayed_activities: list[Activity] = []
        self.data: AggregatedData | None = None
        self.filtered_data: AggregatedData | None = None
        self._sort_asc = False
        self._active_filters: list[FilterFunc] = []
        self._current_view = "stats"

    # ── lifecycle ───────────────────────────────────────────

    def compose(self) -> ComposeResult:
        with Horizontal():
            yield NavSidebar(id="nav")
            with Vertical(id="main-area"):
                yield FilterBar(id="filter-bar", years=[], types=[])
                # all views stacked; only one visible at a time
                with Horizontal(id="view-list"):
                    with Vertical(id="list-left"):
                        yield DataTable(
                            id="run-table",
                            cursor_type="row",
                            zebra_stripes=True,
                        )
                    with Vertical(id="list-right"):
                        yield RunDetailPanel(id="detail-panel")
                        with Vertical(id="route-panel"):
                            yield RouteMapWidget(id="route-map")
                yield StatsView(id="view-stats")

    def on_mount(self) -> None:
        self.title = "running_page TUI"
        try:
            self.activities = load_activities(self.data_path)
            self.data = aggregate_activities(self.activities)
            self.filtered_data = self.data
        except Exception as exc:
            self.notify(f"Failed to load data: {exc}", severity="error", timeout=10)
            return

        # init filter bar — default to most recent year
        self._sync_filter_bar(default_latest_year=True)

        # populate table
        table = self.query_one("#run-table", DataTable)
        table.add_columns("#", "Date", "Distance", "Time", "Pace", "Type", "HR")
        self._rebuild_filters()

        self.notify(f"Loaded {len(self.activities)} activities", timeout=3)

        self._show_view("list")
        table.focus()

    # ── view switching ──────────────────────────────────────

    def _show_view(self, name: str) -> None:
        self._current_view = name
        for vid in ["view-list", "view-stats"]:
            w = self.query_one(f"#{vid}")
            w.display = vid == f"view-{name}"
        self.query_one(NavSidebar).highlight(name)

    # ── table helpers ───────────────────────────────────────

    def _populate_table(self, table: DataTable, activities: list[Activity]) -> None:
        table.clear()
        rows: list[tuple[str, ...]] = []
        for i, a in enumerate(activities, 1):
            color = _type_color(a)
            hr = f"{a.average_heartrate:.0f}" if a.average_heartrate else "-"
            rows.append(
                (
                    str(i),
                    a.date_local,
                    f"{a.distance_km:.2f}",
                    a.formatted_time,
                    a.pace_min_km or "-",
                    f"[{color}]{a.sport_type_normalized}[/]",
                    hr,
                )
            )
        table.add_rows(rows)

    def _select_activity(self, index: int) -> None:
        activities = self._displayed_activities or self.activities
        if not activities or index < 0 or index >= len(activities):
            return
        a = activities[index]
        detail = self.query_one(RunDetailPanel)
        detail.activity = a
        detail.data = self.data
        rw = self.query_one(RouteMapWidget)
        rw.polyline_str = a.summary_polyline or ""
        rw.activity_name = a.name or ""
        rw.distance_km = a.distance_km

    def _sync_filter_bar(self, *, default_latest_year: bool) -> None:
        fb = self.query_one(FilterBar)
        years = self.data.years if self.data else []
        types = sorted(self.data.type_counts.keys()) if self.data else []
        current_year = fb.selected_year
        current_type = fb.selected_type
        selected_year = current_year if current_year in years else "All"
        if selected_year == "All" and default_latest_year and years:
            selected_year = years[0]
        fb.set_options(
            years,
            types,
            selected_year=selected_year,
            selected_type=current_type if current_type in types else "All",
        )

    def _overall_period_label(self) -> str:
        if not self.data or not self.data.first_date or not self.data.last_date:
            return ""
        fb = self.query_one(FilterBar)
        if fb.selected_year == "All":
            return f"{self.data.first_date[:4]}-{self.data.last_date[:4]}"

        start_year = fb.selected_year
        try:
            start_year_int = int(start_year)
        except ValueError:
            return start_year

        next_year = str(start_year_int + 1)
        if next_year in self.data.years:
            return f"{start_year}-{next_year}"
        return f"{start_year}-{start_year}"

    # ── filtering ───────────────────────────────────────────

    def _rebuild_filters(self) -> None:
        fb = self.query_one(FilterBar)
        filters: list[FilterFunc] = []
        if fb.selected_year != "All":
            filters.append(make_year_filter(fb.selected_year))
        if fb.selected_type != "All":
            filters.append(make_type_filter(fb.selected_type))
        self._active_filters = filters
        self._apply_filters()

    def _apply_filters(self) -> None:
        filtered = self.activities
        for f in self._active_filters:
            filtered = [a for a in filtered if f(a)]
        self._displayed_activities = filtered
        self.filtered_data = aggregate_activities(filtered)
        table = self.query_one("#run-table", DataTable)
        self._populate_table(table, filtered)
        stats_view = self.query_one(StatsView)
        stats_view.period_label = self._overall_period_label()
        stats_view.data = self.filtered_data
        if filtered:
            self._select_activity(0)
        else:
            self.query_one(RunDetailPanel).activity = None
            rw = self.query_one(RouteMapWidget)
            rw.polyline_str = ""
            rw.activity_name = ""
            rw.distance_km = 0.0
        total = len(self.activities)
        count = len(filtered)
        fb = self.query_one(FilterBar)
        year_prefix = f"{fb.selected_year}·" if fb.selected_year != "All" else ""
        summary = (
            f"{year_prefix}{count}/{total}"
            if count != total
            else f"{year_prefix}{total} · {self.data.total_distance:.0f}km"
        )
        fb.set_summary(summary)
        self.sub_title = (
            f"{fb.selected_year} · {count}/{total} activities"
            if count != total
            else f"{fb.selected_year} · {total} activities  ·  {self.data.total_distance:.0f} km total"
        )

    # ── message handlers ────────────────────────────────────

    def on_data_table_row_highlighted(self, event: DataTable.RowHighlighted) -> None:
        self._select_activity(event.cursor_row)

    def on_data_table_row_selected(self, event: DataTable.RowSelected) -> None:
        table = self.query_one("#run-table", DataTable)
        try:
            keys = list(table.rows.keys())
            idx = keys.index(event.row_key)
            self._select_activity(idx)
        except (ValueError, IndexError):
            pass

    def on_filter_bar_filter_changed(self, event: FilterBar.FilterChanged) -> None:
        self._rebuild_filters()

    def on_nav_sidebar_view_selected(self, event: NavSidebar.ViewSelected) -> None:
        name = event.view_name
        if name == "list":
            self.action_view_list()
        elif name == "stats":
            self.action_view_stats()

    # ── actions ─────────────────────────────────────────────

    def action_refresh(self) -> None:
        try:
            self.activities = load_activities(self.data_path)
            self.data = aggregate_activities(self.activities)
            self.filtered_data = self.data
            self._sync_filter_bar(default_latest_year=True)
            self._rebuild_filters()
            self.notify(f"Refreshed — {len(self.activities)} activities")
        except Exception as exc:
            self.notify(f"Refresh failed: {exc}", severity="error")

    def action_toggle_sort(self) -> None:
        self._sort_asc = not self._sort_asc
        self.activities.sort(
            key=lambda a: a.start_date_local,
            reverse=not self._sort_asc,
        )
        self._apply_filters()

    def action_next_run(self) -> None:
        if not self._displayed_activities:
            return
        table = self.query_one("#run-table", DataTable)
        cur = table.cursor_row
        nxt = min(cur + 1, len(self._displayed_activities) - 1)
        if nxt != cur:
            table.move_cursor(row=nxt)
            self._select_activity(nxt)

    def action_prev_run(self) -> None:
        if not self._displayed_activities:
            return
        table = self.query_one("#run-table", DataTable)
        cur = table.cursor_row
        prv = max(cur - 1, 0)
        if prv != cur:
            table.move_cursor(row=prv)
            self._select_activity(prv)

    def action_next_year(self) -> None:
        self.query_one(FilterBar).cycle_year()
        self._rebuild_filters()

    def action_older_year(self) -> None:
        self.query_one(FilterBar).previous_year()
        self._rebuild_filters()

    def action_newer_year(self) -> None:
        self.query_one(FilterBar).next_year()
        self._rebuild_filters()

    def action_next_type(self) -> None:
        self.query_one(FilterBar).next_type()
        self._rebuild_filters()

    def action_view_list(self) -> None:
        self._show_view("list")
        self.query_one("#run-table", DataTable).focus()

    def action_view_stats(self) -> None:
        self._show_view("stats")
        self._sync_view_data()
        self.query_one(StatsView).focus()

    def _sync_view_data(self) -> None:
        if self._current_view == "stats" and self.filtered_data:
            self.query_one(StatsView).data = self.filtered_data


# ── entry point ────────────────────────────────────────────


def main() -> None:
    import sys

    path = sys.argv[1] if len(sys.argv) > 1 else None
    app = RunningTUI(path)
    app.run()


if __name__ == "__main__":
    main()
