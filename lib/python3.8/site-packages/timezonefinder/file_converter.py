#!/usr/bin/python
# -*- coding:utf-8 -*-


"""
USAGE:

- download the latest timezones.geojson.zip file from github.com/evansiroky/timezone-boundary-builder/releases
- unzip and place the combined.json inside this timezonefinder folder
- run this file_converter.py as a script until the compilation of the binary files is completed.


IMPORTANT: all coordinates (floats) are being converted to int32 (multiplied by 10^7). This makes computations faster
and it takes lot less space, without loosing too much accuracy (min accuracy (=at the equator) is still 1cm !)

B = unsigned char (1byte = 8bit Integer)
H = unsigned short (2 byte integer)
I = unsigned 4byte integer
i = signed 4byte integer


Binaries being written:

[POLYGONS:] there are approx. 1k Polygons (evansiroky/timezone-boundary-builder 2017a)
poly_zone_ids: the related zone_id for every polygon ('<H')
poly_coord_amount: the amount of coordinates in every polygon ('<I')
poly_adr2data: address in poly_data.bin where data for every polygon starts ('<I')
poly_max_values: boundaries for every polygon ('<iiii': xmax, xmin, ymax, ymin)
poly_data: coordinates for every polygon (multiple times '<i') (for every polygon first all x then all y values!)
poly_nr2zone_id: the polygon number of the first polygon from every zone('<H')

[HOLES:] number of holes (162 evansiroky/timezone-boundary-builder 2018d)
hole_poly_ids: the related polygon_nr (=id) for every hole ('<H')
hole_coord_amount: the amount of coordinates in every hole ('<H')
hole_adr2data: address in hole_data.bin where data for every hole starts ('<I')
hole_data: coordinates for every hole (multiple times '<i')

[SHORTCUTS:] the surface of the world is split up into a grid of shortcut rectangles.
-> there are a total of 360 * NR_SHORTCUTS_PER_LNG * 180 * NR_SHORTCUTS_PER_LAT shortcuts
shortcut here means storing for every cell in a grid of the world map which polygons are located in that cell
they can therefore be used to drastically reduce the amount of polygons which need to be checked in order to
decide which timezone a point is located in.

the list of polygon ids in each shortcut is sorted after freq. of appearance of their zone id
the polygons of the least frequent zone come first
this is critical for ruling out zones faster (as soon as just polygons of one zone are left this zone can be returned)

shortcuts_entry_amount: the amount of polygons for every shortcut ('<H')
shortcuts_adr2data: address in shortcut_data.bin where data for every shortcut starts ('<I')
shortcuts_data: polygon numbers (ids) for every shortcut (multiple times '<H')
shortcuts_direct_id: the id of the most common zone in that shortcut,
                     a high number (with no corresponding zone) if no zone is present ('<H').
                     the majority of zones either have no polygons at all (sea) or just one zone.
                     this zone then can be instantly returned without actually testing polygons.
shortcuts_unique_id: the zone id if only polygons from one zone are present,
                     a high number (with no corresponding zone) if not ('<H').
                     this zone then can be instantly returned without actually testing polygons.
                    the majority of shortcuts either have no polygons at all (sea) or just one zone
                    (cf. statistics below)



statistics:
DATA WITH OCEANS (2020d):

... parsing done. found:
1,403 polygons from
451 timezones with
805 holes
151,050 maximal amount of coordinates in one polygon
21,495 maximal amount of coordinates in a hole polygon

calculating the shortcuts took: 0:01:21.594385

shortcut statistics:
highest entry amount is 49
frequencies of entry amounts (from 0 to max entries):
[0, 109402, 18113, 1828, 187, 35, 14, 6, 5, 3, 2, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 0, 1, 0, 0, 0, 0, 1, 1, 0,
    0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1]
relative accumulated frequencies [%]:
[0.0, 84.42, 98.39, 99.8, 99.95, 99.97, 99.98, 99.99, 99.99, 99.99, 100.0, ...
         100.0]
[100.0, 15.58, 1.61, 0.2, 0.05, 0.03, 0.02, 0.01, 0.01, 0.01, 0.0, ... 0.0]
0.0 % of all shortcuts are empty

highest amount of different zones in one shortcut is 7
frequencies of entry amounts (from 0 to max):
[0, 109403, 18489, 1572, 120, 13, 1, 2]
relative accumulated frequencies [%]:
[0.0, 84.42, 98.68, 99.9, 99.99, 100.0, 100.0, 100.0]
[100.0, 15.58, 1.32, 0.1, 0.01, 0.0, 0.0, 0.0]
--------------------------------

The number of filled shortcut zones are:  129600 (= 100.0 % of all shortcuts)
number of polygons: 1403
number of floats in all the polygons: 12,644,038 (2 per point)

the polygon data makes up 94.67 % of the data
the shortcuts make up 2.03 % of the data
holes make up 3.31 % of the data
"""

import json
from datetime import datetime
from math import ceil, floor
from os.path import abspath, join
from struct import pack

import path_modification  # noqa. to make timezonefinder package discoverable

