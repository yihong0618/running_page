# -*- coding:utf-8 -*-
import json
import re
from abc import ABC, abstractmethod
from io import SEEK_CUR, BytesIO
from math import radians
from os.path import abspath, join, pardir
from struct import unpack
from typing import List, Optional

from numpy import array, dtype, empty, frombuffer, fromfile

from timezonefinder.global_settings import (
    BINARY_DATA_ATTRIBUTES,
    BINARY_FILE_ENDING,
    DATA_ATTRIBUTE_NAMES,
    DTYPE_FORMAT_B_NUMPY,
    DTYPE_FORMAT_F_NUMPY,
    DTYPE_FORMAT_H,
    DTYPE_FORMAT_H_NUMPY,
    DTYPE_FORMAT_I,
    DTYPE_FORMAT_SIGNED_I_NUMPY,
    HOLE_ADR2DATA,
    HOLE_COORD_AMOUNT,
    HOLE_DATA,
    HOLE_REGISTRY,
    HOLE_REGISTRY_FILE,
    MAX_HAVERSINE_DISTANCE,
    NR_BYTES_H,
    NR_BYTES_I,
    NR_LAT_SHORTCUTS,
    NR_SHORTCUTS_PER_LAT,
    NR_SHORTCUTS_PER_LNG,
    OCEAN_TIMEZONE_PREFIX,
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
    TIMEZONE_NAMES,
    TIMEZONE_NAMES_FILE,
)

try:
    import numba

    from timezonefinder.helpers_numba import (
        all_the_same,
        convert2coord_pairs,
        convert2coords,
        coord2int,
        coord2shortcut,
        distance_to_polygon,
        distance_to_polygon_exact,
        inside_polygon,
        rectify_coordinates,
    )
except ImportError:
    numba = None
    from timezonefinder.helpers import (
        all_the_same,
        convert2coord_pairs,
        convert2coords,
        coord2int,
        coord2shortcut,
        distance_to_polygon,
        distance_to_polygon_exact,
        inside_polygon,
        rectify_coordinates,
    )


def fromfile_memory(file, **kwargs):
    # res = frombuffer(file.getbuffer(), offset=file.tell(), **kwargs)
    # faster:
    res = frombuffer(file.getbuffer(), offset=file.tell(), **kwargs)
    file.seek(dtype(kwargs["dtype"]).itemsize * kwargs["count"], SEEK_CUR)
    return res


def is_ocean_timezone(timezone_name: str) -> bool:
    if re.match(OCEAN_TIMEZONE_PREFIX, timezone_name) is None:
        return False
    return True


