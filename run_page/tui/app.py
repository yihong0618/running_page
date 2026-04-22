"""running_page TUI — full-featured terminal UI for browsing running activities."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from rich.console import Group as RichGroup
from rich.panel import Panel
from rich.table import Table as RichTable
from rich.text import Text as RichText
from textual.app import App, ComposeResult
from textual.message import Message
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.reactive import reactive
from textual.widget import Widget
from textual.widgets import Button, DataTable, Input, Label

from .braille import render_polyline
from .data import (
    Activity,
    AggregatedData,
    FilterFunc,
    YearStats,
    aggregate_activities,
    find_data_file,
    load_activities,
    make_search_filter,
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


def _render_stats_cards(data: AggregatedData) -> RichTable:
    def metric_panel(title: str, value: str, accent: str = TEXT_COLOR) -> Panel:
        body = RichText()
        body.append(title + "\n", style=MUTED_TEXT_COLOR)
        body.append(value, style=f"bold {accent}")
        return Panel(body, border_style=CARD_BORDER_COLOR, padding=(0, 1))

    grid = RichTable.grid(expand=True, padding=(0, 1))
    grid.add_column(ratio=1)
    grid.add_column(ratio=1)
    grid.add_row(
        metric_panel(
            "Distance", f"{fmt_num(data.total_distance, 1)} km", PRIMARY_COLOR
        ),
        metric_panel("Runs", f"{data.total_count}"),
    )
    grid.add_row(
        metric_panel("Avg Pace", f"{data.overall_avg_pace or '-'} /km"),
        metric_panel("Max Distance", f"{data.total_max_distance:.1f} km"),
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


def _section_title(title: str) -> RichText:
    return RichText(f"{title}\n", style=f"bold {PRIMARY_COLOR}")


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

    def render(self) -> RichTable | RichText:
        if self.activity is None:
            return RichText(
                "  Select a run to view details", style=f"dim {MUTED_TEXT_COLOR}"
            )
        a = self.activity
        color = _type_color(a)
        t = RichTable(show_header=False, border_style=CARD_BORDER_COLOR, padding=(0, 1))
        t.add_column("", style=f"bold {PRIMARY_COLOR}")
        t.add_column("")
        t.add_row("Name", a.name or "-")
        t.add_row("Date", a.date_local)
        t.add_row(
            "Type",
            f"[{color}]{a.type}[/]" + (f" ({a.subtype})" if a.subtype else ""),
        )
        t.add_row("Distance", f"{a.distance_km:.2f} km")
        t.add_row("Time", a.formatted_time)
        pace = a.pace_min_km
        t.add_row("Pace", f"{pace} /km" if pace else "-")
        if a.average_heartrate:
            t.add_row("Heart Rate", f"{a.average_heartrate:.0f} bpm")
        if a.elevation_gain:
            t.add_row("Elevation", f"{a.elevation_gain:.0f} m")
        t.add_row("Speed", f"{a.average_speed:.2f} m/s")
        if a.location_country:
            t.add_row("Location", a.location_country)
        t.add_row("Route", "Yes" if a.has_route else "No")
        if a.race_label:
            t.add_row("Race", f"[bold {SPECIAL_COLOR}]{a.race_label}[/]")
        return t


# ── filter bar ─────────────────────────────────────────────


class FilterBar(Widget):
    """Top bar with year selector, type filter, and search."""

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
            with Horizontal(id="filter-meta"):
                yield Label("running_page", id="fl-brand")
                yield Label("0 activities", id="fl-summary")
            with Horizontal(classes="filter-group compact-group", id="fl-year-group"):
                yield Button(
                    self._format_year_label(), id="fl-year", classes="filter-chip"
                )
            with Horizontal(classes="filter-group compact-group", id="fl-type-group"):
                yield Button(
                    self._format_type_label(), id="fl-type", classes="filter-chip"
                )
            with Horizontal(classes="filter-group search-group", id="fl-search-group"):
                yield Input(placeholder="Search...", id="fl-search")

    def on_mount(self) -> None:
        self.styles.padding = (0, 1)
        self.styles.background = SURFACE_COLOR

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "fl-year":
            self.next_year()
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

    @property
    def search_query(self) -> str:
        inp = self.query_one("#fl-search", Input)
        return inp.value.strip()

    def _format_year_label(self) -> str:
        return self.selected_year

    def _format_type_label(self) -> str:
        return self.selected_type

    def next_year(self) -> None:
        self._year_idx = (self._year_idx + 1) % len(self._years)
        self.query_one("#fl-year", Button).label = self._format_year_label()

    def next_type(self) -> None:
        self._type_idx = (self._type_idx + 1) % len(self._types)
        self.query_one("#fl-type", Button).label = self._format_type_label()

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
        self.query_one("#fl-year", Button).label = self._format_year_label()
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


class StatsView(Widget):
    """Overall and per-year statistics."""

    data: Optional[AggregatedData] = reactive(None)

    def render(self) -> RichText | RichGroup:
        if self.data is None:
            return RichText("  Loading...", style=f"dim {MUTED_TEXT_COLOR}")

        d = self.data
        parts: list = [
            RichText("\n  Overview\n", style=f"bold {PRIMARY_COLOR}"),
            _render_stats_cards(d),
        ]

        # overall stats
        tbl = RichTable(
            show_header=False, border_style=CARD_BORDER_COLOR, padding=(0, 2)
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
        if d.first_date and d.last_date:
            tbl.add_row("Period", f"{d.first_date[:4]} – {d.last_date[:4]}")
        left_parts: list = [_section_title("Overall Statistics"), tbl]

        # races
        races = d.races
        if any(races.values()):
            left_parts.append(RichText("\n", style=TEXT_COLOR))
            left_parts.append(_section_title("Races"))
            rt = RichTable(
                show_header=False, border_style=SPECIAL_COLOR, padding=(0, 2)
            )
            rt.add_column("", style="bold")
            rt.add_column("")
            rt.add_row("Full Marathons", str(races["全程马拉松"]))
            rt.add_row("Half Marathons", str(races["半程马拉松"]))
            rt.add_row("10K+ Runs", str(races["10K"]))
            left_parts.append(rt)

        # activity type breakdown
        if d.type_counts:
            left_parts.append(RichText("\n", style=TEXT_COLOR))
            left_parts.append(_section_title("By Activity Type"))
            tt = RichTable(
                show_header=False, border_style=CARD_BORDER_COLOR, padding=(0, 2)
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
            left_parts.append(tt)

        # per-year
        if d.year_stats:
            left_parts.append(RichText("\n", style=TEXT_COLOR))
            left_parts.append(_section_title("Per-Year Breakdown"))
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
            left_parts.append(yt)

        # monthly chart for the current / latest year in view
        right_parts: list = []
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
            right_parts.append(_section_title("Trends"))
            if monthly_distance_chart is not None:
                right_parts.append(monthly_distance_chart)
            if monthly_count_chart is not None:
                right_parts.append(monthly_count_chart)
            if distribution_panel is not None:
                right_parts.append(distribution_panel)

        content_grid = RichTable.grid(expand=True, padding=(0, 1))
        content_grid.add_column(ratio=7)
        content_grid.add_column(ratio=5)
        content_grid.add_row(
            RichGroup(*left_parts),
            RichGroup(*right_parts) if right_parts else RichText(""),
        )
        parts.append(content_grid)

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
        height: 3;
        padding: 0 1;
        background: #171717;
        border-bottom: solid #2f2f2f;
    }
    #filter-row {
        height: 3;
        align: left middle;
        padding: 0;
    }
    #filter-meta {
        width: auto;
        min-width: 18;
        height: 3;
        align: left middle;
    }
    #fl-brand {
        width: auto;
        min-width: 0;
        height: 3;
        color: #e0ed5e;
        text-style: bold;
        padding: 0 1 0 0;
        content-align: left middle;
    }
    #fl-summary {
        width: auto;
        height: 3;
        color: #8a8a8a;
        content-align: left middle;
    }
    .filter-group {
        height: 3;
        width: auto;
        min-width: 5;
        margin: 0 1 0 0;
        align: center middle;
    }
    #fl-year-group {
        width: auto;
        min-width: 5;
    }
    #fl-type-group {
        width: auto;
        min-width: 5;
    }
    .search-group {
        width: 12;
        margin: 0;
    }
    .filter-chip {
        width: auto;
        min-width: 5;
        height: 1;
        padding: 0 1;
        margin: 0;
        background: #222222;
        color: #d4d4d8;
        border: none;
        text-style: bold;
        content-align: center middle;
    }
    .filter-chip:hover {
        background: #2c2c2c;
        color: #e0ed5e;
    }
    .filter-chip:focus {
        background: #2f3218;
        color: #e0ed5e;
    }
    .search-group > Input {
        width: 1fr;
        height: 3;
        border: round #343434;
        background: transparent;
        color: #d4d4d8;
        padding: 0 1;
    }
    .search-group > Input:focus {
        background: #202015;
        border: round #ccd94a;
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
    #view-list { height: 1fr; }
    #view-stats { height: 1fr; overflow-y: auto; padding: 0 2; }
    """

    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("r", "refresh", "Refresh"),
        Binding("s", "toggle_sort", "Sort"),
        Binding("n", "next_run", "Next"),
        Binding("p", "prev_run", "Prev"),
        Binding("slash", "focus_search", "Search", key_display="/"),
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
        self.query_one(RunDetailPanel).activity = a
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

    # ── filtering ───────────────────────────────────────────

    def _rebuild_filters(self) -> None:
        fb = self.query_one(FilterBar)
        filters: list[FilterFunc] = []
        if fb.selected_year != "All":
            filters.append(make_year_filter(fb.selected_year))
        if fb.selected_type != "All":
            filters.append(make_type_filter(fb.selected_type))
        q = fb.search_query
        if q:
            filters.append(make_search_filter(q))
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
        self.query_one(StatsView).data = self.filtered_data
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

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if event.input.id == "fl-search":
            self._rebuild_filters()

    def on_input_changed(self, event: Input.Changed) -> None:
        if event.input.id == "fl-search":
            self._rebuild_filters()

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

    def action_focus_search(self) -> None:
        self.query_one("#fl-search", Input).focus()

    def action_next_year(self) -> None:
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