from timezonefinder.global_settings import (
    BINARY_FILE_ENDING,
    DEBUG,
    DEBUG_POLY_STOP,
    DEFAULT_INPUT_PATH,
    DEFAULT_OUTPUT_PATH,
    DTYPE_FORMAT_H,
    DTYPE_FORMAT_I,
    DTYPE_FORMAT_SIGNED_I,
    HOLE_ADR2DATA,
    HOLE_COORD_AMOUNT,
    HOLE_DATA,
    HOLE_REGISTRY_FILE,
    INVALID_VALUE_DTYPE_H,
    NR_BYTES_H,
    NR_BYTES_I,
    NR_SHORTCUTS_PER_LAT,
    NR_SHORTCUTS_PER_LNG,
    POLY_ADR2DATA,
    POLY_COORD_AMOUNT,
    POLY_DATA,
    POLY_MAX_VALUES,
    POLY_NR2ZONE_ID,
    POLY_ZONE_IDS,
    SHORTCUTS_ADR2DATA,
    SHORTCUTS_DATA,
    SHORTCUTS_DIRECT_ID,
    SHORTCUTS_ENTRY_AMOUNT,
    SHORTCUTS_UNIQUE_ID,
    THRES_DTYPE_H,
    THRES_DTYPE_I,
    THRES_DTYPE_SIGNED_I_LOWER,
    THRES_DTYPE_SIGNED_I_UPPER,
    TIMEZONE_NAMES_FILE,
)

# keep in mind: the faster numba optimized helper fct. cannot be used here,
# because numpy classes are not being used at this stage yet!
from timezonefinder.helpers import coord2int, inside_polygon, int2coord

nr_of_polygons = -1
nr_of_zones = -1
all_tz_names = []
poly_zone_ids = []
poly_boundaries = []
polygons = []
polygon_lengths = []
nr_of_holes = 0
polynrs_of_holes = []
holes = []
all_hole_lengths = []
list_of_pointers = []
poly_nr2zone_id = []
shortcuts = {}


def x_shortcut(lng):
    # higher (=lng) means higher x shortcut: 0 (-180deg lng) -> 360 (180deg)
    # if lng < -180 or lng >= 180:
    # raise ValueError('longitude out of bounds', lng)
    return floor((lng + 180) * NR_SHORTCUTS_PER_LNG)


def y_shortcut(lat):
    # lower y (=lat) means higher y shortcut: 0 (90deg lat) -> 180 (-90deg)
    # if lat < -90 or lat >= 90:
    # raise ValueError('this latitude is out of bounds', lat)
    return floor((90 - lat) * NR_SHORTCUTS_PER_LAT)


def big_zone(xmax, xmin, ymax, ymin):
    # returns True if a zone with those boundaries could have more than 4 shortcuts
    return (
        xmax - xmin > 2 / NR_SHORTCUTS_PER_LNG
        and ymax - ymin > 2 / NR_SHORTCUTS_PER_LAT
    )


def percent(numerator, denominator):
    return round((numerator / denominator) * 100, 2)


def accumulated_frequency(int_list):
    out = []
    total = sum(int_list)
    acc = 0
    for e in int_list:
        acc += e
        out.append(percent(acc, total))

    return out


def ints_of(line=0):
    x_coords, y_coords = polygons[line]
    return [coord2int(x) for x in x_coords], [coord2int(x) for x in y_coords]


def contained(x, y, x_coords, y_coords):
    return inside_polygon(x, y, [x_coords, y_coords])


def unique(iterable):
    out = []
    for i in iterable:
        if i not in out:
            out.append(i)
    return out


def point_between(p1, p2):
    return p1[0] + (p2[0] - p1[0]) / 2, p1[1] + (p2[1] - p1[1]) / 2


def get_shortcuts(x, y):
    result = shortcuts.get((x, y))
    if result is None:
        return []
    else:
        return result


def _polygons(id_list):
    for i in id_list:
        yield polygons[i]


def not_empty(iterable):
    for _ in iterable:
        return True
    return False


def polys_of_one_zone():
    for i in range(nr_of_zones):
        start = poly_nr2zone_id[i]
        end = poly_nr2zone_id[i + 1]
        yield list(range(start, end))


def replace_entry(iterable, entry, substitute):
    for i in range(len(iterable)):
        if iterable[i] == entry:
            iterable[i] = substitute
    return iterable


def _holes_in_poly(poly_nr):
    i = 0
    for nr in polynrs_of_holes:
        if nr == poly_nr:
            yield holes[i]
        i += 1


def extract_coords(polygon):
    x_coords, y_coords = list(zip(*polygon))
    x_coords = list(x_coords)
    y_coords = list(y_coords)
    # IMPORTANT: polygon are represented without point repetition at the end
    # -> do not use the last coordinate (only if equal to the first)!
    assert x_coords[0] == x_coords[-1]
    assert y_coords[0] == y_coords[-1]
    x_coords.pop(-1)
    y_coords.pop(-1)
    assert len(x_coords) == len(y_coords)
    assert len(x_coords) > 0
    return x_coords, y_coords


