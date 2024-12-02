from typing import List, Tuple
import polyline
import os
from haversine import haversine

try:
    IGNORE_POLYLINE = (
        polyline.decode(os.getenv("IGNORE_POLYLINE"))
        if os.getenv("IGNORE_POLYLINE")
        else []
    )
except Exception:
    print("IGNORE_POLYLINE is not a valid polyline")
    exit(1)

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


def range_hiding(
    polyline: List[Tuple[float]], points: List[Tuple[float]], distance: int
) -> List[Tuple[float]]:
    return [
        point
        for point in polyline
        if not point_in_list_points_range(point, points, distance)
    ]


def start_end_hiding(polyline: List[Tuple[float]], distance: int) -> List[Tuple[float]]:
    start_index, end_index = 0, len(polyline) - 1

    starting_distance = 0
    for i in range(1, len(polyline)):
        starting_distance += haversine(polyline[i], polyline[i - 1])
        if starting_distance > distance:
            start_index = i
            break

    ending_distance = 0
    for i in range(len(polyline) - 2, -1, -1):
        ending_distance += haversine(polyline[i], polyline[i + 1])
        if ending_distance > distance:
            end_index = i
            break

    if start_index >= end_index:
        return []

    return polyline[start_index : end_index + 1]


def filter_out(polyline_str):
    if not polyline_str:
        return
    pl = polyline.decode(polyline_str)
    if not pl:
        return polyline_str

    new_pl = start_end_hiding(pl, IGNORE_START_END_RANGE)
    new_pl = range_hiding(new_pl, IGNORE_POLYLINE, IGNORE_RANGE)

    if not new_pl:
        return
    return polyline.encode(new_pl)
