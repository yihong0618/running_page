"""Data loading, aggregation, and filtering for running_page TUI."""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, timedelta
from pathlib import Path
from typing import Callable, Optional


# ── constants matching web UI ──────────────────────────────

DIST_UNIT = "km"
M_TO_DIST = 1000.0

FULL_MARATHON = 42.0  # km
HALF_MARATHON = 21.0  # km

PERIOD_RANGES: list[tuple[str, int, int]] = [
    ("Morning", 0, 10),
    ("Midday", 10, 14),
    ("Afternoon", 14, 18),
    ("Evening", 18, 21),
    ("Night", 21, 24),
]

SPORT_TYPE_ALIASES: dict[str, str] = {
    "Run": "Run",
    "running": "Run",
    "Ride": "Ride",
    "cycling": "Ride",
    "Hike": "Hike",
    "hiking": "Hike",
    "Walk": "Walk",
    "walking": "Walk",
    "Swim": "Swim",
    "swimming": "Swim",
    "Workout": "Workout",
    "Ski": "Ski",
    "skiing": "Ski",
}


# ── activity dataclass ─────────────────────────────────────


@dataclass
class Activity:
    run_id: int
    name: str
    distance: float  # metres
    moving_time: str  # "HH:MM:SS" or "X days, HH:MM:SS"
    type: str
    subtype: Optional[str]
    start_date: str  # UTC
    start_date_local: str  # "YYYY-MM-DD HH:MM:SS"
    location_country: Optional[str]
    summary_polyline: Optional[str]
    average_heartrate: Optional[float]
    elevation_gain: Optional[float]
    average_speed: float  # m/s
    streak: int

    # ── computed properties ────────────────────────────────

    @property
    def distance_km(self) -> float:
        return self.distance / 1000

    @property
    def year(self) -> str:
        return self.start_date_local[:4]

    @property
    def date_local(self) -> str:
        return self.start_date_local[:10]

    @property
    def date_obj(self) -> date:
        return date.fromisoformat(self.date_local)

    @property
    def hour(self) -> int:
        return int(self.start_date_local[11:13])

    @property
    def period(self) -> str:
        h = self.hour
        for name, lo, hi in PERIOD_RANGES:
            if lo <= h < hi:
                return name
        return "Night"

    @property
    def period_label(self) -> str:
        labels = {
            "Morning": "清晨跑步",
            "Midday": "午间跑步",
            "Afternoon": "午后跑步",
            "Evening": "傍晚跑步",
            "Night": "夜晚跑步",
        }
        return labels.get(self.period, self.period)

    @property
    def has_route(self) -> bool:
        return bool(self.summary_polyline)

    @property
    def formatted_time(self) -> str:
        parts = self.moving_time.split(":")
        if len(parts) == 3:
            h, m, s = int(parts[0]), int(parts[1]), int(parts[2])
            if h > 0:
                return f"{h}h{m}m"
            return f"{m}m{s}s"
        return self.moving_time

    @property
    def moving_seconds(self) -> int:
        parts = self.moving_time.split(":")
        if len(parts) == 3:
            return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])
        if "days" in self.moving_time or "day" in self.moving_time:
            # "X days, HH:MM:SS"
            try:
                day_part, time_part = self.moving_time.split(", ")
                days = int(day_part.split()[0])
                h, m, s = [int(x) for x in time_part.split(":")]
                return days * 86400 + h * 3600 + m * 60 + s
            except (ValueError, IndexError):
                pass
        return 0

    @property
    def pace_min_km(self) -> Optional[str]:
        if self.distance <= 0:
            return None
        secs = self.moving_seconds
        if secs <= 0:
            return None
        pace = secs / self.distance_km
        return f"{int(pace // 60)}:{int(pace % 60):02d}"

    @property
    def pace_seconds_per_km(self) -> Optional[float]:
        if self.distance <= 0:
            return None
        secs = self.moving_seconds
        if secs <= 0:
            return None
        return secs / self.distance_km

    # ── location parsing ───────────────────────────────────

    @property
    def city(self) -> str:
        loc = self.location_country
        if not loc:
            return ""
        parts = [p.strip() for p in loc.split(",")]
        # Chinese address: city is typically 3rd from end
        # e.g. "..., 沈阳市, 辽宁省, 110142, 中国"
        for p in reversed(parts):
            if p.endswith("市") or p.endswith("县"):
                return p
        if len(parts) >= 3:
            return parts[-3]
        return parts[0] if parts else ""

    @property
    def province(self) -> str:
        loc = self.location_country
        if not loc:
            return ""
        parts = [p.strip() for p in loc.split(",")]
        for p in reversed(parts):
            if p.endswith("省") or p.endswith("自治区") or p.endswith("特别行政区"):
                return p
        if len(parts) >= 2:
            return parts[-2]
        return ""

    @property
    def country(self) -> str:
        loc = self.location_country
        if not loc:
            return ""
        parts = [p.strip() for p in loc.split(",")]
        country = parts[-1] if parts else ""
        country_std = {
            "中国": "中国",
            "美利坚合众国": "美国",
            "United States": "美国",
            "日本": "日本",
            "대한민국": "韩国",
        }
        return country_std.get(country, country)

    # ── race classification ────────────────────────────────

    @property
    def race_label(self) -> Optional[str]:
        km = self.distance_km
        if km >= FULL_MARATHON:
            return "全程马拉松"
        if km >= HALF_MARATHON:
            return "半程马拉松"
        if km >= 10:
            return "10K"
        return None

    @property
    def sport_type_normalized(self) -> str:
        return SPORT_TYPE_ALIASES.get(self.type, self.type)