class AbstractTimezoneFinder(ABC):
    # TODO document attributes in all classes
    # prevent dynamic attribute assignment (-> safe memory)
    __slots__ = ["bin_file_location", "in_memory", "_fromfile", TIMEZONE_NAMES]

    binary_data_attributes: List[str] = []

    def __init__(
        self, bin_file_location: Optional[str] = None, in_memory: bool = False
    ):
        self.in_memory = in_memory

        if self.in_memory:
            self._fromfile = fromfile_memory
        else:
            self._fromfile = fromfile

        # open all the files in binary reading mode
        # for more info on what is stored in which .bin file, please read the comments in file_converter.py
        if bin_file_location is None:
            self.bin_file_location = abspath(join(__file__, pardir))
        else:
            self.bin_file_location = bin_file_location

        for attribute_name in self.binary_data_attributes:
            bin_file = open(
                join(self.bin_file_location, attribute_name + BINARY_FILE_ENDING),
                mode="rb",
            )
            if self.in_memory:
                bf_in_mem = BytesIO(bin_file.read())
                bf_in_mem.seek(0)
                bin_file.close()
                bin_file = bf_in_mem
            setattr(self, attribute_name, bin_file)

        with open(join(self.bin_file_location, TIMEZONE_NAMES_FILE), "r") as json_file:
            setattr(self, TIMEZONE_NAMES, json.loads(json_file.read()))

    def __del__(self):
        for attribute_name in self.binary_data_attributes:
            getattr(self, attribute_name).close()

    @property
    def nr_of_zones(self):
        return len(getattr(self, TIMEZONE_NAMES))

    @staticmethod
    def using_numba():
        """tests if Numba is being used or not

        :return: True if the import of the JIT compiled algorithms worked. False otherwise
        """
        return numba is not None

    @abstractmethod
    def timezone_at(self, *, lng: float, lat: float) -> Optional[str]:
        """looks up in which timezone the given coordinate is included in

        :param lng: longitude of the point in degree (-180.0 to 180.0)
        :param lat: latitude in degree (90.0 to -90.0)
        :return: the timezone name of a matching polygon or None
        """
        pass

    def timezone_at_land(self, *, lng: float, lat: float) -> Optional[str]:
        """computes in which land timezone a point is included in

        Especially for large polygons it is expensive to check if a point is really included.
        To speed things up there are "shortcuts" being used (stored in a binary file),
        which have been precomputed and store which timezone polygons have to be checked.

        :param lng: longitude of the point in degree (-180.0 to 180.0)
        :param lat: latitude in degree (90.0 to -90.0)
        :return: the timezone name of a matching polygon or
            ``None`` when an ocean timezone ("Etc/GMT+-XX") has been matched.
        """
        tz_name = self.timezone_at(lng=lng, lat=lat)
        if is_ocean_timezone(tz_name):
            return None
        return tz_name

    def _get_unique_zone(self, shortcut_id_x, shortcut_id_y):
        shortcut_unique_id = getattr(self, SHORTCUTS_UNIQUE_ID)
        shortcut_unique_id.seek(
            NR_LAT_SHORTCUTS * NR_BYTES_H * shortcut_id_x + NR_BYTES_H * shortcut_id_y
        )
        try:
            # if there is just one possible zone in this shortcut instantly return its name
            return getattr(self, TIMEZONE_NAMES)[
                unpack(
                    DTYPE_FORMAT_H, getattr(self, SHORTCUTS_UNIQUE_ID).read(NR_BYTES_H)
                )[0]
            ]
        except IndexError:  # no zone matched
            return None

    def unique_timezone_at(self, *, lng: float, lat: float) -> Optional[str]:
        """instantly returns the name of a unique zone within the corresponding shortcut

        :param lng: longitude of the point in degree (-180.0 to 180.0)
        :param lat: latitude in degree (90.0 to -90.0)
        :return: the timezone name of the unique zone or None if there are no or multiple zones in this shortcut
        """
        lng, lat = rectify_coordinates(lng, lat)
        shortcut_id_x, shortcut_id_y = coord2shortcut(lng, lat)
        return self._get_unique_zone(shortcut_id_x, shortcut_id_y)


class TimezoneFinderL(AbstractTimezoneFinder):
    """a 'light' version of the TimezoneFinder class for quickly suggesting a timezone for a point on earth

    Instead of using timezone polygon data like ``TimezoneFinder``,
    this class only uses a precomputed 'shortcut' to suggest a probable result:
    the most common zone in a rectangle of a half degree of latitude and one degree of longitude
    """

    # __slots__ declared in parents are available in child classes. However, child subclasses will get a __dict__
    # and __weakref__ unless they also define __slots__ (which should only contain names of any additional slots).
    __slots__ = [SHORTCUTS_DIRECT_ID, SHORTCUTS_UNIQUE_ID]
    binary_data_attributes = [SHORTCUTS_DIRECT_ID, SHORTCUTS_UNIQUE_ID]

    def timezone_at(self, *, lng: float, lat: float) -> str:
        """instantly returns the name of the most common zone within the corresponding shortcut

        :param lng: longitude of the point in degree (-180.0 to 180.0)
        :param lat: latitude in degree (90.0 to -90.0)
        :return: the timezone name of the most common zone or None if there are no timezone polygons in this shortcut
        """
        lng, lat = rectify_coordinates(lng, lat)
        shortcut_id_x, shortcut_id_y = coord2shortcut(lng, lat)
        shortcut_direct_id = getattr(self, SHORTCUTS_DIRECT_ID)
        shortcut_direct_id.seek(
            NR_LAT_SHORTCUTS * NR_BYTES_H * shortcut_id_x + NR_BYTES_H * shortcut_id_y
        )
        try:
            return getattr(self, TIMEZONE_NAMES)[
                unpack(DTYPE_FORMAT_H, shortcut_direct_id.read(NR_BYTES_H))[0]
            ]
        except IndexError:
            raise ValueError("timezone could not be found. index error.")


