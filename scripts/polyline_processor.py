from typing import List, Tuple
import polyline
import os
from haversine import haversine

IGNORE_POLYLINE = (
    polyline.decode(os.getenv("IGNORE_POLYLINE"))
    if os.getenv("IGNORE_POLYLINE")
    else []
)

try:
    IGNORE_RANGE = int(os.getenv("IGNORE_RANGE", "0")) / 1000
    IGNORE_START_END_RANGE = int(os.getenv("IGNORE_START_END_RANGE", "0")) / 1000
except ValueError:
    print("IGNORE_RANGE or IGNORE_START_END_RANGE is not a number")
    exit(1)


def point_distance_in_range(
    point: Tuple[float], center_point: Tuple[float], distance: int
) -> bool:
    return haversine(point, center_point) < distance


def point_in_list_points_range(
    point: Tuple[float], points: List[Tuple[float]], distance: int
) -> bool:
    return any([point_distance_in_range(point, p, distance) for p in points])


def filter_out(polyline_str):
    pl = polyline.decode(polyline_str)
    if not pl:
        return polyline_str
    start_point, end_point = pl[0], pl[-1]

    new_pl = []
    for point in pl:
        if point_in_list_points_range(
            point, [start_point, end_point], IGNORE_START_END_RANGE
        ):
            continue
        if point_in_list_points_range(point, IGNORE_POLYLINE, IGNORE_RANGE):
            continue

        new_pl.append(point)
    if not new_pl:
        return None

    return polyline.encode(new_pl)