# ── filtering ──────────────────────────────────────────────


FilterFunc = Callable[[Activity], bool]


def make_year_filter(year: str) -> FilterFunc:
    return lambda a: a.year == year


def make_type_filter(sport_type: str) -> FilterFunc:
    st = sport_type.lower()
    return lambda a: SPORT_TYPE_ALIASES.get(a.type, a.type).lower() == st


def make_city_filter(city: str) -> FilterFunc:
    return lambda a: city in (a.city or "")


def make_period_filter(period: str) -> FilterFunc:
    return lambda a: a.period_label == period


def make_search_filter(query: str) -> FilterFunc:
    q = query.lower()
    return lambda a: (
        q in (a.name or "").lower()
        or q in (a.location_country or "").lower()
        or q in a.type.lower()
    )


def filter_activities(
    activities: list[Activity],
    filters: list[FilterFunc],
) -> list[Activity]:
    if not filters:
        return activities
    return [a for a in activities if all(f(a) for f in filters)]


# ── aggregation ────────────────────────────────────────────


@dataclass
class YearStats:
    year: str
    count: int = 0
    total_distance: float = 0.0  # km
    total_time_sec: float = 0.0
    total_elevation: float = 0.0
    heart_rate_sum: float = 0.0
    heart_rate_count: int = 0
    max_distance: float = 0.0
    max_speed: float = 0.0
    streak: int = 0
    daily_distances: dict[str, float] = field(default_factory=dict)

    @property
    def avg_pace(self) -> Optional[str]:
        if self.total_distance <= 0 or self.total_time_sec <= 0:
            return None
        pace_sec = self.total_time_sec / self.total_distance
        return f"{int(pace_sec // 60)}:{int(pace_sec % 60):02d}"

    @property
    def avg_heart_rate(self) -> Optional[float]:
        if self.heart_rate_count <= 0:
            return None
        return self.heart_rate_sum / self.heart_rate_count

    @property
    def avg_speed_kmh(self) -> Optional[float]:
        if self.total_time_sec <= 0:
            return None
        return self.total_distance / (self.total_time_sec / 3600)


@dataclass
class LocationStats:
    city: str
    province: str = ""
    country: str = ""
    total_distance: float = 0.0
    count: int = 0
    total_elevation: float = 0.0