def parse_polygons_from_json(input_path):
    global nr_of_holes, nr_of_polygons, nr_of_zones, poly_zone_ids

    print(f"parsing input file: {input_path}\n...\n")
    with open(input_path) as json_file:
        tz_list = json.loads(json_file.read()).get("features")

    polygon_counter = 0  # this counter just counts polygons, not holes!
    current_zone_id = 0
    print("extracting data.\nfound holes:")
    for tz_dict in tz_list:
        if DEBUG and polygon_counter > DEBUG_POLY_STOP:
            break

        tz_name = tz_dict.get("properties").get("tzid")
        all_tz_names.append(tz_name)
        geometry = tz_dict.get("geometry")
        if geometry.get("type") == "MultiPolygon":
            # depth is 4
            multipolygon = geometry.get("coordinates")
        else:
            # depth is 3 (only one polygon, possibly with holes!)
            multipolygon = [geometry.get("coordinates")]
        # multipolygon has depth 4
        # assert depth_of_array(multipolygon) == 4
        for poly_with_hole in multipolygon:
            # the first entry is polygon
            x_coords, y_coords = extract_coords(poly_with_hole.pop(0))
            polygons.append((x_coords, y_coords))
            polygon_lengths.append(len(x_coords))
            poly_boundaries.append(
                (max(x_coords), min(x_coords), max(y_coords), min(y_coords))
            )
            poly_zone_ids.append(current_zone_id)

            # everything else is interpreted as a hole!
            for hole_nr, hole in enumerate(poly_with_hole):
                print(
                    f"#{nr_of_holes}: polygon #{polygon_counter}({hole_nr}) zone: {tz_name}"
                )
                nr_of_holes += 1  # keep track of how many holes there are
                polynrs_of_holes.append(polygon_counter)
                x_coords, y_coords = extract_coords(hole)
                holes.append((x_coords, y_coords))
                all_hole_lengths.append(len(x_coords))

            polygon_counter += 1

        current_zone_id += 1

    nr_of_polygons = len(polygon_lengths)
    assert polygon_counter == nr_of_polygons
    nr_of_zones = len(all_tz_names)
    assert current_zone_id == nr_of_zones
    assert nr_of_polygons >= nr_of_zones

    assert (
        polygon_counter == nr_of_polygons
    ), f"polygon counter {polygon_counter} and entry amount in all_length {nr_of_polygons} are different."

    if 0 in polygon_lengths:
        raise ValueError()

    # binary file value range tests:
    assert (
        nr_of_polygons < THRES_DTYPE_H
    ), f"address overflow: #{nr_of_polygons} polygon ids cannot be encoded as {DTYPE_FORMAT_H}!"
    assert (
        nr_of_zones < THRES_DTYPE_H
    ), f"address overflow: #{nr_of_zones} zone ids cannot be encoded as {DTYPE_FORMAT_H}!"
    max_poly_length = max(polygon_lengths)
    assert (
        max_poly_length < THRES_DTYPE_I
    ), f"address overflow: the maximal amount of coords {max_poly_length} cannot be represented by {DTYPE_FORMAT_I}"
    max_hole_poly_length = max(all_hole_lengths)
    assert max_hole_poly_length < THRES_DTYPE_H, (
        f"address overflow: the maximal amount of coords in hole polygons "
        f"{max_hole_poly_length} cannot be represented by {DTYPE_FORMAT_I}"
    )

    print("... parsing done. found:")
    print(f"{nr_of_polygons:,} polygons from")
    print(f"{nr_of_zones:,} timezones with")
    print(f"{nr_of_holes:,} holes")
    print(f"{max_poly_length:,} maximal amount of coordinates in one polygon")
    print(f"{max_hole_poly_length:,} maximal amount of coordinates in a hole polygon")
    print("\n")


def update_zone_names(output_path):
    global poly_zone_ids
    global list_of_pointers
    global poly_boundaries
    global polygons
    global polygon_lengths
    global polynrs_of_holes
    global nr_of_zones
    global nr_of_polygons
    file_path = abspath(join(output_path, TIMEZONE_NAMES_FILE))
    print(f"updating the zone names in {file_path} now.")
    # pickle the zone names (python array)
    with open(abspath(file_path), "w") as json_file:
        json.dump(all_tz_names, json_file, indent=4)
    print("...Done.\n\nComputing where zones start and end...")
    last_id = -1
    for poly_nr, zone_id in enumerate(poly_zone_ids):
        if zone_id != last_id:
            poly_nr2zone_id.append(poly_nr)
            assert zone_id >= last_id
            last_id = zone_id
    assert (
        zone_id == nr_of_zones - 1
    ), f"not pointing to the last zone with id {nr_of_zones - 1}"
    assert nr_of_polygons == len(poly_zone_ids)
    assert (
        poly_nr == nr_of_polygons - 1
    ), f"not pointing to the last polygon with id {nr_of_polygons - 1}"
    # ATTENTION: add one more entry for knowing where the last zone ends!
    # ATTENTION: the last entry is one higher than the last polygon id (to be consistant with the
    poly_nr2zone_id.append(nr_of_polygons)
    assert len(poly_nr2zone_id) == nr_of_zones + 1
    print("...Done.\n")


def write_value(output_file, value, data_format, lower_value_limit, upper_value_limit):
    assert (
        value > lower_value_limit
    ), f"trying to write value {value} subceeding lower limit {lower_value_limit} (data type {data_format})"
    assert (
        value < upper_value_limit
    ), f"trying to write value {value} exceeding upper limit {upper_value_limit} (data type {data_format})"
    output_file.write(pack(data_format, value))