class TimezoneFinder(AbstractTimezoneFinder):
    """Class for quickly finding the timezone of a point on earth offline.

    Opens the required timezone polygon data in binary files to enable fast access.
    Currently per half degree of latitude and per degree of longitude the set of all candidate polygons are stored.
    Because of these so called 'shortcuts' not all timezone polygons have to be tested during a query.
    For a detailed documentation of data management please refer to the code documentation of
    `file_converter.py <https://github.com/MrMinimal64/timezonefinder/blob/master/timezonefinder/file_converter.py>`__

    :ivar binary_data_attributes: the names of all attributes which store the opened binary data files

    :param bin_file_location: path to the binary data files to use, None if native package data should be used
    :param in_memory: whether to completely read and keep the binary files in memory
    """

    # __slots__ declared in parents are available in child classes. However, child subclasses will get a __dict__
    # and __weakref__ unless they also define __slots__ (which should only contain names of any additional slots).
    __slots__ = DATA_ATTRIBUTE_NAMES

    binary_data_attributes = BINARY_DATA_ATTRIBUTES

    def __init__(
        self, bin_file_location: Optional[str] = None, in_memory: bool = False
    ):
        super(TimezoneFinder, self).__init__(bin_file_location, in_memory)

        # stores for which polygons (how many) holes exits and the id of the first of those holes
        # since there are very few (~22) it is feasible to keep them in the memory
        with open(join(self.bin_file_location, HOLE_REGISTRY_FILE), "r") as json_file:
            hole_registry_tmp = json.loads(json_file.read())
            # convert the json string keys to int
            setattr(
                self, HOLE_REGISTRY, {int(k): v for k, v in hole_registry_tmp.items()}
            )

    def id_of(self, polygon_nr: int = 0):
        poly_zone_ids = getattr(self, POLY_ZONE_IDS)
        poly_zone_ids.seek(NR_BYTES_H * polygon_nr)
        return unpack(DTYPE_FORMAT_H, poly_zone_ids.read(NR_BYTES_H))[0]

    def ids_of(self, iterable):
        poly_zone_ids = getattr(self, POLY_ZONE_IDS)
        id_array = empty(shape=len(iterable), dtype=DTYPE_FORMAT_B_NUMPY)

        for i, line_nr in enumerate(iterable):
            poly_zone_ids.seek(NR_BYTES_H * line_nr)
            id_array[i] = unpack(DTYPE_FORMAT_H, poly_zone_ids.read(NR_BYTES_H))[0]

        return id_array

    def polygon_ids_of_shortcut(self, x: int = 0, y: int = 0):
        # get the address of the first entry in this shortcut
        # offset: 180 * number of shortcuts per lat degree * 2bytes = entries per column of x shortcuts
        # shortcuts are stored: (0,0) (0,1) (0,2)... (1,0)...
        shortcuts_entry_amount = getattr(self, SHORTCUTS_ENTRY_AMOUNT)
        shortcuts_adr2data = getattr(self, SHORTCUTS_ADR2DATA)
        shortcuts_data = getattr(self, SHORTCUTS_DATA)

        shortcuts_entry_amount.seek(NR_LAT_SHORTCUTS * NR_BYTES_H * x + NR_BYTES_H * y)
        nr_of_entries = unpack(DTYPE_FORMAT_H, shortcuts_entry_amount.read(NR_BYTES_H))[
            0
        ]

        shortcuts_adr2data.seek(NR_LAT_SHORTCUTS * NR_BYTES_I * x + NR_BYTES_I * y)
        shortcuts_data.seek(
            unpack(DTYPE_FORMAT_I, shortcuts_adr2data.read(NR_BYTES_I))[0]
        )
        return self._fromfile(
            shortcuts_data, dtype=DTYPE_FORMAT_H_NUMPY, count=nr_of_entries
        )

    def coords_of(self, polygon_nr: int = 0):
        poly_coord_amount = getattr(self, POLY_COORD_AMOUNT)
        poly_adr2data = getattr(self, POLY_ADR2DATA)
        poly_data = getattr(self, POLY_DATA)

        # how many coordinates are stored in this polygon
        poly_coord_amount.seek(NR_BYTES_I * polygon_nr)
        nr_of_values = unpack(DTYPE_FORMAT_I, poly_coord_amount.read(NR_BYTES_I))[0]

        poly_adr2data.seek(NR_BYTES_I * polygon_nr)
        poly_data.seek(unpack(DTYPE_FORMAT_I, poly_adr2data.read(NR_BYTES_I))[0])
        return array(
            [
                self._fromfile(
                    poly_data, dtype=DTYPE_FORMAT_SIGNED_I_NUMPY, count=nr_of_values
                ),
                self._fromfile(
                    poly_data, dtype=DTYPE_FORMAT_SIGNED_I_NUMPY, count=nr_of_values
                ),
            ]
        )

    def _holes_of_poly(self, polygon_nr: int = 0):
        hole_coord_amount = getattr(self, HOLE_COORD_AMOUNT)
        hole_adr2data = getattr(self, HOLE_ADR2DATA)
        hole_data = getattr(self, HOLE_DATA)

        try:
            amount_of_holes, hole_id = getattr(self, HOLE_REGISTRY)[
                polygon_nr
            ]  # json keys are strings
            for _ in range(amount_of_holes):
                hole_coord_amount.seek(NR_BYTES_H * hole_id)
                nr_of_values = unpack(
                    DTYPE_FORMAT_H, hole_coord_amount.read(NR_BYTES_H)
                )[0]

                hole_adr2data.seek(NR_BYTES_I * hole_id)
                hole_data.seek(
                    unpack(DTYPE_FORMAT_I, hole_adr2data.read(NR_BYTES_I))[0]
                )

                yield array(
                    [
                        self._fromfile(
                            hole_data,
                            dtype=DTYPE_FORMAT_SIGNED_I_NUMPY,
                            count=nr_of_values,
                        ),
                        self._fromfile(
                            hole_data,
                            dtype=DTYPE_FORMAT_SIGNED_I_NUMPY,
                            count=nr_of_values,
                        ),
                    ]
                )
                hole_id += 1

        except KeyError:
            return

    def get_polygon(self, polygon_nr: int, coords_as_pairs: bool = False):
        list_of_converted_polygons = []
        if coords_as_pairs:
            conversion_method = convert2coord_pairs
        else:
            conversion_method = convert2coords
        list_of_converted_polygons.append(
            conversion_method(self.coords_of(polygon_nr=polygon_nr))
        )

        for hole in self._holes_of_poly(polygon_nr):
            list_of_converted_polygons.append(conversion_method(hole))

        return list_of_converted_polygons

    def get_geometry(
        self,
        tz_name: Optional[str] = "",
        tz_id: Optional[int] = 0,
        use_id: bool = False,
        coords_as_pairs: bool = False,
    ):
        """retrieves the geometry of a timezone polygon

        :param tz_name: one of the names in ``timezone_names.json`` or ``getattr(self, TIMEZONE_NAMES)``
        :param tz_id: the id of the timezone (=index in ``getattr(self, TIMEZONE_NAMES)``)
        :param use_id: if ``True`` uses ``tz_id`` instead of ``tz_name``
        :param coords_as_pairs: determines the structure of the polygon representation
        :return: a data structure representing the multipolygon of this timezone
            output format: ``[ [polygon1, hole1, hole2...], [polygon2, ...], ...]``
            and each polygon and hole is itself formatted like: ``([longitudes], [latitudes])``
            or ``[(lng1,lat1), (lng2,lat2),...]`` if ``coords_as_pairs=True``.
        """

        if use_id:
            if not isinstance(tz_id, int):
                raise TypeError("the zone id must be given as int.")
            if tz_id < 0 or tz_id >= self.nr_of_zones:
                raise ValueError(
                    f"the given zone id {tz_id} is invalid (value range: 0 - {self.nr_of_zones - 1}."
                )
        else:
            try:
                tz_id = getattr(self, TIMEZONE_NAMES).index(tz_name)
            except ValueError:
                raise ValueError("The timezone '", tz_name, "' does not exist.")
        poly_nr2zone_id = getattr(self, POLY_NR2ZONE_ID)
        poly_nr2zone_id.seek(NR_BYTES_H * tz_id)
        # read poly_nr of the first polygon of that zone
        this_zone_poly_id = unpack(DTYPE_FORMAT_H, poly_nr2zone_id.read(NR_BYTES_H))[0]
        # read poly_nr of the first polygon of the consequent zone
        # (also exists for the last zone, cf. file_converter.py)
        next_zone_poly_id = unpack(DTYPE_FORMAT_H, poly_nr2zone_id.read(NR_BYTES_H))[0]
        # read and return all polygons from this zone:
        return [
            self.get_polygon(poly_nr, coords_as_pairs)
            for poly_nr in range(this_zone_poly_id, next_zone_poly_id)
        ]

    def id_list(self, polygon_id_list, nr_of_polygons):
        """
        :param polygon_id_list:
        :param nr_of_polygons: length of polygon_id_list
        :return: (list of zone_ids, boolean: do all entries belong to the same zone)
        """
        zone_id_list = empty([nr_of_polygons], dtype=DTYPE_FORMAT_H_NUMPY)
        for pointer_local, polygon_id in enumerate(polygon_id_list):
            zone_id = self.id_of(polygon_id)
            zone_id_list[pointer_local] = zone_id

        return zone_id_list

    def compile_id_list(self, polygon_id_list, nr_of_polygons):
        """sorts the polygons_id list from least to most occurrences of the zone ids (->speed up)

        only 4.8% of all shortcuts include polygons from more than one zone
        but only for about 0.4% sorting would be beneficial (zones have different frequencies)
        in most of those cases there are only two types of zones (= entries in counted_zones) and one of them
        has only one entry.
        the polygon lists of all single shortcut are already sorted (during compilation of the binary files)
        sorting should be used for closest_timezone_at(), because only in
        that use case the polygon lists are quite long (multiple shortcuts are being checked simultaneously).

        :param polygon_id_list: input list of polygon
        :param nr_of_polygons: length of polygon_id_list
        :return: sorted list of polygon_ids, sorted list of zone_ids, boolean: do all entries belong to the same zone
        """

        zone_id_list = empty([nr_of_polygons], dtype=DTYPE_FORMAT_H_NUMPY)
        counted_zones = {}
        for pointer_local, polygon_id in enumerate(polygon_id_list):
            zone_id = self.id_of(polygon_id)
            zone_id_list[pointer_local] = zone_id
            try:
                counted_zones[zone_id] += 1
            except KeyError:
                counted_zones[zone_id] = 1

        if len(counted_zones) == 1:
            # there is only one zone. no sorting needed.
            return polygon_id_list, zone_id_list, True

        if len(set(counted_zones.values())) == 1:
            # all the zones have the same amount of polygons. no sorting needed.
            return polygon_id_list, zone_id_list, False

        counted_zones_sorted = sorted(counted_zones.items(), key=lambda zone: zone[1])
        sorted_polygon_id_list = empty(nr_of_polygons, dtype=DTYPE_FORMAT_H_NUMPY)
        sorted_zone_id_list = empty(nr_of_polygons, dtype=DTYPE_FORMAT_H_NUMPY)

        pointer_output = 0
        for zone_id, amount in counted_zones_sorted:
            # write all polygons from this zone in the new list
            pointer_local = 0
            detected_polygons = 0
            while detected_polygons < amount:
                if zone_id_list[pointer_local] == zone_id:
                    # the polygon at the pointer has the wanted zone_id
                    detected_polygons += 1
                    sorted_polygon_id_list[pointer_output] = polygon_id_list[
                        pointer_local
                    ]
                    sorted_zone_id_list[pointer_output] = zone_id
                    pointer_output += 1

                pointer_local += 1

        return sorted_polygon_id_list, sorted_zone_id_list, False

    # TODO split up in different functions
    # TODO any point is included in some zone,
    #  -> shared boundaries, ambiguous results, not meaningful to search for the closest boundary!
    def closest_timezone_at(
        self,
        *,
        lng: float,
        lat: float,
        delta_degree: int = 1,
        exact_computation: bool = False,
        return_distances: bool = False,
        force_evaluation: bool = False,
    ):
        """Computes the (approximate) minimal distance to the polygon boundaries in the surrounding shortcuts.

        .. note::  Since ocean timezones span the whole globe, any point will be included in some zone!
            Hence there will often be shared boundaries and the results are ambiguous. -> It is not meaningful
            to search just for the closest time zoned (<-> boundary)!

        All polygons within ``delta_degree`` degree lng and lat will be considered.

        .. note:: the algorithm won't find the closest polygon when it's on the 'other end of earth'
            (it can't search beyond the 180 deg lng border!)

        .. note:: x degrees lat are not the same distance apart than x degree lng!
            This is also the reason why there could still be a closer polygon even though you got a result already.
            In order to make sure to get the closest polygon, you should increase the search radius
            until you get a result and then increase it once more (and take that result).
            This should however only make a difference in rare cases.

        :param lng: longitude in degree
        :param lat: latitude in degree
        :param delta_degree: the 'search radius' in degree. determines the polygons to be checked (shortcuts to include)
        :param exact_computation: when enabled the distance to every polygon edge is computed
            (=computationally more expensive!), instead of only evaluating the distances to all the vertices.
            NOTE: This only makes a real difference when polygons are very close.
        :param return_distances: when enabled the output looks like this:
            ``( 'tz_name_of_the_closest_polygon',[ distances to all polygons in km], [tz_names of all polygons])``
        :param force_evaluation: whether all distances should be computed in any case
        :return: the timezone name of the polygon with the closest boundary, the list of distances or None
        """

        def exact_routine(polygon_nr):
            coords = self.coords_of(polygon_nr)
            nr_points = len(coords[0])
            empty_array = empty([2, nr_points], dtype=DTYPE_FORMAT_F_NUMPY)
            return distance_to_polygon_exact(lng, lat, nr_points, coords, empty_array)

        def normal_routine(polygon_nr):
            coords = self.coords_of(polygon_nr)
            nr_points = len(coords[0])
            return distance_to_polygon(lng, lat, nr_points, coords)

        lng, lat = rectify_coordinates(lng, lat)

        # transform point X into cartesian coordinates
        current_closest_id = None
        central_x_shortcut, central_y_shortcut = coord2shortcut(lng, lat)

        lng = radians(lng)
        lat = radians(lat)

        possible_polygons = []

        # there are 2 shortcuts per 1 degree lat, so to cover 1 degree two shortcuts (rows) have to be checked
        # the highest shortcut is 0
        top = max(central_y_shortcut - NR_SHORTCUTS_PER_LAT * delta_degree, 0)
        # the lowest shortcut is 359 (= 2 shortcuts per 1 degree lat)
        bottom = min(central_y_shortcut + NR_SHORTCUTS_PER_LAT * delta_degree, 359)

        # the most left shortcut is 0
        left = max(central_x_shortcut - NR_SHORTCUTS_PER_LNG * delta_degree, 0)
        # the most right shortcut is 359 (= 1 shortcuts per 1 degree lng)
        right = min(central_x_shortcut + NR_SHORTCUTS_PER_LAT * delta_degree, 359)

        # select all the polygons from the surrounding shortcuts
        for x in range(left, right + 1, 1):
            for y in range(top, bottom + 1, 1):
                for p in self.polygon_ids_of_shortcut(x, y):
                    if p not in possible_polygons:
                        possible_polygons.append(p)

        polygons_in_list = len(possible_polygons)

        if polygons_in_list == 0:
            return None

        # initialize the list of ids
        # this list is sorted (see documentation of compile_id_list() )
        possible_polygons, ids, zones_are_equal = self.compile_id_list(
            possible_polygons, polygons_in_list
        )

        # if all the polygons in this shortcut belong to the same zone return it
        timezone_names = getattr(self, TIMEZONE_NAMES)
        if zones_are_equal:
            if not (return_distances or force_evaluation):
                return timezone_names[ids[0]]

        if exact_computation:
            routine = exact_routine
        else:
            routine = normal_routine

        min_distance = MAX_HAVERSINE_DISTANCE
        distances = empty(polygons_in_list, dtype=DTYPE_FORMAT_F_NUMPY)
        # [None for i in range(polygons_in_list)]

        if force_evaluation:
            for pointer, polygon_nr in enumerate(possible_polygons):
                distance = routine(polygon_nr)
                distances[pointer] = distance
                if distance < min_distance:
                    min_distance = distance
                    current_closest_id = ids[pointer]

        else:
            pointer = 0
            # stores which polygons have been checked yet
            already_checked = [False] * polygons_in_list  # initialize array with False
            while pointer < polygons_in_list:
                # only check a polygon when its id is not the closest a the moment and it has not been checked already!
                if already_checked[pointer] or ids[pointer] == current_closest_id:
                    # go to the next polygon
                    pointer += 1

                else:
                    # this polygon has to be checked
                    distance = routine(possible_polygons[pointer])
                    distances[pointer] = distance
                    already_checked[pointer] = True
                    if distance < min_distance:
                        min_distance = distance
                        current_closest_id = ids[pointer]
                        # list of polygons has to be searched again, because closest zone has changed
                        # set pointer to the beginning of the list
                        # having a sorted list of polygon is beneficial here (less common zones come first)
                        pointer = 1

        if return_distances:
            return (
                timezone_names[current_closest_id],
                distances,
                [timezone_names[x] for x in ids],
            )
        return timezone_names[current_closest_id]

    def timezone_at(self, *, lng: float, lat: float) -> str:
        """computes in which ocean OR land timezone a point is included in

        Especially for large polygons it is expensive to check if a point is really included.
        To speed things up there are "shortcuts" being used (stored in a binary file),
        which have been precomputed and store which timezone polygons have to be checked.
        In case there is only one possible zone this zone will instantly be returned without actually checking
        if the query point is included in this polygon -> speed up

        Since ocean timezones span the whole globe, some timezone will always be matched!

        :param lng: longitude of the point in degree (-180.0 to 180.0)
        :param lat: latitude in degree (90.0 to -90.0)
        :return: the timezone name of the matched timezone polygon. possibly "Etc/GMT+-XX" in case of an ocean timezone.
        """
        lng, lat = rectify_coordinates(lng, lat)

        shortcut_id_x, shortcut_id_y = coord2shortcut(lng, lat)
        timezone = self._get_unique_zone(shortcut_id_x, shortcut_id_y)
        if timezone is not None:  # found perfect and fast match
            return timezone
        # more thorough testing required:
        possible_polygons = self.polygon_ids_of_shortcut(shortcut_id_x, shortcut_id_y)
        nr_possible_polygons = len(possible_polygons)
        if nr_possible_polygons == 0:
            raise ValueError(
                "some timezone polygon should be present (ocean timezones exist everywhere)!"
            )
        if nr_possible_polygons == 1:
            # there is only one polygon in that area. return its timezone name without further checks
            return getattr(self, TIMEZONE_NAMES)[self.id_of(possible_polygons[0])]

        # create a list of all the timezone ids of all possible polygons
        ids = self.id_list(possible_polygons, nr_possible_polygons)
        # x = longitude  y = latitude  both converted to 8byte int
        x = coord2int(lng)
        y = coord2int(lat)

        # check until the point is included in one of the possible polygons
        for i in range(nr_possible_polygons):

            # when including the current polygon only polygons from the same zone remain,
            same_element = all_the_same(
                pointer=i, length=nr_possible_polygons, id_list=ids
            )
            if same_element != -1:
                # return the name of that zone
                return getattr(self, TIMEZONE_NAMES)[same_element]

            polygon_nr = possible_polygons[i]

            # get the boundaries of the polygon = (lng_max, lng_min, lat_max, lat_min)
            getattr(self, POLY_MAX_VALUES).seek(4 * NR_BYTES_I * polygon_nr)
            boundaries = self._fromfile(
                getattr(self, POLY_MAX_VALUES),
                dtype=DTYPE_FORMAT_SIGNED_I_NUMPY,
                count=4,
            )
            # only run the expensive algorithm if the point is withing the boundaries
            if not (
                x > boundaries[0]
                or x < boundaries[1]
                or y > boundaries[2]
                or y < boundaries[3]
            ):

                outside_all_holes = True
                # when the point is within a hole of the polygon, this timezone must not be returned
                for hole_coordinates in self._holes_of_poly(polygon_nr):
                    if inside_polygon(x, y, hole_coordinates):
                        outside_all_holes = False
                        break

                if outside_all_holes:
                    if inside_polygon(x, y, self.coords_of(polygon_nr=polygon_nr)):
                        # the point is included in this polygon. return its timezone name without further checks
                        return getattr(self, TIMEZONE_NAMES)[ids[i]]

        # the timezone name of the last polygon should always be returned
        # if no other polygon has been matched beforehand.
        raise ValueError(
            "BUG: this statement should never be reached. Please open up an issue on Github!"
        )

    def certain_timezone_at(self, *, lng: float, lat: float) -> Optional[str]:
        """checks in which timezone polygon the point is certainly included in

        .. note:: this is only meaningful when you use timezone data WITHOUT oceans!
            Otherwise some timezone will always be matched, since ocean timezones span the whole globe.
            -> useless to actually test all polygons.

        .. note:: this is much slower than 'timezone_at'!

        :param lng: longitude of the point in degree
        :param lat: latitude in degree
        :return: the timezone name of the polygon the point is included in or None
        """

        lng, lat = rectify_coordinates(lng, lat)
        shortcut_id_x, shortcut_id_y = coord2shortcut(lng, lat)
        timezone = self._get_unique_zone(shortcut_id_x, shortcut_id_y)
        if timezone is not None:  # found perfect and fast match
            return timezone
        possible_polygons = self.polygon_ids_of_shortcut(shortcut_id_x, shortcut_id_y)

        # x = longitude  y = latitude  both converted to 8byte int
        x = coord2int(lng)
        y = coord2int(lat)

        # check if the point is actually included in one of the polygons
        for polygon_nr in possible_polygons:

            # get boundaries
            getattr(self, POLY_MAX_VALUES).seek(4 * NR_BYTES_I * polygon_nr)
            boundaries = self._fromfile(
                getattr(self, POLY_MAX_VALUES),
                dtype=DTYPE_FORMAT_SIGNED_I_NUMPY,
                count=4,
            )
            if not (
                x > boundaries[0]
                or x < boundaries[1]
                or y > boundaries[2]
                or y < boundaries[3]
            ):

                outside_all_holes = True
                # when the point is within a hole of the polygon this timezone doesn't need to be checked
                for hole_coordinates in self._holes_of_poly(polygon_nr):
                    if inside_polygon(x, y, hole_coordinates):
                        outside_all_holes = False
                        break

                if outside_all_holes:
                    if inside_polygon(x, y, self.coords_of(polygon_nr=polygon_nr)):
                        return getattr(self, TIMEZONE_NAMES)[self.id_of(polygon_nr)]
        return None  # no polygon has been matched