@dataclass
class AggregatedData:
    """Pre-computed aggregations over all activities."""

    activities: list[Activity]
    years: list[str]
    year_stats: dict[str, YearStats]

    # location
    cities: dict[str, float]  # name -> total km
    provinces: dict[str, float]
    countries: dict[str, float]
    city_details: dict[str, LocationStats]

    # periods
    periods: dict[str, int]  # label -> count

    # overall
    total_distance: float  # km
    total_time_sec: float
    total_elevation: float
    total_count: int
    total_heart_rate_sum: float
    total_heart_rate_count: int
    total_max_distance: float
    total_max_speed: float

    # activity type breakdown
    type_counts: dict[str, int]
    type_distances: dict[str, float]

    # date range
    first_date: Optional[str]
    last_date: Optional[str]

    @property
    def overall_avg_pace(self) -> Optional[str]:
        if self.total_distance <= 0 or self.total_time_sec <= 0:
            return None
        pace_sec = self.total_time_sec / self.total_distance
        return f"{int(pace_sec // 60)}:{int(pace_sec % 60):02d}"

    @property
    def overall_avg_hr(self) -> Optional[float]:
        if self.total_heart_rate_count <= 0:
            return None
        return self.total_heart_rate_sum / self.total_heart_rate_count

    @property
    def races(self) -> dict[str, int]:
        counts: dict[str, int] = {"全程马拉松": 0, "半程马拉松": 0, "10K": 0}
        for a in self.activities:
            label = a.race_label
            if label in counts:
                counts[label] += 1
        return counts

    def filter(self, filters: list[FilterFunc]) -> AggregatedData:
        """Return a new AggregatedData for the filtered subset."""
        filtered = filter_activities(self.activities, filters)
        return aggregate_activities(filtered)

    def year_runs(self, year: str) -> list[Activity]:
        return [a for a in self.activities if a.year == year]


def _parse_city_province_country(a: Activity) -> tuple[str, str, str]:
    return a.city, a.province, a.country


def aggregate_activities(activities: list[Activity]) -> AggregatedData:
    """Compute all aggregations from a list of activities."""

    years_set: set[str] = set()
    cities: dict[str, float] = defaultdict(float)
    provinces: dict[str, float] = defaultdict(float)
    countries: dict[str, float] = defaultdict(float)
    city_details: dict[str, LocationStats] = {}
    periods: dict[str, int] = defaultdict(int)
    type_counts: dict[str, int] = defaultdict(int)
    type_distances: dict[str, float] = defaultdict(float)
    year_stats: dict[str, YearStats] = {}

    total_dist = 0.0
    total_time = 0.0
    total_elev = 0.0
    total_hr_sum = 0.0
    total_hr_cnt = 0
    total_max_dist = 0.0
    total_max_speed = 0.0
    first_date_val: Optional[str] = None
    last_date_val: Optional[str] = None

    for a in activities:
        y = a.year
        years_set.add(y)
        d_km = a.distance_km
        secs = a.moving_seconds

        # year stats
        if y not in year_stats:
            year_stats[y] = YearStats(year=y)
        ys = year_stats[y]
        ys.year = y
        ys.count += 1
        ys.total_distance += d_km
        ys.total_time_sec += secs
        if a.elevation_gain:
            ys.total_elevation += a.elevation_gain
        if a.average_heartrate:
            ys.heart_rate_sum += a.average_heartrate
            ys.heart_rate_count += 1
        if d_km > ys.max_distance:
            ys.max_distance = d_km
        speed_kmh = a.average_speed * 3.6
        if speed_kmh > ys.max_speed:
            ys.max_speed = speed_kmh
        if a.streak > ys.streak:
            ys.streak = a.streak
        ys.daily_distances[a.date_local] = (
            ys.daily_distances.get(a.date_local, 0) + d_km
        )

        # location
        city, prov, ctry = _parse_city_province_country(a)
        if city:
            cities[city] += d_km
            if city not in city_details:
                city_details[city] = LocationStats(
                    city=city, province=prov, country=ctry
                )
            city_details[city].total_distance += d_km
            city_details[city].count += 1
            if a.elevation_gain:
                city_details[city].total_elevation += a.elevation_gain
        if prov:
            provinces[prov] += d_km
        if ctry:
            countries[ctry] += d_km

        # period
        periods[a.period_label] += 1

        # type
        st = a.sport_type_normalized
        type_counts[st] += 1
        type_distances[st] += d_km

        # overall
        total_dist += d_km
        total_time += secs
        if a.elevation_gain:
            total_elev += a.elevation_gain
        if a.average_heartrate:
            total_hr_sum += a.average_heartrate
            total_hr_cnt += 1
        if d_km > total_max_dist:
            total_max_dist = d_km
        if speed_kmh > total_max_speed:
            total_max_speed = speed_kmh

        # date range
        dl = a.date_local
        if first_date_val is None or dl < first_date_val:
            first_date_val = dl
        if last_date_val is None or dl > last_date_val:
            last_date_val = dl

    return AggregatedData(
        activities=activities,
        years=sorted(years_set, reverse=True),
        year_stats={y: year_stats[y] for y in sorted(year_stats, reverse=True)},
        cities=dict(sorted(cities.items(), key=lambda x: -x[1])),
        provinces=dict(sorted(provinces.items(), key=lambda x: -x[1])),
        countries=dict(sorted(countries.items(), key=lambda x: -x[1])),
        city_details=city_details,
        periods=dict(sorted(periods.items(), key=lambda x: -x[1])),
        total_distance=total_dist,
        total_time_sec=total_time,
        total_elevation=total_elev,
        total_count=len(activities),
        total_heart_rate_sum=total_hr_sum,
        total_heart_rate_count=total_hr_cnt,
        total_max_distance=total_max_dist,
        total_max_speed=total_max_speed,
        type_counts=type_counts,
        type_distances=type_distances,
        first_date=first_date_val,
        last_date=last_date_val,
    )