def write_coordinate_value(output_file, coord):
    value = coord2int(coord)
    write_value(
        output_file,
        value,
        data_format=DTYPE_FORMAT_SIGNED_I,
        lower_value_limit=THRES_DTYPE_SIGNED_I_LOWER,
        upper_value_limit=THRES_DTYPE_SIGNED_I_UPPER,
    )


def write_regular(output_file, data, *args, **kwargs):
    for value in data:
        write_value(output_file, value, *args, **kwargs)


def write_coordinates(output_file, data, *args, **kwargs):
    for x_coords, y_coords in data:
        for x in x_coords:
            write_coordinate_value(output_file, x)

        for y in y_coords:
            write_coordinate_value(output_file, y)


def write_boundaries(output_file, data, *args, **kwargs):
    for boundaries in data:
        for boundary in boundaries:
            write_coordinate_value(output_file, boundary)


def write_binary(
    output_path,
    bin_file_name,
    data,
    data_format=DTYPE_FORMAT_H,
    lower_value_limit=-1,
    upper_value_limit=THRES_DTYPE_H,
    writing_fct=write_regular,
):
    path = abspath(join(output_path, bin_file_name + BINARY_FILE_ENDING))
    print(f"writing {path}")
    with open(path, "wb") as output_file:
        writing_fct(
            output_file, data, data_format, lower_value_limit, upper_value_limit
        )
        file_length = output_file.tell()
    return file_length


def write_coordinate_data(output_path, bin_file_name, data):
    return write_binary(output_path, bin_file_name, data, writing_fct=write_coordinates)


def write_boundary_data(output_path, bin_file_name, data):
    return write_binary(output_path, bin_file_name, data, writing_fct=write_boundaries)


