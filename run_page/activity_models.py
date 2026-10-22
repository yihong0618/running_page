"""Shared activity records produced by file loaders and sync providers."""

from dataclasses import dataclass
from datetime import timedelta


@dataclass(frozen=True)
class StartPoint:
    lat: float
    lon: float


@dataclass(frozen=True)
class RunMap:
    summary_polyline: str


@dataclass(frozen=True, kw_only=True)
class ActivityRecord:
    id: int | str
    name: str
    type: str | int
    subtype: str | int
    start_date: str
    start_date_local: str
    distance: float
    moving_time: timedelta
    elapsed_time: timedelta
    average_speed: float
    average_heartrate: float | None
    elevation_gain: float | None
    map: RunMap
    start_latlng: StartPoint | None
    end: str | None = None
    end_local: str | None = None
    length: float | None = None
    location_country: str | None = ""
    source: str | None = None
    gpx_file_path: str | None = None