# ── contribution grid data ─────────────────────────────────


@dataclass
class GridCell:
    date_str: str
    distance_km: float
    level: int  # 0-4


@dataclass
class ContributionGrid:
    """Data for rendering a GitHub-style contribution grid."""

    year: str
    weeks: list[list[Optional[GridCell]]]  # 7 rows x N cols
    month_labels: list[tuple[int, int, str]]  # (col_index, span, name)

    @property
    def max_level(self) -> int:
        return 4


def build_contribution_grid(activities: list[Activity], year: str) -> ContributionGrid:
    """Build a contribution grid for the given year."""
    daily: dict[str, float] = defaultdict(float)
    for a in activities:
        if a.year == year:
            daily[a.date_local] += a.distance_km

    if not daily:
        return ContributionGrid(year=year, weeks=[], month_labels=[])

    # Find the start and end of the year
    try:
        start = date(int(year), 1, 1)
        end = date(int(year), 12, 31)
    except (ValueError, OverflowError):
        return ContributionGrid(year=year, weeks=[], month_labels=[])

    # Find the Monday on or before Jan 1
    start_weekday = start.weekday()  # 0=Mon
    grid_start = start - timedelta(days=start_weekday)

    # Build the grid
    weeks: list[list[Optional[GridCell]]] = [[None] * 7 for _ in range(53)]
    current = grid_start
    max_dist = max(daily.values()) if daily else 1

    for col in range(53):
        for row in range(7):
            if current > end:
                weeks[col][row] = None
            elif current < start:
                weeks[col][row] = GridCell(
                    date_str=current.isoformat(),
                    distance_km=0.0,
                    level=0,
                )
            else:
                ds = current.isoformat()
                d = daily.get(ds, 0.0)
                level = 0
                if d > 0:
                    ratio = d / max_dist
                    if ratio > 0.75:
                        level = 4
                    elif ratio > 0.5:
                        level = 3
                    elif ratio > 0.25:
                        level = 2
                    else:
                        level = 1
                weeks[col][row] = GridCell(date_str=ds, distance_km=d, level=level)
            current += timedelta(days=1)
            if current > end:
                break
        if current > end:
            break

    # Remove trailing empty columns
    while weeks and all(c is None for c in weeks[-1]):
        weeks.pop()

    # Month labels: find the first column where each month appears
    month_labels: list[tuple[int, int, str]] = []
    month_names = [
        "1月",
        "2月",
        "3月",
        "4月",
        "5月",
        "6月",
        "7月",
        "8月",
        "9月",
        "10月",
        "11月",
        "12月",
    ]
    seen_months: set[int] = set()
    for col_idx, col in enumerate(weeks):
        for cell in col:
            if cell and cell.date_str >= start.isoformat():
                m = int(cell.date_str[5:7])
                if m not in seen_months:
                    seen_months.add(m)
                    month_labels.append((col_idx, 1, month_names[m - 1]))
                break

    return ContributionGrid(year=year, weeks=weeks, month_labels=month_labels)


# ── loading ────────────────────────────────────────────────


def load_activities(json_path: str | Path) -> list[Activity]:
    path = Path(json_path)
    if not path.exists():
        raise FileNotFoundError(f"Activities file not found: {path}")
    with open(path) as f:
        data = json.load(f)
    return [Activity(**item) for item in data]


def find_data_file() -> Path:
    candidates = [
        Path("src/static/activities.json"),
        Path("../src/static/activities.json"),
        Path(__file__).resolve().parent.parent.parent
        / "src"
        / "static"
        / "activities.json",
    ]
    for p in candidates:
        if p.exists():
            return p.resolve()
    raise FileNotFoundError(
        "Could not find activities.json. Run data sync first or specify path."
    )