def compile_binaries(output_path):
    global nr_of_polygons
    global shortcuts

    def print_shortcut_statistics():
        frequencies = []
        max_val = max(*nr_of_entries_in_shortcut)
        print("shortcut statistics:")
        print("highest entry amount is", max_val)
        while max_val >= 0:
            frequencies.append(nr_of_entries_in_shortcut.count(max_val))
            max_val -= 1

        frequencies.reverse()
        print("frequencies of entry amounts (from 0 to max entries):")
        print(frequencies)
        empty_shortcuts = frequencies[0]
        print("relative accumulated frequencies [%]:")
        acc = accumulated_frequency(frequencies)
        print(acc)
        print([round(100 - x, 2) for x in acc])
        print(
            percent(empty_shortcuts, amount_of_shortcuts),
            "% of all shortcuts are empty\n",
        )

        amount_of_different_zones = []
        for entry in shortcut_entries:
            registered_zone_ids = []
            for polygon_nr in entry:
                id = poly_zone_ids[polygon_nr]
                if id not in registered_zone_ids:
                    registered_zone_ids.append(id)

            amount_of_different_zones.append(len(registered_zone_ids))

        frequencies = []
        max_val = max(*amount_of_different_zones)
        print("highest amount of different zones in one shortcut is", max_val)
        while max_val >= 1:
            frequencies.append(amount_of_different_zones.count(max_val))
            max_val -= 1
        # show the proper amount of shortcuts with 0 zones (=nr of empty shortcuts)
        frequencies.append(empty_shortcuts)
        frequencies.reverse()
        print("frequencies of entry amounts (from 0 to max):")
        print(frequencies)
        print("relative accumulated frequencies [%]:")
        acc = accumulated_frequency(frequencies)
        print(acc)
        print([round(100 - x, 2) for x in acc])
        print("--------------------------------\n")

    def included_shortcut_row_nrs(max_lat, min_lat):
        return list(range(y_shortcut(max_lat), y_shortcut(min_lat) + 1))

    def included_shortcut_column_nrs(max_lng, min_lng):
        return list(range(x_shortcut(min_lng), x_shortcut(max_lng) + 1))

    def longitudes_to_check(max_lng, min_lng):
        output_list = []
        step = 1 / NR_SHORTCUTS_PER_LNG
        current = ceil(min_lng * NR_SHORTCUTS_PER_LNG) / NR_SHORTCUTS_PER_LNG
        end = floor(max_lng * NR_SHORTCUTS_PER_LNG) / NR_SHORTCUTS_PER_LNG
        while current < end:
            output_list.append(current)
            current += step

        output_list.append(end)
        return output_list

    def latitudes_to_check(max_lat, min_lat):
        output_list = []
        step = 1 / NR_SHORTCUTS_PER_LAT
        current = ceil(min_lat * NR_SHORTCUTS_PER_LAT) / NR_SHORTCUTS_PER_LAT
        end = floor(max_lat * NR_SHORTCUTS_PER_LAT) / NR_SHORTCUTS_PER_LAT
        while current < end:
            output_list.append(current)
            current += step

        output_list.append(end)
        return output_list

    def compute_x_intersection(y, x1, x2, y1, y2):
        """returns the x intersection from a horizontal line in y with the line from x1,y1 to x1,y2"""
        delta_y = y2 - y1
        if delta_y == 0:
            return x1
        return ((y - y1) * (x2 - x1) / delta_y) + x1

    def compute_y_intersection(x, x1, x2, y1, y2):
        """returns the y intersection from a vertical line in x with the line from x1,y1 to x1,y2"""
        delta_x = x2 - x1
        if delta_x == 0:
            return x1
        return ((x - x1) * (y2 - y1) / delta_x) + y1

    def x_intersections(y, x_coords, y_coords):
        intersects = []
        for i in range(len(y_coords) - 1):
            iplus1 = i + 1
            if y_coords[i] <= y:
                # print('Y1<=y')
                if y_coords[iplus1] > y:
                    # this was a crossing. compute the intersect
                    # print('Y2>y')
                    intersects.append(
                        compute_x_intersection(
                            y,
                            x_coords[i],
                            x_coords[iplus1],
                            y_coords[i],
                            y_coords[iplus1],
                        )
                    )
            else:
                # print('Y1>y')
                if y_coords[iplus1] <= y:
                    # this was a crossing. compute the intersect
                    # print('Y2<=y')
                    intersects.append(
                        compute_x_intersection(
                            y,
                            x_coords[i],
                            x_coords[iplus1],
                            y_coords[i],
                            y_coords[iplus1],
                        )
                    )
        return intersects

    def y_intersections(x, x_coords, y_coords):

        intersects = []
        for i in range(len(y_coords) - 1):
            iplus1 = i + 1
            if x_coords[i] <= x:
                if x_coords[iplus1] > x:
                    # this was a crossing. compute the intersect
                    intersects.append(
                        compute_y_intersection(
                            x,
                            x_coords[i],
                            x_coords[iplus1],
                            y_coords[i],
                            y_coords[iplus1],
                        )
                    )
            else:
                if x_coords[iplus1] <= x:
                    # this was a crossing. compute the intersect
                    intersects.append(
                        compute_y_intersection(
                            x,
                            x_coords[i],
                            x_coords[iplus1],
                            y_coords[i],
                            y_coords[iplus1],
                        )
                    )
        return intersects

    def compute_exact_shortcuts(xmax, xmin, ymax, ymin, line):
        shortcuts_for_line = set()

        # x_longs = binary_reader.x_coords_of(line)
        x_longs, y_longs = ints_of(line)

        # y_longs = binary_reader.y_coords_of(line)
        y_longs.append(y_longs[0])
        x_longs.append(x_longs[0])

        step = 1 / NR_SHORTCUTS_PER_LAT
        # print('checking the latitudes')
        for lat in latitudes_to_check(ymax, ymin):
            # print(lat)
            # print(coordinate_to_longlong(lat))
            # print(y_longs)
            # print(x_intersections(coordinate_to_longlong(lat), x_longs, y_longs))
            # raise ValueError
            intersects = sorted(
                int2coord(x) for x in x_intersections(coord2int(lat), x_longs, y_longs)
            )
            # print(intersects)

            nr_of_intersects = len(intersects)
            if nr_of_intersects % 2 != 0:
                raise ValueError("an uneven number of intersections has been accounted")

            for i in range(0, nr_of_intersects, 2):
                possible_longitudes = []
                # collect all the zones between two intersections [in,out,in,out,...]
                iplus = i + 1
                intersection_in = intersects[i]
                intersection_out = intersects[iplus]
                if intersection_in == intersection_out:
                    # the polygon has a point exactly on the border of a shortcut zone here!
                    # only select the top shortcut if it is actually inside the polygon (point a little up is inside)
                    if contained(
                        coord2int(intersection_in), coord2int(lat) + 1, x_longs, y_longs
                    ):
                        shortcuts_for_line.add(
                            (x_shortcut(intersection_in), y_shortcut(lat) - 1)
                        )
                    # the bottom shortcut is always selected
                    shortcuts_for_line.add(
                        (x_shortcut(intersection_in), y_shortcut(lat))
                    )

                else:
                    # add all the shortcuts for the whole found area of intersection
                    possible_y_shortcut = y_shortcut(lat)

                    # both shortcuts should only be selected when the polygon doesnt stays on the border
                    middle = intersection_in + (intersection_out - intersection_in) / 2
                    if contained(
                        coord2int(middle), coord2int(lat) + 1, x_longs, y_longs
                    ):
                        while intersection_in < intersection_out:
                            possible_longitudes.append(intersection_in)
                            intersection_in += step

                        possible_longitudes.append(intersection_out)

                        # the shortcut above and below of the intersection should be selected!
                        possible_y_shortcut_min1 = possible_y_shortcut - 1
                        for possible_x_coord in possible_longitudes:
                            shortcuts_for_line.add(
                                (x_shortcut(possible_x_coord), possible_y_shortcut)
                            )
                            shortcuts_for_line.add(
                                (x_shortcut(possible_x_coord), possible_y_shortcut_min1)
                            )
                    else:
                        # polygon does not cross the border!
                        while intersection_in < intersection_out:
                            possible_longitudes.append(intersection_in)
                            intersection_in += step

                        possible_longitudes.append(intersection_out)

                        # only the shortcut above of the intersection should be selected!
                        for possible_x_coord in possible_longitudes:
                            shortcuts_for_line.add(
                                (x_shortcut(possible_x_coord), possible_y_shortcut)
                            )

        # print('now all the longitudes to check')
        # same procedure horizontally
        step = 1 / NR_SHORTCUTS_PER_LAT
        for lng in longitudes_to_check(xmax, xmin):
            # print(lng)
            # print(coordinate_to_longlong(lng))
            # print(x_longs)
            # print(x_intersections(coordinate_to_longlong(lng), x_longs, y_longs))
            intersects = sorted(
                int2coord(y) for y in y_intersections(coord2int(lng), x_longs, y_longs)
            )
            # print(intersects)

            nr_of_intersects = len(intersects)
            if nr_of_intersects % 2 != 0:
                raise ValueError("an uneven number of intersections has been accounted")

            possible_latitudes = []
            for i in range(0, nr_of_intersects, 2):
                # collect all the zones between two intersections [in,out,in,out,...]
                iplus = i + 1
                intersection_in = intersects[i]
                intersection_out = intersects[iplus]
                if intersection_in == intersection_out:
                    # the polygon has a point exactly on the border of a shortcut here!
                    # only select the left shortcut if it is actually inside the polygon (point a little left is inside)
                    if contained(
                        coord2int(lng) - 1, coord2int(intersection_in), x_longs, y_longs
                    ):
                        shortcuts_for_line.add(
                            (x_shortcut(lng) - 1, y_shortcut(intersection_in))
                        )
                    # the right shortcut is always selected
                    shortcuts_for_line.add(
                        (x_shortcut(lng), y_shortcut(intersection_in))
                    )

                else:
                    # add all the shortcuts for the whole found area of intersection
                    possible_x_shortcut = x_shortcut(lng)

                    # both shortcuts should only be selected when the polygon doesnt stays on the border
                    middle = intersection_in + (intersection_out - intersection_in) / 2
                    if contained(
                        coord2int(lng) - 1, coord2int(middle), x_longs, y_longs
                    ):
                        while intersection_in < intersection_out:
                            possible_latitudes.append(intersection_in)
                            intersection_in += step

                        possible_latitudes.append(intersection_out)

                        # both shortcuts right and left of the intersection should be selected!
                        possible_x_shortcut_min1 = possible_x_shortcut - 1
                        for possible_latitude in possible_latitudes:
                            shortcuts_for_line.add(
                                (possible_x_shortcut, y_shortcut(possible_latitude))
                            )
                            shortcuts_for_line.add(
                                (
                                    possible_x_shortcut_min1,
                                    y_shortcut(possible_latitude),
                                )
                            )

                    else:
                        while intersection_in < intersection_out:
                            possible_latitudes.append(intersection_in)
                            intersection_in += step
                        # only the shortcut right of the intersection should be selected!
                        possible_latitudes.append(intersection_out)

                        for possible_latitude in possible_latitudes:
                            shortcuts_for_line.add(
                                (possible_x_shortcut, y_shortcut(possible_latitude))
                            )

        return shortcuts_for_line

    def construct_shortcuts():
        print("building shortucts...")
        print("currently at polygon nr:")
        line = 0
        for xmax, xmin, ymax, ymin in poly_boundaries:
            # xmax, xmin, ymax, ymin = boundaries_of(line=line)
            if line % 100 == 0:
                print(line)
                # print([xmax, xmin, ymax, ymin])

            column_nrs = included_shortcut_column_nrs(xmax, xmin)
            row_nrs = included_shortcut_row_nrs(ymax, ymin)

            if big_zone(xmax, xmin, ymax, ymin):

                # print('line ' + str(line))
                # print('This is a big zone! computing exact shortcuts')
                # print('Nr of entries before')
                # print(len(column_nrs) * len(row_nrs))
                # print('columns and rows before optimisation:')
                # print(column_nrs)
                # print(row_nrs)
                # print(ints_of(line))

                # This is a big zone! compute exact shortcuts with the whole polygon points
                shortcuts_for_line = compute_exact_shortcuts(
                    xmax, xmin, ymax, ymin, line
                )
                # n += len(shortcuts_for_line)

                min_x_shortcut = column_nrs[0]
                max_x_shortcut = column_nrs[-1]
                min_y_shortcut = row_nrs[0]
                max_y_shortcut = row_nrs[-1]
                shortcuts_to_remove = []

                # remove shortcuts from outside the possible/valid area
                for x, y in shortcuts_for_line:
                    if (
                        x < min_x_shortcut
                        or x > max_x_shortcut
                        or y < min_y_shortcut
                        or y > max_y_shortcut
                    ):
                        shortcuts_to_remove.append((x, y))

                for s in shortcuts_to_remove:
                    shortcuts_for_line.remove(s)

                # print('and after:')
                # print(len(shortcuts_for_line))
                # print(shortcuts_for_line)
                # column_nrs_after = set()
                # row_nrs_after = set()
                # for x, y in shortcuts_for_line:
                #     column_nrs_after.add(x)
                #     row_nrs_after.add(y)
                # print(column_nrs_after)
                # print(row_nrs_after)
                # print(shortcuts_for_line)

                if len(shortcuts_for_line) > len(column_nrs) * len(row_nrs):
                    raise ValueError(
                        "there are more shortcuts than before now. there is something wrong with the algorithm!"
                    )
                if len(shortcuts_for_line) < 3:
                    raise ValueError(
                        "algorithm not valid! less than 3 zones detected (should be at least 3)"
                    )

            else:
                shortcuts_for_line = []
                for column_nr in column_nrs:
                    for row_nr in row_nrs:
                        shortcuts_for_line.append((column_nr, row_nr))
                        # print(shortcuts_for_line)

            for shortcut in shortcuts_for_line:
                shortcuts[shortcut] = shortcuts.get(shortcut, []) + [line]

            line += 1
            # print('collected entries:')
            # print(n)

    start_time = datetime.now()
    construct_shortcuts()
    end_time = datetime.now()
    print("calculating the shortcuts took:", end_time - start_time, "\n")

    # there are two floats per coordinate (lng, lat)
    nr_of_floats = 2 * sum(polygon_lengths)

    # write number of entries in shortcut field (x,y)
    nr_of_entries_in_shortcut = []
    shortcut_entries = []
    amount_filled_shortcuts = 0

    def sort_poly_shortcut(poly_nrs):
        # TODO write test
        # the list of polygon ids in each shortcut is sorted after freq. of appearance of their zone id
        # polygons of the least frequent zone should come first!
        # this is critical for ruling out zones faster
        # (as soon as just polygons of one zone are left this zone can be returned)
        # only around 5% of all shortcuts include polygons from more than one zone
        # in most of those cases there are only two types of zones (= entries in counted_zones) and one of them
        # has only one entry (important to check the zone with one entry first!).
        zone_ids = [poly_zone_ids[poly_nr] for poly_nr in poly_nrs]
        zone_id_freq = [zone_ids.count(id) for id in zone_ids]
        zipped = list(zip(poly_nrs, zone_ids, zone_id_freq))
        # also make sure polygons with the same zone freq. are ordered after their zone id
        # (polygons from different zones should not get mixed up)
        zipped_sorted = sorted(zipped, key=lambda x: (x[1], x[2]))
        # [x[0] for x in zipped_sorted]  # take only the polygon nrs
        return zip(*zipped_sorted)

    direct_ids = []
    unique_ids = []
    # count how many shortcut addresses will be written
    # flatten out the shortcuts in one list in the order they are going to be written inside the polygon file
    for x in range(360 * NR_SHORTCUTS_PER_LNG):
        for y in range(180 * NR_SHORTCUTS_PER_LAT):
            try:
                shortcuts_this_entry = shortcuts[(x, y)]
                shortcuts_sorted, zone_ids, zone_id_freqs = sort_poly_shortcut(
                    shortcuts_this_entry
                )
                # polygons of the least common zone must come first
                # -> this zone can be ruled out faster
                assert zone_id_freqs[-1] >= zone_id_freqs[0]
                shortcut_entries.append(shortcuts_sorted)
                amount_filled_shortcuts += 1
                nr_of_entries_in_shortcut.append(len(shortcuts_this_entry))
                direct_id = zone_ids[-1]  # most common zone id
                if direct_id == zone_ids[0]:  # equal to least common zone id
                    unique_id = direct_id
                else:
                    # there is a polygon from a different zone (hence an invalid id should be written)
                    unique_id = INVALID_VALUE_DTYPE_H

            except KeyError:
                nr_of_entries_in_shortcut.append(0)
                # also write an invalid id when there is no polygon at all
                direct_id = INVALID_VALUE_DTYPE_H
                unique_id = INVALID_VALUE_DTYPE_H

            direct_ids.append(direct_id)
            unique_ids.append(unique_id)

    amount_of_shortcuts = len(nr_of_entries_in_shortcut)
    print_shortcut_statistics()

    if amount_of_shortcuts != 360 * 180 * NR_SHORTCUTS_PER_LNG * NR_SHORTCUTS_PER_LAT:
        raise ValueError("this number of shortcut zones is wrong:", amount_of_shortcuts)

    print(
        "The number of filled shortcut zones are: ",
        amount_filled_shortcuts,
        "(=",
        round((amount_filled_shortcuts / amount_of_shortcuts) * 100, 2),
        "% of all shortcuts)",
    )

    # for every shortcut <H and <I is written (nr of entries and address)
    shortcut_space = (
        360
        * NR_SHORTCUTS_PER_LNG
        * 180
        * NR_SHORTCUTS_PER_LAT
        * (NR_BYTES_H + NR_BYTES_I)
    )
    for nr in nr_of_entries_in_shortcut:
        # every line in every shortcut takes up 2bytes
        shortcut_space += NR_BYTES_H * nr

    print("number of polygons:", nr_of_polygons)
    print(f"number of floats in all the polygons: {nr_of_floats:,} (2 per point)")

    def compile_addresses(length_list, multiplier=1, byte_amount_per_entry=1):
        adr = 0
        addresses = [adr]
        for length in length_list:
            adr += multiplier * byte_amount_per_entry * length
            addresses.append(adr)
        return addresses

    # NOTE: last entry is nr_of_polygons -> allow +1
    write_binary(
        output_path,
        POLY_NR2ZONE_ID,
        poly_nr2zone_id,
        upper_value_limit=nr_of_polygons + 1,
    )
    write_binary(
        output_path, POLY_ZONE_IDS, poly_zone_ids, upper_value_limit=nr_of_zones
    )
    write_boundary_data(output_path, POLY_MAX_VALUES, poly_boundaries)
    write_coordinate_data(output_path, POLY_DATA, polygons)
    write_binary(
        output_path,
        POLY_COORD_AMOUNT,
        polygon_lengths,
        data_format=DTYPE_FORMAT_I,
        upper_value_limit=THRES_DTYPE_I,
    )

    # 2 entries per coordinate
    poly_addresses = compile_addresses(
        polygon_lengths, multiplier=2, byte_amount_per_entry=NR_BYTES_I
    )
    write_binary(
        output_path,
        POLY_ADR2DATA,
        poly_addresses,
        data_format=DTYPE_FORMAT_I,
        upper_value_limit=THRES_DTYPE_I,
    )

    # [SHORTCUT AREA]
    write_binary(
        output_path,
        SHORTCUTS_ENTRY_AMOUNT,
        nr_of_entries_in_shortcut,
        upper_value_limit=nr_of_polygons,
    )

    # write address of first "shortcut" (=polygon number) in shortcut field (x,y)
    adr = 0
    path = join(output_path, SHORTCUTS_ADR2DATA + BINARY_FILE_ENDING)
    print(f"writing {path}")
    with open(path, "wb") as output_file:
        for nr in nr_of_entries_in_shortcut:
            if nr == 0:
                # ATTENTION: write 0 when there are no entries in this shortcut
                output_file.write(pack(DTYPE_FORMAT_I, 0))
            else:
                output_file.write(pack(DTYPE_FORMAT_I, adr))
                # each line_nr takes up x bytes of space
                adr += NR_BYTES_H * nr

    def flatten(list):  # only one level!
        return [item for sublist in list for item in sublist]

    shortcut_data = flatten(shortcut_entries)
    write_binary(
        output_path, SHORTCUTS_DATA, shortcut_data, upper_value_limit=nr_of_polygons
    )
    write_binary(output_path, SHORTCUTS_UNIQUE_ID, unique_ids)
    write_binary(output_path, SHORTCUTS_DIRECT_ID, direct_ids)

    # [HOLE AREA, Y = number of holes (very few: around 22)]
    hole_space = 0

    # store for which polygons (how many) holes exits and the id of the first of those holes
    # since there are very few it is feasible to keep them in memory
    # -> export and import as json
    hole_registry = {}
    # read the polygon ids for all the holes
    for i, poly_id in enumerate(polynrs_of_holes):
        try:
            amount_of_holes, hole_id = hole_registry[poly_id]
            hole_registry.update(
                {
                    poly_id: (amount_of_holes + 1, hole_id),
                }
            )
        except KeyError:
            hole_registry.update(
                {
                    poly_id: (1, i),
                }
            )

    with open(join(output_path, HOLE_REGISTRY_FILE), "w") as json_file:
        json.dump(hole_registry, json_file, indent=4)

    # '<H'  Y times [H unsigned short: nr of values (coordinate PAIRS! x,y in int32 int32) in this hole]
    assert len(all_hole_lengths) == nr_of_holes
    used_space = write_binary(output_path, HOLE_COORD_AMOUNT, all_hole_lengths)
    hole_space += used_space

    # '<I' Y times [ I unsigned int: absolute address of the byte where the data of that hole starts]
    write_binary(
        output_path,
        POLY_ADR2DATA,
        poly_addresses,
        data_format=DTYPE_FORMAT_I,
        upper_value_limit=THRES_DTYPE_I,
    )

    # 2 entries per coordinate
    hole_adr2data = compile_addresses(
        all_hole_lengths, multiplier=2, byte_amount_per_entry=NR_BYTES_I
    )
    used_space = write_binary(
        output_path,
        HOLE_ADR2DATA,
        hole_adr2data,
        data_format=DTYPE_FORMAT_I,
        upper_value_limit=THRES_DTYPE_I,
    )
    hole_space += used_space

    # Y times [ 2x i signed ints for every hole: x coords, y coords ]
    used_space = write_coordinate_data(output_path, HOLE_DATA, holes)
    hole_space += used_space

    polygon_space = nr_of_floats * NR_BYTES_I
    total_space = polygon_space + hole_space + shortcut_space

    print(
        "the polygon data makes up",
        percent(polygon_space, total_space),
        "% of the data",
    )
    print(
        "the shortcuts make up", percent(shortcut_space, total_space), "% of the data"
    )
    print("holes make up", percent(hole_space, total_space), "% of the data")
    print("Success!")


def parse_data(input_path=DEFAULT_INPUT_PATH, output_path=DEFAULT_OUTPUT_PATH):
    # parsing the data from the .json into RAM
    parse_polygons_from_json(input_path)
    # update all the zone names and set the right ids to be written in the poly_zone_ids.bin
    # sort data according to zone_id
    update_zone_names(output_path)

    # TODO
    # IMPORTANT: import the newly compiled timezone_names pickle!
    # the compilation process needs the new version of the timezone names
    # with open(path2timezone_names, 'r') as f:
    #     timezone_names = json.loads(f.read())

    # compute shortcuts and write everything into the binaries
    compile_binaries(output_path)


if __name__ == "__main__":
    import argparse

    # TODO document
    parser = argparse.ArgumentParser(description="parse data directories")
    parser.add_argument(
        "-inp", help="path to input JSON file", default=DEFAULT_INPUT_PATH
    )
    parser.add_argument(
        "-out",
        help="path to output folder for storing the parsed data files",
        default=DEFAULT_OUTPUT_PATH,
    )
    parsed_args = parser.parse_args()  # takes input from sys.argv
    parse_data(input_path=parsed_args.inp, output_path=parsed_args.out)
