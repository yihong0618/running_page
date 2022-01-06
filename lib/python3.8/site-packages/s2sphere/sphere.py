from __future__ import print_function, unicode_literals, division

from future.builtins import int
from future.builtins import range

import bisect
import decimal
import functools
import heapq
import math


@functools.total_ordering
class Angle(object):
    """A one-dimensional angle (as opposed to a two-dimensional solid angle).

    It has methods for converting angles to or from radians and degrees.

    :param float radians:
        angle in radians

    see :cpp:class:`S1Angle`
    """

    def __init__(self, radians=0):
        if not isinstance(radians, (float, int)):
            raise ValueError()
        self.__radians = radians

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__radians == other.__radians)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.__radians < other.__radians

    def __add__(self, other):
        return self.__class__.from_radians(self.__radians + other.__radians)

    def __repr__(self):
        return '{}: {}'.format(self.__class__.__name__, self.__radians)

    @classmethod
    def from_degrees(cls, degrees):
        """class generator

        :param float degrees:
            degrees

        """
        return cls(math.radians(degrees))

    @classmethod
    def from_radians(cls, radians):
        return cls(radians)

    @property
    def radians(self):
        return self.__radians

    @property
    def degrees(self):
        return math.degrees(self.__radians)


class Point(object):
    """A point in 3d Euclidean space.

    "Normalized" points are points on the unit sphere.

    see :cpp:type:`S2Point`
    """

    def __init__(self, x, y, z):
        self.__point = (x, y, z)

    def __getitem__(self, index):
        return self.__point[index]

    def __neg__(self):
        return self.__class__(-self[0], -self[1], -self[2])

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__point == other.__point)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__point)

    def __repr__(self):
        return 'Point: {}'.format(self.__point)

    def __add__(self, other):
        return self.__class__(self[0] + other[0],
                              self[1] + other[1],
                              self[2] + other[2])

    def __sub__(self, other):
        return self.__class__(self[0] - other[0],
                              self[1] - other[1],
                              self[2] - other[2])

    def __mul__(self, other):
        return self.__class__(self[0] * other,
                              self[1] * other,
                              self[2] * other)

    def __rmul__(self, other):
        return self.__class__(self[0] * other,
                              self[1] * other,
                              self[2] * other)

    def abs(self):
        return self.__class__(math.fabs(self.__point[0]),
                              math.fabs(self.__point[1]),
                              math.fabs(self.__point[2]))

    def largest_abs_component(self):
        temp = self.abs()
        if temp[0] > temp[1]:
            if temp[0] > temp[2]:
                return 0
            else:
                return 2
        else:
            if temp[1] > temp[2]:
                return 1
            else:
                return 2

    def angle(self, other):
        return math.atan2(self.cross_prod(other).norm(), self.dot_prod(other))

    def cross_prod(self, other):
        x, y, z = self.__point
        ox, oy, oz = other.__point
        return self.__class__(y * oz - z * oy,
                              z * ox - x * oz,
                              x * oy - y * ox)

    def dot_prod(self, other):
        x, y, z = self.__point
        ox, oy, oz = other.__point
        return x * ox + y * oy + z * oz

    def norm2(self):
        x, y, z = self.__point
        return x * x + y * y + z * z

    def norm(self):
        return math.sqrt(self.norm2())

    def normalize(self):
        n = self.norm()
        if n != 0:
            n = 1.0 / n
        return self.__class__(self[0] * n, self[1] * n, self[2] * n)


class LatLng(object):
    """A point on a sphere in latitute-longitude coordinates.

    see :cpp:class:`S2LatLng`
    """

    @classmethod
    def from_degrees(cls, lat, lng):
        return cls(math.radians(lat), math.radians(lng))

    @classmethod
    def from_radians(cls, lat, lng):
        return cls(lat, lng)

    @classmethod
    def from_point(cls, point):
        return cls(LatLng.latitude(point).radians,
                   LatLng.longitude(point).radians)

    @classmethod
    def from_angles(cls, lat, lng):
        return cls(lat.radians, lng.radians)

    @classmethod
    def default(cls):
        return cls(0, 0)

    @classmethod
    def invalid(cls):
        return cls(math.pi, 2 * math.pi)

    def __init__(self, lat, lng):
        self.__coords = (lat, lng)

    def __eq__(self, other):
        return isinstance(other, LatLng) and self.__coords == other.__coords

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__coords)

    def __repr__(self):
        return 'LatLng: {},{}'.format(math.degrees(self.__coords[0]),
                                      math.degrees(self.__coords[1]))

    def __add__(self, other):
        return self.__class__(self.lat().radians + other.lat().radians,
                              self.lng().radians + other.lng().radians)

    def __sub__(self, other):
        return self.__class__(self.lat().radians - other.lat().radians,
                              self.lng().radians - other.lng().radians)

    # only implemented so we can do scalar * LatLng
    def __rmul__(self, other):
        return self.__class__(other * self.lat().radians,
                              other * self.lng().radians)

    @staticmethod
    def latitude(point):
        return Angle.from_radians(
            math.atan2(point[2],
                       math.sqrt(point[0] * point[0] + point[1] * point[1]))
        )

    @staticmethod
    def longitude(point):
        return Angle.from_radians(math.atan2(point[1], point[0]))

    def lat(self):
        return Angle.from_radians(self.__coords[0])

    def lng(self):
        return Angle.from_radians(self.__coords[1])

    def is_valid(self):
        return (abs(self.lat().radians) <= (math.pi / 2) and
                abs(self.lng().radians) <= math.pi)

    def to_point(self):
        phi = self.lat().radians
        theta = self.lng().radians
        cosphi = math.cos(phi)
        return Point(math.cos(theta) * cosphi,
                     math.sin(theta) * cosphi,
                     math.sin(phi))

    def normalized(self):
        return self.__class__(
            max(-math.pi / 2.0, min(math.pi / 2.0, self.lat().radians)),
            drem(self.lng().radians, 2 * math.pi))

    def approx_equals(self, other, max_error=1e-15):
        return (math.fabs(self.lat().radians -
                          other.lat().radians) < max_error and
                math.fabs(self.lng().radians -
                          other.lng().radians) < max_error)

    def get_distance(self, other):
        assert self.is_valid()
        assert other.is_valid()

        from_lat = self.lat().radians
        to_lat = other.lat().radians
        from_lng = self.lng().radians
        to_lng = other.lng().radians
        dlat = math.sin(0.5 * (to_lat - from_lat))
        dlng = math.sin(0.5 * (to_lng - from_lng))
        x = dlat * dlat + dlng * dlng * math.cos(from_lat) * math.cos(to_lat)
        return Angle.from_radians(
            2 * math.atan2(math.sqrt(x), math.sqrt(max(0.0, 1.0 - x)))
        )


class Cap(object):
    """A spherical cap, which is a portion of a sphere cut off by a plane.

    see :cpp:class:`S2Cap`
    """

    ROUND_UP = 1.0 + 1.0 / (1 << 52)

    def __init__(self, axis=Point(1, 0, 0), height=-1):
        self.__axis = axis
        self.__height = height

    def __repr__(self):
        return '{}: {} {}'.format(self.__class__.__name__, self.__axis,
                                  self.__height)

    @classmethod
    def from_axis_height(cls, axis, height):
        assert is_unit_length(axis)
        return cls(axis, height)

    @classmethod
    def from_axis_angle(cls, axis, angle):
        assert is_unit_length(axis)
        assert angle.radians >= 0
        return cls(axis, cls.get_height_for_angle(angle.radians))

    @classmethod
    def get_height_for_angle(cls, radians):
        assert radians >= 0
        if radians >= math.pi:
            return 2

        d = math.sin(0.5 * radians)
        return 2 * d * d

    @classmethod
    def from_axis_area(cls, axis, area):
        assert is_unit_length(axis)
        return cls(axis, area / (2 * math.pi))

    @classmethod
    def empty(cls):
        return cls()

    @classmethod
    def full(cls):
        return cls(Point(1, 0, 0), 2)

    def height(self):
        return self.__height

    def axis(self):
        return self.__axis

    def area(self):
        """2 * pi * height"""
        return 2 * math.pi * max(0.0, self.height())

    def angle(self):
        if self.is_empty():
            return Angle.from_radians(-1)
        return Angle.from_radians(
            2 * math.asin(math.sqrt(0.5 * self.height()))
        )

    def is_valid(self):
        return is_unit_length(self.axis()) and self.height() <= 2

    def is_empty(self):
        return self.height() < 0

    def is_full(self):
        return self.height() >= 2

    def get_cap_bound(self):
        return self

    def add_point(self, point):
        assert is_unit_length(point)
        if self.is_empty():
            self.__axis = point
            self.__height = 0
        else:
            dist2 = (self.axis() - point).norm2()
            self.__height = max(
                self.__height,
                self.__class__.ROUND_UP * 0.5 * dist2,
            )

    def complement(self):
        if self.is_full():
            height = -1
        else:
            height = 2 - max(self.height(), 0.0)
        return self.__class__.from_axis_height(-self.axis(), height)

    def contains(self, other):
        if isinstance(other, self.__class__):
            if self.is_full() or other.is_empty():
                return True
            return (self.angle().radians >=
                    self.axis().angle(other.axis()) + other.angle().radians)
        elif isinstance(other, Point):
            assert is_unit_length(other)
            return (self.axis() - other).norm2() <= 2 * self.height()
        elif isinstance(other, Cell):
            vertices = []
            for k in range(4):
                vertices.append(other.get_vertex(k))
                if not self.contains(vertices[k]):
                    return False
            return not self.complement().intersects(other, vertices)
        else:
            raise NotImplementedError()

    def interior_contains(self, other):
        if isinstance(other, Point):
            assert is_unit_length(other)
            return (self.is_full() or
                    (self.axis() - other).norm2() < 2 * self.height())
        else:
            raise NotImplementedError()

    def intersects(self, *args):
        if len(args) == 1 and isinstance(args[0], self.__class__):
            other = args[0]
            if self.is_empty() or other.is_empty():
                return False
            return (self.angle().radians + other.angle().radians >=
                    self.axis().angle(other.axis()))
        elif len(args) == 2 and isinstance(args[0], Cell) \
                and isinstance(args[1], (list, tuple)):
            cell, vertices = args
            if self.height() >= 1:
                return False
            if self.is_empty():
                return False
            if cell.contains(self.axis()):
                return True

            sin2_angle = self.height() * (2 - self.height())
            for k in range(4):
                edge = cell.get_edge_raw(k)
                dot = self.axis().dot_prod(edge)
                if dot > 0:
                    continue
                if dot * dot > sin2_angle * edge.norm2():
                    return False
                dir = edge.cross_prod(self.axis())
                if dir.dot_prod(vertices[k]) < 0 \
                        and dir.dot_prod(vertices[(k + 1) & 3]) > 0:
                    return True
            return False
        else:
            raise NotImplementedError()

    def may_intersect(self, other):
        vertices = []
        for k in range(4):
            vertices.append(other.get_vertex(k))
            if self.contains(vertices[k]):
                return True
        return self.intersects(other, vertices)

    def interior_intersects(self, other):
        if self.height() <= 0 or other.is_empty():
            return False
        return (self.angle().radians + other.angle().radians >
                self.axis().angle(other.axis()))

    def get_rect_bound(self):
        if self.is_empty():
            return LatLngRect.empty()

        axis_ll = LatLng.from_point(self.axis())
        cap_angle = self.angle().radians

        all_longitudes = False
        lat, lng = [], []
        lng.append(-math.pi)
        lng.append(math.pi)

        lat.append(axis_ll.lat().radians - cap_angle)
        if lat[0] <= -math.pi / 2.0:
            lat[0] = -math.pi / 2.0
            all_longitudes = True

        lat.append(axis_ll.lat().radians + cap_angle)
        if lat[1] >= math.pi / 2.0:
            lat[1] = math.pi / 2.0
            all_longitudes = True

        if not all_longitudes:
            sin_a = math.sqrt(self.height() * (2 - self.height()))
            sin_c = math.cos(axis_ll.lat().radians)
            if sin_a <= sin_c:
                angle_a = math.asin(sin_a / sin_c)
                lng[0] = drem(axis_ll.lng().radians - angle_a, 2 * math.pi)
                lng[1] = drem(axis_ll.lng().radians + angle_a, 2 * math.pi)

        return LatLngRect(LineInterval(*lat), SphereInterval(*lng))

    def approx_equals(self, other, max_error=1e-14):
        return ((self.axis().angle(other.axis()) <= max_error and
                 math.fabs(self.height() - other.height()) <= max_error) or
                (self.is_empty() and other.height() <= max_error) or
                (other.is_empty() and self.height() <= max_error) or
                (self.is_full() and other.height() >= 2 - max_error) or
                (other.is_full() and self.height() >= 2 - max_error))

    def expanded(self, distance):
        assert distance.radians >= 0
        if self.is_empty():
            return self.__class__.empty()
        return self.__class__.from_axis_angle(self.axis(),
                                              self.angle() + distance)


class LatLngRect(object):
    """A rectangle in latitude-longitude space.

    see :cpp:class:`S2LatLngRect`
    """

    def __init__(self, *args):
        if len(args) == 0:
            self.__lat = LineInterval.empty()
            self.__lng = SphereInterval.empty()
        elif isinstance(args[0], LatLng) and isinstance(args[1], LatLng):
            lo, hi = args
            self.__lat = LineInterval(lo.lat().radians, hi.lat().radians)
            self.__lng = SphereInterval(lo.lng().radians, hi.lng().radians)
        elif isinstance(args[0], LineInterval) \
                and isinstance(args[1], SphereInterval):
            self.__lat, self.__lng = args
        else:
            raise NotImplementedError()

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.lat() == other.lat() and self.lng() == other.lng())

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '{}: {}, {}'.format(self.__class__.__name__,
                                   self.lat(), self.lng())

    def lat(self):
        return self.__lat

    def lng(self):
        return self.__lng

    def lat_lo(self):
        return Angle.from_radians(self.lat().lo())

    def lat_hi(self):
        return Angle.from_radians(self.lat().hi())

    def lng_lo(self):
        return Angle.from_radians(self.lng().lo())

    def lng_hi(self):
        return Angle.from_radians(self.lng().hi())

    def lo(self):
        return LatLng.from_angles(self.lat_lo(), self.lng_lo())

    def hi(self):
        return LatLng.from_angles(self.lat_hi(), self.lng_hi())

    # Construct a rectangle of the given size centered around the given point.
    # "center" needs to be normalized, but "size" does not.  The latitude
    # interval of the result is clamped to [-90,90] degrees, and the longitude
    # interval of the result is Full() if and only if the longitude size is
    # 360 degrees or more.  Examples of clamping (in degrees):
    #
    #   center=(80,170),  size=(40,60)   -> lat=[60,90],   lng=[140,-160]
    #   center=(10,40),   size=(210,400) -> lat=[-90,90],  lng=[-180,180]
    #   center=(-90,180), size=(20,50)   -> lat=[-90,-80], lng=[155,-155]
    @classmethod
    def from_center_size(cls, center, size):
        return cls.from_point(center).expanded(0.5 * size)

    @classmethod
    def from_point(cls, p):
        assert p.is_valid()
        return cls(p, p)

    @classmethod
    def from_point_pair(cls, a, b):
        assert a.is_valid()
        assert b.is_valid()
        return LatLngRect(LineInterval.from_point_pair(a.lat().radians,
                                                       b.lat().radians),
                          SphereInterval.from_point_pair(a.lng().radians,
                                                         b.lng().radians))

    @classmethod
    def full_lat(cls):
        return LineInterval(-math.pi / 2.0, math.pi / 2.0)

    @classmethod
    def full_lng(cls):
        return SphereInterval.full()

    @classmethod
    def full(cls):
        return cls(cls.full_lat(), cls.full_lng())

    def is_full(self):
        return self.lat() == self.__class__.full_lat() and self.lng().is_full()

    def is_valid(self):
        return (math.fabs(self.lat().lo()) <= math.pi / 2.0 and
                math.fabs(self.lat().hi()) <= math.pi / 2.0 and
                self.lng().is_valid() and
                self.lat().is_empty() == self.lng().is_empty())

    @classmethod
    def empty(cls):
        return cls()

    def get_center(self):
        return LatLng.from_radians(self.lat().get_center(),
                                   self.lng().get_center())

    def get_size(self):
        return LatLng.from_radians(self.lat().get_length(),
                                   self.lng().get_length())

    def get_vertex(self, k):
        # Twiddle bits to return the points in CCW order (SW, SE, NE, NW)
        return LatLng.from_radians(self.lat().bound(k >> 1),
                                   self.lng().bound((k >> 1) ^ (k & 1)))

    def area(self):
        """Area in steradians."""
        if self.is_empty():
            return 0.0

        return self.lng().get_length() * math.fabs(
            math.sin(self.lat_hi().radians) -
            math.sin(self.lat_lo().radians)
        )

    def is_empty(self):
        return self.lat().is_empty()

    def is_point(self):
        return (self.lat().lo() == self.lat().hi() and
                self.lng().lo() == self.lng().hi())

    def convolve_with_cap(self, angle):
        cap = Cap.from_axis_angle(Point(1, 0, 0), angle)

        r = self
        for k in range(4):
            vertex_cap = Cap.from_axis_height(self.get_vertex(k).to_point(),
                                              cap.height())
            r = r.union(vertex_cap.get_rect_bound())
        return r

    def contains(self, other):
        if isinstance(other, Point):
            return self.contains(LatLng.from_point(other))
        elif isinstance(other, LatLng):
            assert other.is_valid()
            return (self.lat().contains(other.lat().radians) and
                    self.lng().contains(other.lng().radians))
        elif isinstance(other, self.__class__):
            return (self.lat().contains(other.lat()) and
                    self.lng().contains(other.lng()))
        elif isinstance(other, Cell):
            return self.contains(other.get_rect_bound())
        else:
            raise NotImplementedError()

    def interior_contains(self, other):
        if isinstance(other, Point):
            self.interior_contains(LatLng(other))
        elif isinstance(other, LatLng):
            assert other.is_valid()
            return (self.lat().interior_contains(other.lat().radians) and
                    self.lng().interior_contains(other.lng().radians))
        elif isinstance(other, self.__class__):
            return (self.lat().interior_contains(other.lat()) and
                    self.lng().interior_contains(other.lng()))
        else:
            raise NotImplementedError()

    def may_intersect(self, cell):
        return self.intersects(cell.get_rect_bound())

    def intersects(self, *args):
        if isinstance(args[0], self.__class__):
            other = args[0]
            return (self.lat().intersects(other.lat()) and
                    self.lng().intersects(other.lng()))
        elif isinstance(args[0], Cell):
            cell = args[0]
            if self.is_empty():
                return False
            if self.contains(cell.get_center_raw()):
                return True
            if cell.contains(self.get_center().to_point()):
                return True
            if not self.intersects(cell.get_rect_bound()):
                return False

            cell_v = []
            cell_ll = []
            for i in range(4):
                cell_v.append(cell.get_vertex(i))
                cell_ll.append(LatLng.from_point(cell_v[i]))
                if self.contains(cell_ll[i]):
                    return True
                if cell.contains(self.get_vertex(i).to_point()):
                    return True

            for i in range(4):
                edge_lng = SphereInterval.from_point_pair(
                    cell_ll[i].lng().radians,
                    cell_ll[(i + 1) & 3].lng().radians,
                )
                if not self.lng().intersects(edge_lng):
                    continue

                a = cell_v[i]
                b = cell_v[(i + 1) & 3]
                if edge_lng.contains(self.lng().lo()):
                    if self.__class__.intersects_lng_edge(
                            a, b,
                            self.lat(), self.lng().lo()):
                        return True
                if edge_lng.contains(self.lng().hi()):
                    if self.__class__.intersects_lng_edge(
                            a, b,
                            self.lat(), self.lng().hi()):
                        return True
                if self.__class__.intersects_lat_edge(
                        a, b,
                        self.lat().lo(), self.lng()):
                    return True
                if self.__class__.intersects_lat_edge(
                        a, b,
                        self.lat().hi(), self.lng()):
                    return True
            return False
        else:
            raise NotImplementedError()

    @classmethod
    def intersects_lng_edge(cls, a, b, lat, lng):
        return simple_crossing(
            a, b,
            LatLng.from_radians(lat.lo(), lng).to_point(),
            LatLng.from_radians(lat.hi(), lng).to_point(),
        )

    @classmethod
    def intersects_lat_edge(cls, a, b, lat, lng):
        assert is_unit_length(a)
        assert is_unit_length(b)

        z = robust_cross_prod(a, b).normalize()
        if z[2] < 0:
            z = -z

        y = robust_cross_prod(z, Point(0, 0, 1)).normalize()
        x = y.cross_prod(z)
        assert is_unit_length(x)
        assert x[2] >= 0

        sin_lat = math.sin(lat)
        if math.fabs(sin_lat) >= x[2]:
            return False

        assert x[2] > 0
        cos_theta = sin_lat / x[2]
        sin_theta = math.sqrt(1 - cos_theta * cos_theta)
        theta = math.atan2(sin_theta, cos_theta)

        ab_theta = SphereInterval.from_point_pair(
            math.atan2(a.dot_prod(y), a.dot_prod(x)),
            math.atan2(b.dot_prod(y), b.dot_prod(x)),
        )

        if ab_theta.contains(theta):
            isect = x * cos_theta + y * sin_theta
            if lng.contains(math.atan2(isect[1], isect[0])):
                return True
        if ab_theta.contains(-theta):
            isect = x * cos_theta - y * sin_theta
            if lng.contains(math.atan2(isect[1], isect[0])):
                return True
        return False

    def interior_intersects(self, *args):
        if isinstance(args[0], self.__class__):
            other = args[0]
            return (self.lat().interior_intersects(other.lat()) and
                    self.lng().interior_intersects(other.lng()))
        else:
            raise NotImplementedError()

    def union(self, other):
        return self.__class__(self.lat().union(other.lat()),
                              self.lng().union(other.lng()))

    def intersection(self, other):
        lat = self.lat().intersection(other.lat())
        lng = self.lng().intersection(other.lng())
        if lat.is_empty() or lng.is_empty():
            return self.__class__.empty()
        return self.__class__(lat, lng)

    # Return a rectangle that contains all points whose latitude distance from
    # this rectangle is at most margin.lat(), and whose longitude distance
    # from this rectangle is at most margin.lng().  In particular, latitudes
    # are clamped while longitudes are wrapped.  Note that any expansion of an
    # empty interval remains empty, and both components of the given margin
    # must be non-negative.  "margin" does not need to be normalized.
    #
    # NOTE: If you are trying to grow a rectangle by a certain *distance* on
    # the sphere (e.g. 5km), use the ConvolveWithCap() method instead.
    def expanded(self, margin):
        assert margin.lat().radians > 0
        assert margin.lng().radians > 0
        return self.__class__(
            (self.lat()
             .expanded(margin.lat().radians)
             .intersection(self.full_lat())),
            (self.lng()
             .expanded(margin.lng().radians))
        )

    def approx_equals(self, other, max_error=1e-15):
        return (self.lat().approx_equals(other.lat(), max_error) and
                self.lng().approx_equals(other.lng(), max_error))

    def get_cap_bound(self):
        if self.is_empty():
            return Cap.empty()

        if self.lat().lo() + self.lat().hi() < 0:
            pole_z = -1
            pole_angle = math.pi / 2.0 + self.lat().hi()
        else:
            pole_z = 1
            pole_angle = math.pi / 2.0 - self.lat().lo()

        pole_cap = Cap.from_axis_angle(Point(0, 0, pole_z),
                                       Angle.from_radians(pole_angle))

        lng_span = self.lng().hi() - self.lng().lo()
        if drem(lng_span, 2 * math.pi) >= 0:
            if lng_span < 2 * math.pi:
                mid_cap = Cap.from_axis_angle(self.get_center().to_point(),
                                              Angle.from_radians(0))

                for k in range(4):
                    mid_cap.add_point(self.get_vertex(k).to_point())
                if mid_cap.height() < pole_cap.height():
                    return mid_cap
        return pole_cap


# Constants for CellId
LOOKUP_BITS = 4
SWAP_MASK = 0x01
INVERT_MASK = 0x02

POS_TO_IJ = ((0, 1, 3, 2),
             (0, 2, 3, 1),
             (3, 2, 0, 1),
             (3, 1, 0, 2))
POS_TO_ORIENTATION = [SWAP_MASK, 0, 0, INVERT_MASK | SWAP_MASK]
LOOKUP_POS = [None] * (1 << (2 * LOOKUP_BITS + 2))
LOOKUP_IJ = [None] * (1 << (2 * LOOKUP_BITS + 2))


def _init_lookup_cell(level, i, j, orig_orientation, pos, orientation):
    if level == LOOKUP_BITS:
        ij = (i << LOOKUP_BITS) + j
        LOOKUP_POS[(ij << 2) + orig_orientation] = (pos << 2) + orientation
        LOOKUP_IJ[(pos << 2) + orig_orientation] = (ij << 2) + orientation
    else:
        level = level + 1
        i <<= 1
        j <<= 1
        pos <<= 2
        r = POS_TO_IJ[orientation]
        for index in range(4):
            _init_lookup_cell(
                level, i + (r[index] >> 1),
                j + (r[index] & 1), orig_orientation,
                pos + index, orientation ^ POS_TO_ORIENTATION[index],
            )


_init_lookup_cell(0, 0, 0, 0, 0, 0)
_init_lookup_cell(0, 0, 0, SWAP_MASK, 0, SWAP_MASK)
_init_lookup_cell(0, 0, 0, INVERT_MASK, 0, INVERT_MASK)
_init_lookup_cell(0, 0, 0, SWAP_MASK | INVERT_MASK, 0, SWAP_MASK | INVERT_MASK)


@functools.total_ordering
class CellId(object):
    """S2 cell id

    The 64-bit ID has:

    - 3 bits to encode the face
    - 0-60 bits to encode the position
    - a 1

    The final 1 is the least significant bit (lsb) in the underlying integer
    representation and is returned with :func:`s2sphere.CellId.lsb`.

    see :cpp:class:`S2CellId`
    """

    # projection types
    LINEAR_PROJECTION = 0
    TAN_PROJECTION = 1
    QUADRATIC_PROJECTION = 2

    # current projection used
    PROJECTION = QUADRATIC_PROJECTION

    FACE_BITS = 3
    NUM_FACES = 6

    MAX_LEVEL = 30
    POS_BITS = 2 * MAX_LEVEL + 1
    MAX_SIZE = 1 << MAX_LEVEL

    WRAP_OFFSET = NUM_FACES << POS_BITS

    def __init__(self, id_=0):
        self.__id = id_ % 0xffffffffffffffff

    def __repr__(self):
        return 'CellId: {:016x}'.format(self.id())

    def __hash__(self):
        return hash(self.id())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.id() == other.id()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __lt__(self, other):
        return self.id() < other.id()

    @classmethod
    def from_lat_lng(cls, ll):
        return cls.from_point(ll.to_point())

    @classmethod
    def from_point(cls, p):
        face, u, v = xyz_to_face_uv(p)
        i = cls.st_to_ij(cls.uv_to_st(u))
        j = cls.st_to_ij(cls.uv_to_st(v))
        return cls.from_face_ij(face, i, j)

    @classmethod
    def from_face_pos_level(cls, face, pos, level):
        return cls((face << cls.POS_BITS) + (pos | 1)).parent(level)

    @classmethod
    def from_face_ij(cls, face, i, j):
        n = face << (cls.POS_BITS - 1)
        bits = face & SWAP_MASK

        for k in range(7, -1, -1):
            mask = (1 << LOOKUP_BITS) - 1
            bits += (((i >> (k * LOOKUP_BITS)) & mask) << (LOOKUP_BITS + 2))
            bits += (((j >> (k * LOOKUP_BITS)) & mask) << 2)
            bits = LOOKUP_POS[bits]
            n |= (bits >> 2) << (k * 2 * LOOKUP_BITS)
            bits &= (SWAP_MASK | INVERT_MASK)

        return cls(n * 2 + 1)

    @classmethod
    def from_face_ij_wrap(cls, face, i, j):
        # Convert i and j to the coordinates of a leaf cell just beyond the
        # boundary of this face.  This prevents 32-bit overflow in the case
        # of finding the neighbors of a face cell
        i = max(-1, min(cls.MAX_SIZE, i))
        j = max(-1, min(cls.MAX_SIZE, j))

        # Find the (u,v) coordinates corresponding to the center of cell (i,j).
        # For our purposes it's sufficient to always use the linear projection
        # from (s,t) to (u,v): u=2*s-1 and v=2*t-1.
        scale = 1.0 / cls.MAX_SIZE
        u = scale * ((i << 1) + 1 - cls.MAX_SIZE)
        v = scale * ((j << 1) + 1 - cls.MAX_SIZE)

        # Find the leaf cell coordinates on the adjacent face, and convert
        # them to a cell id at the appropriate level.  We convert from (u,v)
        # back to (s,t) using s=0.5*(u+1), t=0.5*(v+1).
        face, u, v = xyz_to_face_uv(face_uv_to_xyz(face, u, v))
        return cls.from_face_ij(
            face,
            cls.st_to_ij(0.5 * (u + 1)),
            cls.st_to_ij(0.5 * (v + 1)),
        )

    @classmethod
    def from_face_ij_same(cls, face, i, j, same_face):
        if same_face:
            return cls.from_face_ij(face, i, j)
        else:
            return cls.from_face_ij_wrap(face, i, j)

    @classmethod
    def st_to_ij(cls, s):
        return max(0, min(cls.MAX_SIZE - 1, int(math.floor(cls.MAX_SIZE * s))))

    @classmethod
    def lsb_for_level(cls, level):
        return 1 << (2 * (cls.MAX_LEVEL - level))

    def parent(self, *args):
        assert self.is_valid()
        if len(args) == 0:
            assert not self.is_face()
            new_lsb = self.lsb() << 2
            return self.__class__((self.id() & -new_lsb) | new_lsb)
        elif len(args) == 1:
            level = args[0]
            assert level >= 0
            assert level <= self.level()
            new_lsb = self.__class__.lsb_for_level(level)
            return self.__class__((self.id() & -new_lsb) | new_lsb)

    def child(self, pos):
        assert self.is_valid()
        assert not self.is_leaf()
        new_lsb = self.lsb() >> 2
        return self.__class__(self.id() + (2 * pos + 1 - 4) * new_lsb)

    def contains(self, other):
        assert self.is_valid()
        assert other.is_valid()
        return other >= self.range_min() and other <= self.range_max()

    def intersects(self, other):
        assert self.is_valid()
        assert other.is_valid()
        return (other.range_min() <= self.range_max() and
                other.range_max() >= self.range_min())

    def is_face(self):
        return (self.id() & (self.lsb_for_level(0) - 1)) == 0

    def id(self):
        return self.__id

    def is_valid(self):
        return ((self.face() < self.__class__.NUM_FACES) and
                (self.lsb() & 0x1555555555555555) != 0)

    def lsb(self):
        return self.id() & -self.id()

    def face(self):
        return self.id() >> self.__class__.POS_BITS

    def pos(self):
        # is this correct?
        return self.id() & (0xffffffffffffffff >> self.__class__.FACE_BITS)

    def is_leaf(self):
        return (self.id() & 1) != 0

    def level(self):
        if self.is_leaf():
            return self.__class__.MAX_LEVEL

        x = (self.id() & 0xffffffff)
        level = -1
        if x != 0:
            level += 16
        else:
            # is this correct?
            x = ((self.id() >> 32) & 0xffffffff)

        x &= -x
        if x & 0x00005555:
            level += 8
        if x & 0x00550055:
            level += 4
        if x & 0x05050505:
            level += 2
        if x & 0x11111111:
            level += 1

        assert level >= 0
        assert level <= self.__class__.MAX_LEVEL
        return level

    def child_begin(self, *args):
        assert self.is_valid()
        if len(args) == 0:
            assert not self.is_leaf()

            old_lsb = self.lsb()
            return self.__class__(self.id() - old_lsb + (old_lsb >> 2))
        elif len(args) == 1:
            level = args[0]
            assert level >= self.level()
            assert level <= self.__class__.MAX_LEVEL
            return (self.__class__(self.id() - self.lsb() +
                    self.__class__.lsb_for_level(level)))
        else:
            raise ValueError('no args or level arg')

    def child_end(self, *args):
        assert self.is_valid()
        if len(args) == 0:
            assert not self.is_leaf()
            old_lsb = self.lsb()
            return self.__class__(self.id() + old_lsb + (old_lsb >> 2))
        elif len(args) == 1:
            level = args[0]
            assert level >= self.level()
            assert level <= self.__class__.MAX_LEVEL
            return (self.__class__(self.id() + self.lsb() +
                    self.__class__.lsb_for_level(level)))
        else:
            raise ValueError('no args or level arg')

    def prev(self):
        return self.__class__(self.id() - (self.lsb() << 1))

    def next(self):
        return self.__class__(self.id() + (self.lsb() << 1))

    def children(self, *args):
        cell_id = self.child_begin(*args)
        end = self.child_end(*args)
        while cell_id != end:
            yield cell_id
            cell_id = cell_id.next()

    def range_min(self):
        return self.__class__(self.id() - (self.lsb() - 1))

    def range_max(self):
        return self.__class__(self.id() + (self.lsb() - 1))

    @classmethod
    def begin(cls, level):
        return cls.from_face_pos_level(0, 0, 0).child_begin(level)

    @classmethod
    def end(cls, level):
        return cls.from_face_pos_level(5, 0, 0).child_end(level)

    @classmethod
    def walk(cls, level):
        """Walk along a Hilbert curve at the given level.

        This function does not exist in the SWIG bindings of the original C++
        library. It provides a more Pythonic way to iterate over cells.

        :returns:
            Iterator over instances of :class:`CellId` s.
        """
        cellid_int = cls.begin(level).id()
        endid_int = cls.end(level).id()

        # Doubling the lsb yields the increment between positions at a certain
        # level as 64-bit IDs. See CellId docstring for bit encoding.
        increment = cls.begin(level).lsb() << 1

        while cellid_int != endid_int:
            yield cls(cellid_int)
            cellid_int += increment

    @classmethod
    def walk_fast(cls, level):
        """Walk along a Hilbert curve at the given level.

        This function does not exist in the SWIG bindings of the original C++
        library. It provides a more Pythonic way to iterate over cells.

        Use with caution: this repeatedly mutates a single instance with a
        changing ``id``. If you save the object, it will change out from
        underneath you.

        :returns:
            Iterator over ids in the same instance of :class:`CellId`.
        """
        instance = cls.begin(level)
        cellid_int = instance.id()
        endid_int = cls.end(level).id()

        # Doubling the lsb yields the increment between positions at a certain
        # level as 64-bit IDs. See CellId docstring for bit encoding.
        increment = instance.lsb() << 1

        while cellid_int != endid_int:
            instance.__id = cellid_int
            yield instance
            cellid_int += increment

    @classmethod
    def none(cls):
        return cls()

    def prev_wrap(self):
        assert self.is_valid()
        p = self.prev()
        if p.id() < self.__class__.WRAP_OFFSET:
            return p
        else:
            return self.__class__(p.id() + self.__class__.WRAP_OFFSET)

    def next_wrap(self):
        assert self.is_valid()
        n = self.next()
        if n.id() < self.__class__.WRAP_OFFSET:
            return n
        else:
            return self.__class__(n.id() - self.__class__.WRAP_OFFSET)

    def advance_wrap(self, steps):
        assert self.is_valid()
        if steps == 0:
            return self

        step_shift = 2 * (self.__class__.MAX_LEVEL - self.level()) + 1
        if steps < 0:
            min_steps = -(self.id() >> step_shift)
            if steps < min_steps:
                step_wrap = self.__class__.WRAP_OFFSET >> step_shift
                # cannot use steps %= step_wrap as Python % different to C++
                steps = int(math.fmod(steps, step_wrap))
                if steps < min_steps:
                    steps += step_wrap
        else:
            max_steps = (self.__class__.WRAP_OFFSET - self.id()) >> step_shift
            if steps > max_steps:
                step_wrap = self.__class__.WRAP_OFFSET >> step_shift
                # cannot use steps %= step_wrap as Python % different to C++
                steps = int(math.fmod(steps, step_wrap))
                if steps > max_steps:
                    steps -= step_wrap

        return self.__class__(self.id() + (steps << step_shift))

    def advance(self, steps):
        if steps == 0:
            return self

        step_shift = 2 * (self.__class__.MAX_LEVEL - self.level()) + 1
        if steps < 0:
            min_steps = -(self.id() >> step_shift)
            if steps < min_steps:
                steps = min_steps
        else:
            max_steps = (self.__class__.WRAP_OFFSET +
                         self.lsb() - self.id()) >> step_shift
            if steps > max_steps:
                steps = max_steps

        return self.__class__(self.id() + (steps << step_shift))

    # Return the S2LatLng corresponding to the center of the given cell.
    def to_lat_lng(self):
        return LatLng.from_point(self.to_point_raw())

    def to_point_raw(self):
        face, si, ti = self.get_center_si_ti()
        return face_uv_to_xyz(
            face,
            self.__class__.st_to_uv((0.5 / self.__class__.MAX_SIZE) * si),
            self.__class__.st_to_uv((0.5 / self.__class__.MAX_SIZE) * ti),
        )

    def to_point(self):
        return self.to_point_raw().normalize()

    def get_center_si_ti(self):
        face, i, j, orientation = self.to_face_ij_orientation()
        if self.is_leaf():
            delta = 1
        elif ((i ^ (self.id() >> 2)) & 1) != 0:
            delta = 2
        else:
            delta = 0

        return face, 2 * i + delta, 2 * j + delta

    def get_center_uv(self):
        """center of the cell in (u, v) coordinates

        :rtype: pair
        """
        face, si, ti = self.get_center_si_ti()
        cls = self.__class__
        return (cls.st_to_uv((0.5 / cls.MAX_SIZE) * si),
                cls.st_to_uv((0.5 / cls.MAX_SIZE) * ti))

    def to_face_ij_orientation(self):
        i, j = 0, 0
        face = self.face()
        bits = (face & SWAP_MASK)

        for k in range(7, -1, -1):
            if k == 7:
                nbits = (self.__class__.MAX_LEVEL - 7 * LOOKUP_BITS)
            else:
                nbits = LOOKUP_BITS

            bits += (
                self.id() >> (k * 2 * LOOKUP_BITS + 1) &
                ((1 << (2 * nbits)) - 1)
            ) << 2
            bits = LOOKUP_IJ[bits]
            i += (bits >> (LOOKUP_BITS + 2)) << (k * LOOKUP_BITS)
            j += ((bits >> 2) & ((1 << LOOKUP_BITS) - 1)) << (k * LOOKUP_BITS)
            bits &= (SWAP_MASK | INVERT_MASK)

        assert 0 == POS_TO_ORIENTATION[2]
        assert SWAP_MASK == POS_TO_ORIENTATION[0]
        if (self.lsb() & 0x1111111111111110) != 0:
            bits ^= SWAP_MASK
        orientation = bits

        return face, i, j, orientation

    def get_edge_neighbors(self):
        level = self.level()
        size = self.get_size_ij(level)
        face, i, j, orientation = self.to_face_ij_orientation()

        return (self.from_face_ij_same(face, i, j - size, j - size >= 0)
                .parent(level),
                self.from_face_ij_same(face, i + size, j,
                                       i + size < self.__class__.MAX_SIZE
                                       ).parent(level),
                self.from_face_ij_same(face, i, j + size,
                                       j + size < self.__class__.MAX_SIZE
                                       ).parent(level),
                self.from_face_ij_same(face, i - size, j, i - size >= 0)
                .parent(level))

    def get_vertex_neighbors(self, level):
        """Return the neighbors of closest vertex to this cell.

        Normally there are four neighbors, but the closest vertex may only have
        three neighbors if it is one of the 8 cube vertices.
        """
        # "level" must be strictly less than this cell's level so that we can
        # determine which vertex this cell is closest to.
        assert level < self.level()
        face, i, j, orientation = self.to_face_ij_orientation()

        # Determine the i- and j-offsets to the closest neighboring cell in
        # each direction.  This involves looking at the next bit of "i" and
        # "j" to determine which quadrant of this->parent(level) this cell
        # lies in.
        halfsize = self.get_size_ij(level + 1)
        size = halfsize << 1
        if i & halfsize:
            ioffset = size
            isame = (i + size) < self.__class__.MAX_SIZE
        else:
            ioffset = -size
            isame = (i - size) >= 0
        if j & halfsize:
            joffset = size
            jsame = (j + size) < self.__class__.MAX_SIZE
        else:
            joffset = -size
            jsame = (j - size) >= 0

        neighbors = []
        neighbors.append(self.parent(level))
        neighbors.append(
            self.__class__
            .from_face_ij_same(face, i + ioffset, j, isame)
            .parent(level)
        )
        neighbors.append(
            self.__class__
            .from_face_ij_same(face, i, j + joffset, jsame)
            .parent(level)
        )
        if isame or jsame:
            neighbors.append(
                self.__class__
                .from_face_ij_same(face, i + ioffset, j + joffset,
                                   isame and jsame)
                .parent(level)
            )

        return neighbors

    def get_all_neighbors(self, nbr_level):
        face, i, j, orientation = self.to_face_ij_orientation()

        # Find the coordinates of the lower left-hand leaf cell.  We need to
        # normalize (i,j) to a known position within the cell because nbr_level
        # may be larger than this cell's level.
        size = self.get_size_ij()
        i &= -size
        j &= -size

        nbr_size = self.get_size_ij(nbr_level)
        assert nbr_size <= size

        # We compute the N-S, E-W, and diagonal neighbors in one pass.
        # The loop test is at the end of the loop to avoid 32-bit overflow.
        k = -nbr_size
        while True:
            if k < 0:
                same_face = (j + k >= 0)
            elif k >= size:
                same_face = (j + k < self.__class__.MAX_SIZE)
            else:
                same_face = False
                # North and South neighbors.
                yield (self.__class__
                       .from_face_ij_same(face, i + k, j - nbr_size,
                                          j - size >= 0)
                       .parent(nbr_level))
                yield (self.__class__
                       .from_face_ij_same(face, i + k, j + size,
                                          j + size < self.__class__.MAX_SIZE)
                       .parent(nbr_level))

            yield (self.__class__
                   .from_face_ij_same(face, i - nbr_size, j + k,
                                      same_face and i - size >= 0)
                   .parent(nbr_level))
            yield (self.__class__
                   .from_face_ij_same(face, i + size, j + k,
                                      same_face and
                                      i + size < self.__class__.MAX_SIZE)
                   .parent(nbr_level))

            if k >= size:
                break
            k += nbr_size

    def get_size_ij(self, *args):
        if len(args) == 0:
            level = self.level()
        else:
            level = args[0]
        return 1 << (self.__class__.MAX_LEVEL - level)

    def to_token(self):
        """A unique string token for this cell id.

        This is a hex encoded version of the cell id with the right zeros
        stripped of.
        """
        return format(self.id(), '016x').rstrip('0')

    @classmethod
    def from_token(cls, token):
        """Creates a CellId from a hex encoded cell id string, called a token.

        :param str token:
            A hex representation of the cell id. If the input is shorter than
            16 characters, zeros are appended on the right.
        """
        return cls(int(token.ljust(16, '0'), 16))

    @classmethod
    def st_to_uv(cls, s):
        if cls.PROJECTION == cls.LINEAR_PROJECTION:
            return 2 * s - 1
        elif cls.PROJECTION == cls.TAN_PROJECTION:
            s = math.tan((math.pi / 2.0) * s - math.pi / 4.0)
            return s + (1.0 / (1 << 53)) * s
        elif cls.PROJECTION == cls.QUADRATIC_PROJECTION:
            if s >= 0.5:
                return (1.0 / 3.0) * (4 * s * s - 1)
            else:
                return (1.0 / 3.0) * (1 - 4 * (1 - s) * (1 - s))
        else:
            raise ValueError('unknown projection type')

    @classmethod
    def uv_to_st(cls, u):
        if cls.PROJECTION == cls.LINEAR_PROJECTION:
            return 0.5 * (u + 1)
        elif cls.PROJECTION == cls.TAN_PROJECTION:
            return (2 * (1.0 / math.pi)) * (math.atan(u) * math.pi / 4.0)
        elif cls.PROJECTION == cls.QUADRATIC_PROJECTION:
            if u >= 0:
                return 0.5 * math.sqrt(1 + 3 * u)
            else:
                return 1 - 0.5 * math.sqrt(1 - 3 * u)
        else:
            raise ValueError('unknown projection type')

    @classmethod
    def max_edge(cls):
        return LengthMetric(cls.max_angle_span().deriv())

    @classmethod
    def max_angle_span(cls):
        if cls.PROJECTION == cls.LINEAR_PROJECTION:
            return LengthMetric(2)
        elif cls.PROJECTION == cls.TAN_PROJECTION:
            return LengthMetric(math.pi / 2)
        elif cls.PROJECTION == cls.QUADRATIC_PROJECTION:
            return LengthMetric(1.704897179199218452)
        else:
            raise ValueError('unknown projection type')

    @classmethod
    def max_diag(cls):
        if cls.PROJECTION == cls.LINEAR_PROJECTION:
            return LengthMetric(2 * math.sqrt(2))
        elif cls.PROJECTION == cls.TAN_PROJECTION:
            return LengthMetric(math.pi * math.sqrt(2.0 / 3.0))
        elif cls.PROJECTION == cls.QUADRATIC_PROJECTION:
            return LengthMetric(2.438654594434021032)
        else:
            raise ValueError('unknown projection type')

    @classmethod
    def min_width(cls):
        if cls.PROJECTION == cls.LINEAR_PROJECTION:
            return LengthMetric(math.sqrt(2))
        elif cls.PROJECTION == cls.TAN_PROJECTION:
            return LengthMetric(math.pi / 2 * math.sqrt(2))
        elif cls.PROJECTION == cls.QUADRATIC_PROJECTION:
            return LengthMetric(2 * math.sqrt(2) / 3)
        else:
            raise ValueError('unknown projection type')


class Metric(object):
    """Metric

    The classes :class:`s2sphere.LengthMetric` and
    :class:`s2sphere.AreaMetric` are specializations of this class.

    see :cpp:class:`S2::Metric`
    """

    def __init__(self, deriv, dim):
        self.__deriv = deriv
        self.__dim = dim

    def deriv(self):
        return self.__deriv

    def get_value(self, level):
        """The value of this metric at a given level.

        :returns:
            Depending on whether this is used in one or two dimensions, this is
            an angle in radians or a solid angle in steradians.
        """
        return math.ldexp(self.deriv(), -self.__dim * level)

    def get_closest_level(self, value):
        """Closest cell level according to the given value.

        Return the level at which the metric has approximately the given
        value.  For example, ``s2sphere.AVG_EDGE.get_closest_level(0.1)``
        returns the level at which the average cell edge length is
        approximately 0.1. The return value is always a valid level.

        :param value:
            Depending on whether this is used in one or two dimensions, this is
            an angle in radians or a solid angle in steradians.
        """
        return self.get_min_level(
            (math.sqrt(2) if self.__dim == 1 else 2) * value
        )

    def get_min_level(self, value):
        """Minimum cell level for given value.

        Return the minimum level such that the metric is at most the given
        value, or ``s2sphere.CellId.MAX_LEVEL`` if there is no such level.
        For example, ``s2sphere.MAX_DIAG.get_min_level(0.1)`` returns the
        minimum level such that all cell diagonal lengths are 0.1 or smaller.
        The return value is always a valid level.

        :param value:
            Depending on whether this is used in one or two dimensions, this is
            an angle in radians or a solid angle in steradians.
        """
        if value <= 0:
            return CellId.MAX_LEVEL

        m, x = math.frexp(value / self.deriv())
        level = max(0, min(CellId.MAX_LEVEL, -((x - 1) >> (self.__dim - 1))))
        assert level == CellId.MAX_LEVEL or self.get_value(level) <= value
        assert level == 0 or self.get_value(level - 1) > value
        return level

    def get_max_level(self, value):
        """Maximum cell level for given value.

        Return the maximum level such that the metric is at least the given
        value, or zero if there is no such level.  For example,
        ``s2sphere.MIN_WIDTH.get_max_level(0.1)`` returns the maximum level
        such that all cells have a minimum width of 0.1 or larger.
        The return value is always a valid level.

        :param value:
            Depending on whether this is used in one or two dimensions, this is
            an angle in radians or a solid angle in steradians.
        """
        if value <= 0:
            return CellId.MAX_LEVEL

        m, x = math.frexp(self.deriv() / value)
        level = max(0, min(CellId.MAX_LEVEL, (x - 1) >> (self.__dim - 1)))
        assert level == 0 or self.get_value(level) >= value
        assert level == CellId.MAX_LEVEL or self.get_value(level + 1) < value
        return level


class LengthMetric(Metric):
    """Length metric. A 1D specialization of :class:`s2sphere.Metric`.

    Preconfigured instances of this class are
    :const:`s2sphere.AVG_ANGLE_SPAN`,
    :const:`s2sphere.MIN_ANGLE_SPAN`,
    :const:`s2sphere.MAX_ANGLE_SPAN`,
    :const:`s2sphere.AVG_EDGE`,
    :const:`s2sphere.MIN_EDGE`,
    :const:`s2sphere.MAX_EDGE`,
    :const:`s2sphere.AVG_DIAG`,
    :const:`s2sphere.MIN_DIAG`,
    :const:`s2sphere.MAX_DIAG`,
    :const:`s2sphere.AVG_WIDTH`,
    :const:`s2sphere.MIN_WIDTH` and
    :const:`s2sphere.MAX_WIDTH`.

    see :cpp:class:`S2::LengthMetric`
    """
    def __init__(self, deriv):
        super(LengthMetric, self).__init__(deriv, 1)


AVG_ANGLE_SPAN = LengthMetric(math.pi / 2)  # true for all projections
MIN_ANGLE_SPAN = LengthMetric(4 / 3)  # quadratic projection
MAX_ANGLE_SPAN = LengthMetric(1.704897179199218452)  # quadratic projection

AVG_EDGE = LengthMetric(1.459213746386106062)  # quadratic projection
MIN_EDGE = LengthMetric(2 * math.sqrt(2) / 3)  # quadratic projection
MAX_EDGE = LengthMetric(MAX_ANGLE_SPAN.deriv())  # true for all projections

AVG_DIAG = LengthMetric(2.060422738998471683)  # quadratic projection
MIN_DIAG = LengthMetric(8 * math.sqrt(2) / 9)  # quadratic projection
MAX_DIAG = LengthMetric(2.438654594434021032)  # quadratic projection

AVG_WIDTH = LengthMetric(1.434523672886099389)  # quadratic projection
MIN_WIDTH = LengthMetric(2 * math.sqrt(2) / 3)  # quadratic projection
MAX_WIDTH = LengthMetric(MAX_ANGLE_SPAN.deriv())  # true for all projections


class AreaMetric(Metric):
    """Area metric. A 2D specialization of `s2sphere.Metric` (check for API).

    Preconfigured instances of this class are `s2sphere.AVG_AREA`,
    `s2sphere.MIN_AREA`, `s2sphere.MAX_AREA`.

    See C++ docs at :cpp:class:`S2::AreaMetric`.
    """
    def __init__(self, deriv):
        super(AreaMetric, self).__init__(deriv, 2)


#: Average cell area for all projections.
AVG_AREA = AreaMetric(4 * math.pi / 6)


#: Minimum cell area for quadratic projections.
MIN_AREA = AreaMetric(8 * math.sqrt(2) / 9)


#: Maximum cell area for quadratic projections.
MAX_AREA = AreaMetric(2.635799256963161491)


def drem(x, y):
    """Like fmod but rounds to nearest integer instead of floor."""
    xd = decimal.Decimal(x)
    yd = decimal.Decimal(y)
    return float(xd.remainder_near(yd))


def valid_face_xyz_to_uv(face, p):
    assert p.dot_prod(face_uv_to_xyz(face, 0, 0)) > 0
    if face == 0:
        return p[1] / p[0], p[2] / p[0]
    elif face == 1:
        return -p[0] / p[1], p[2] / p[1]
    elif face == 2:
        return -p[0] / p[2], -p[1] / p[2]
    elif face == 3:
        return p[2] / p[0], p[1] / p[0]
    elif face == 4:
        return p[2] / p[1], -p[0] / p[1]
    else:
        return -p[1] / p[2], -p[0] / p[2]


def xyz_to_face_uv(p):
    face = p.largest_abs_component()
    if p[face] < 0:
        face += 3
    u, v = valid_face_xyz_to_uv(face, p)
    return face, u, v


def face_xyz_to_uv(face, p):
    """(face, XYZ) to UV

    see :cpp:func:`S2::FaceXYZtoUV`
    """
    if face < 3:
        if p[face] <= 0:
            return False, 0, 0
    else:
        if p[face - 3] >= 0:
            return False, 0, 0
    u, v = valid_face_xyz_to_uv(face, p)
    return True, u, v


def face_uv_to_xyz(face, u, v):
    """(face, u, v) to xyz

    see :cpp:func:`S2::FaceUVtoXYZ`
    """
    if face == 0:
        return Point(1, u, v)
    elif face == 1:
        return Point(-u, 1, v)
    elif face == 2:
        return Point(-u, -v, 1)
    elif face == 3:
        return Point(-1, -v, -u)
    elif face == 4:
        return Point(v, -1, -u)
    else:
        return Point(v, u, -1)


def get_norm(face):
    return face_uv_to_xyz(face, 0, 0)


def get_u_norm(face, u):
    """Vector normal to the positive v-axis and the plane through the origin.

    The vector is normal to the positive v-axis and a plane that contains the
    origin and the v-axis.

    The right-handed normal (not necessarily unit length) for an
    edge in the direction of the positive v-axis at the given u-value on
    the given face.  (This vector is perpendicular to the plane through
    the sphere origin that contains the given edge.)

    :rtype: Point

    see :cpp:func:`S2::GetUNorm`
    """
    if face == 0:
        return Point(u, -1, 0)
    elif face == 1:
        return Point(1, u, 0)
    elif face == 2:
        return Point(1, 0, u)
    elif face == 3:
        return Point(-u, 0, 1)
    elif face == 4:
        return Point(0, -u, 1)
    else:
        return Point(0, -1, -u)


def get_v_norm(face, v):
    """Vector normal to the positive u-axis and the plane through the origin.

    The vector is normal to the positive u-axis and a plane that contains the
    origin and the u-axis.

    Return the right-handed normal (not necessarily unit length) for an
    edge in the direction of the positive u-axis at the given v-value on
    the given face.

    see :cpp:func:`S2::GetVNorm`
    """
    if face == 0:
        return Point(-v, 0, 1)
    elif face == 1:
        return Point(0, -v, 1)
    elif face == 2:
        return Point(0, -1, -v)
    elif face == 3:
        return Point(v, -1, 0)
    elif face == 4:
        return Point(1, v, 0)
    else:
        return Point(1, 0, v)


def get_u_axis(face):
    if face == 0:
        return Point(0, 1, 0)
    elif face == 1:
        return Point(-1, 0, 0)
    elif face == 2:
        return Point(-1, 0, 0)
    elif face == 3:
        return Point(0, 0, -1)
    elif face == 4:
        return Point(0, 0, -1)
    else:
        return Point(0, 1, 0)


def get_v_axis(face):
    if face == 0:
        return Point(0, 0, 1)
    elif face == 1:
        return Point(0, 0, 1)
    elif face == 2:
        return Point(0, -1, 0)
    elif face == 3:
        return Point(0, -1, 0)
    elif face == 4:
        return Point(1, 0, 0)
    else:
        return Point(1, 0, 0)


def is_unit_length(p):
    return math.fabs(p.norm() * p.norm() - 1) <= 1e-15


def ortho(a):
    """see :cpp:func:`S2::Ortho`"""
    k = a.largest_abs_component() - 1
    if k < 0:
        k = 2
    if k == 0:
        temp = Point(1, 0.0053, 0.00457)
    elif k == 1:
        temp = Point(0.012, 1, 0.00457)
    else:
        temp = Point(0.012, 0.0053, 1)
    return a.cross_prod(temp).normalize()


def origin():
    """A unique and empirically chosen reference point.

    see :cpp:func:`S2::Origin`
    """
    return Point(0.00457, 1, 0.0321).normalize()


def robust_cross_prod(a, b):
    """A numerically more robust cross product.

    The direction of :math:`a \\times b` becomes unstable as :math:`(a + b)` or
    :math:`(a - b)` approaches zero.  This leads to situations where
    :math:`a \\times b` is not very orthogonal to :math:`a` and/or :math:`b`.
    We could fix this using Gram-Schmidt, but we also want
    :math:`b \\times a = - a \\times b`.

    The easiest fix is to just compute the cross product of :math:`(b+a)` and
    :math:`(b-a)`. Mathematically, this cross product is exactly twice the
    cross product of :math:`a` and :math:`b`, but it has the numerical
    advantage that :math:`(b+a)` and :math:`(b-a)` are always perpendicular
    (since :math:`a` and :math:`b` are unit length).  This
    yields a result that is nearly orthogonal to both :math:`a` and :math:`b`
    even if these two values differ only in the lowest bit of one component.

    see :cpp:func:`S2::RobustCrossProd`
    """
    assert is_unit_length(a)
    assert is_unit_length(b)

    x = (b + a).cross_prod(b - a)
    if x != Point(0, 0, 0):
        return x

    return ortho(a)


def simple_crossing(a, b, c, d):
    """see :cpp:func:`S2EdgeUtil::SimpleCrossing`"""
    ab = a.cross_prod(b)
    acb = -(ab.dot_prod(c))
    bda = ab.dot_prod(d)
    if acb * bda <= 0:
        return False

    cd = c.cross_prod(d)
    cbd = -(cd.dot_prod(b))
    dac = cd.dot_prod(a)
    return (acb * cbd > 0) and (acb * dac > 0)


def girard_area(a, b, c):
    """see :cpp:func:`S2::GirardArea`"""
    ab = robust_cross_prod(a, b)
    bc = robust_cross_prod(b, c)
    ac = robust_cross_prod(a, c)
    return max(0.0, ab.angle(ac) - ab.angle(bc) + bc.angle(ac))


def area(a, b, c):
    """Area of the triangle (a, b, c).

    see :cpp:func:`S2::Area`
    """
    assert is_unit_length(a)
    assert is_unit_length(b)
    assert is_unit_length(c)

    sa = b.angle(c)
    sb = c.angle(a)
    sc = a.angle(b)
    s = 0.5 * (sa + sb + sc)
    if s >= 3e-4:
        s2 = s * s
        dmin = s - max(sa, max(sb, sc))
        if dmin < 1e-2 * s * s2 * s2:
            area = girard_area(a, b, c)
            if dmin < 2 * (0.1 * area):
                return area

    return 4 * math.atan(math.sqrt(
        max(0.0,
            math.tan(0.5 * s) *
            math.tan(0.5 * (s - sa)) *
            math.tan(0.5 * (s - sb)) *
            math.tan(0.5 * (s - sc)))
    ))


def simple_ccw(a, b, c):
    """Simple Counterclockwise test.

    Return true if the points A, B, C are strictly counterclockwise.  Return
    false if the points are clockwise or collinear (i.e. if they are all
    contained on some great circle).

    Due to numerical errors, situations may arise that are mathematically
    impossible, e.g. ABC may be considered strictly CCW while BCA is not.
    However, the implementation guarantees the following:

      If simple_ccw(a,b,c), then !simple_ccw(c,b,a) for all a,b,c.

    see :cpp:func:`S2::SimpleCCW`
    """
    return c.cross_prod(a).dot_prod(b) > 0


class Interval(object):
    """Interval interface"""
    def __init__(self, lo, hi):
        # self.__bounds = [args[0], args[1]]
        self.__bounds = (lo, hi)

    def __repr__(self):
        return '{}: ({}, {})'.format(
            self.__class__.__name__, self.__bounds[0], self.__bounds[1])

    def lo(self):
        return self.__bounds[0]

    def hi(self):
        return self.__bounds[1]

    def bound(self, i):
        return self.__bounds[i]

    def bounds(self):
        return self.__bounds

    @classmethod
    def empty(cls):
        return cls()


class LineInterval(Interval):
    """Line Interval in R1

    see :cpp:class:`R1Interval`
    """

    def __init__(self, lo=1, hi=0):
        super(LineInterval, self).__init__(lo, hi)

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                ((self.lo() == other.lo() and self.hi() == other.hi()) or
                (self.is_empty() and other.is_empty())))

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__bounds)

    @classmethod
    def from_point_pair(cls, a, b):
        if a <= b:
            return cls(a, b)
        else:
            return cls(b, a)

    def contains(self, other):
        if isinstance(other, self.__class__):
            if other.is_empty():
                return True
            return other.lo() >= self.lo() and other.hi() <= self.hi()
        else:
            return other >= self.lo() and other <= self.hi()

    def interior_contains(self, other):
        if isinstance(other, self.__class__):
            if other.is_empty():
                return True
            return other.lo() > self.lo() and other.hi() < self.hi()
        else:
            return other > self.lo() and other < self.hi()

    def intersects(self, other):
        if self.lo() <= other.lo():
            return other.lo() <= self.hi() and other.lo() <= other.hi()
        else:
            return self.lo() <= other.hi() and self.lo() <= self.hi()

    def interior_intersects(self, other):
        return (other.lo() < self.hi() and self.lo() < other.hi() and
                self.lo() < self.hi() and other.lo() <= other.hi())

    def union(self, other):
        if self.is_empty():
            return other
        if other.is_empty():
            return self
        return self.__class__(min(self.lo(), other.lo()),
                              max(self.hi(), other.hi()))

    def intersection(self, other):
        return self.__class__(max(self.lo(), other.lo()),
                              min(self.hi(), other.hi()))

    def expanded(self, radius):
        assert radius >= 0
        if self.is_empty():
            return self
        return self.__class__(self.lo() - radius, self.hi() + radius)

    def get_center(self):
        return 0.5 * (self.lo() + self.hi())

    def get_length(self):
        return self.hi() - self.lo()

    def is_empty(self):
        return self.lo() > self.hi()

    def approx_equals(self, other, max_error=1e-15):
        if self.is_empty():
            return other.get_length() <= max_error
        if other.is_empty():
            return self.get_length() <= max_error
        return (math.fabs(other.lo() - self.lo()) +
                math.fabs(other.hi() - self.hi()) <= max_error)


class SphereInterval(Interval):
    """Interval in S1

    see :cpp:class:`S1Interval`
    """
    def __init__(self, lo=math.pi, hi=-math.pi, args_checked=False):
        if args_checked:
            super(SphereInterval, self).__init__(lo, hi)
        else:
            clamped_lo, clamped_hi = lo, hi
            if lo == -math.pi and hi != math.pi:
                clamped_lo = math.pi
            if hi == -math.pi and lo != math.pi:
                clamped_hi = math.pi

            super(SphereInterval, self).__init__(clamped_lo, clamped_hi)
        assert self.is_valid()

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.lo() == other.lo() and self.hi() == other.hi())

    def __ne__(self, other):
        return not self.__eq__(other)

    @classmethod
    def from_point_pair(cls, a, b):
        assert math.fabs(a) <= math.pi
        assert math.fabs(b) <= math.pi
        if a == -math.pi:
            a = math.pi
        if b == -math.pi:
            b = math.pi
        if cls.positive_distance(a, b) <= math.pi:
            return cls(a, b, args_checked=True)
        else:
            return cls(b, a, args_checked=True)

    @classmethod
    def positive_distance(cls, a, b):
        d = b - a
        if d >= 0:
            return d
        return (b + math.pi) - (a - math.pi)

    @classmethod
    def full(cls):
        return cls(-math.pi, math.pi, args_checked=True)

    def is_full(self):
        return (self.hi() - self.lo()) == (2 * math.pi)

    def is_valid(self):
        return (math.fabs(self.lo()) <= math.pi and
                math.fabs(self.hi()) <= math.pi and
                not (self.lo() == -math.pi and self.hi() != math.pi) and
                not (self.hi() == -math.pi and self.lo() != math.pi))

    def is_inverted(self):
        return self.lo() > self.hi()

    def is_empty(self):
        return self.lo() - self.hi() == 2 * math.pi

    def get_center(self):
        center = 0.5 * (self.lo() + self.hi())
        if not self.is_inverted():
            return center
        if center <= 0:
            return center + math.pi
        else:
            return center - math.pi

    def get_length(self):
        length = self.hi() - self.lo()
        if length >= 0:
            return length
        length += (2 * math.pi)
        if length > 0:
            return length
        else:
            return -1

    def complement(self):
        """Return the complement of the interior of the interval.

        An interval and its complement have the same boundary but do not share
        any interior values. The complement operator is not a bijection, since
        the complement of a singleton interval (containing a single value) is
        the same as the complement of an empty interval.
        """
        if self.lo() == self.hi():
            return self.__class__.full()
        return self.__class__(self.hi(), self.lo())

    def approx_equals(self, other, max_error=1e-15):
        if self.is_empty():
            return other.get_length() <= max_error
        if other.is_empty():
            return self.get_length() <= max_error
        return ((math.fabs(drem(other.lo() - self.lo(), 2 * math.pi)) +
                 math.fabs(drem(other.hi() - self.hi(), 2 * math.pi))) <=
                max_error)

    def fast_contains(self, other):
        if self.is_inverted():
            return ((other >= self.lo() or other <= self.hi()) and
                    not self.is_empty())
        else:
            return other >= self.lo() and other <= self.hi()

    def contains(self, other):
        if isinstance(other, self.__class__):
            if self.is_inverted():
                if other.is_inverted():
                    return other.lo() >= self.lo() and other.hi() <= self.hi()
                return (
                    (other.lo() >= self.lo() or other.hi() <= self.hi()) and
                    not self.is_empty()
                )
            else:
                if other.is_inverted():
                    return self.is_full() or other.is_empty()
                return other.lo() >= self.lo() and other.hi() <= self.hi()
        else:
            assert math.fabs(other) <= math.pi
            if other == -math.pi:
                other = math.pi
            return self.fast_contains(other)

    def interior_contains(self, other):
        if isinstance(other, self.__class__):
            if self.is_inverted():
                if not other.is_inverted():
                    return other.lo() > self.lo() or other.hi() < self.hi()
                return ((other.lo() > self.lo() and other.hi() < self.hi()) or
                        other.is_empty())
            else:
                if other.is_inverted():
                    return self.is_full() or other.is_empty()
                return ((other.lo() > self.lo() and other.hi() < self.hi()) or
                        self.is_full())
        else:
            assert math.fabs(other) <= math.pi
            if other == -math.pi:
                other = math.pi

            if self.is_inverted():
                return other > self.lo() or other < self.hi()
            else:
                return ((other > self.lo() and other < self.hi()) or
                        self.is_full())

    def intersects(self, other):
        if self.is_empty() or other.is_empty():
            return False
        if self.is_inverted():
            return (other.is_inverted() or other.lo() <= self.hi() or
                    other.hi() >= self.lo())
        else:
            if other.is_inverted():
                return other.lo() <= self.hi() or other.hi() >= self.lo()
            return other.lo() <= self.hi() and other.hi() >= self.lo()

    def interior_intersects(self, other):
        if self.is_empty() or other.is_empty() or self.lo() == self.hi():
            return False
        if self.is_inverted():
            return (other.is_inverted() or other.lo() < self.hi() or
                    other.hi() > self.lo())
        else:
            if other.is_inverted():
                return other.lo() < self.hi() or other.hi() > self.lo()
            return ((other.lo() < self.hi() and other.hi() > self.lo()) or
                    self.is_full())

    def union(self, other):
        if other.is_empty():
            return self

        if self.fast_contains(other.lo()):
            if self.fast_contains(other.hi()):
                if self.contains(other):
                    return self
                return self.__class__.full()
            return self.__class__(self.lo(), other.hi(), args_checked=True)

        if self.fast_contains(other.hi()):
            return self.__class__(other.lo(), self.hi(), args_checked=True)

        if self.is_empty() or other.fast_contains(self.lo()):
            return other

        dlo = self.__class__.positive_distance(other.hi(), self.lo())
        dhi = self.__class__.positive_distance(self.hi(), other.lo())
        if dlo < dhi:
            return self.__class__(other.lo(), self.hi(), args_checked=True)
        else:
            return self.__class__(self.lo(), other.hi(), args_checked=True)

    def intersection(self, other):
        if other.is_empty():
            return self.__class__.empty()
        if self.fast_contains(other.lo()):
            if self.fast_contains(other.hi()):
                if other.get_length() < self.get_length():
                    return other
                return self
            return self.__class__(other.lo(), self.hi(), args_checked=True)

        if self.fast_contains(other.hi()):
            return self.__class__(self.lo(), other.hi(), args_checked=True)

        if other.fast_contains(self.lo()):
            return self
        assert not self.intersects(other)
        return self.__class__.empty()

    def expanded(self, radius):
        assert radius >= 0
        if self.is_empty():
            return self

        if self.get_length() + 2 * radius >= 2 * math.pi - 1e-15:
            return self.__class__.full()

        lo = drem(self.lo() - radius, 2 * math.pi)
        hi = drem(self.hi() + radius, 2 * math.pi)
        if lo <= -math.pi:
            lo = math.pi
        return self.__class__(lo, hi)

    def get_complement_center(self):
        if self.lo() != self.hi():
            return self.complement().get_center()
        else:
            if self.hi() <= 0:
                return self.hi() + math.pi
            else:
                return self.hi() - math.pi

    def get_directed_hausdorff_distance(self, other):
        if other.contains(self):
            return 0.0
        if other.is_empty():
            return math.pi

        other_complement_center = other.get_complement_center()
        if self.contains(other_complement_center):
            return self.__class__.positive_distance(other.hi(),
                                                    other_complement_center)
        else:
            if self.__class__(other.hi(), other_complement_center) \
                    .contains(self.hi()):
                hi_hi = self.__class__.positive_distance(other.hi(), self.hi())
            else:
                hi_hi = 0

            if self.__class__(other_complement_center, other.lo()) \
                    .contains(self.lo()):
                lo_lo = self.__class__.positive_distance(self.lo(), other.lo())
            else:
                lo_lo = 0

            assert hi_hi > 0 or lo_lo > 0
            return max(hi_hi, lo_lo)


class Cell(object):
    """Cell

    see :cpp:class:`S2Cell`
    """

    def __init__(self, cell_id=None):
        self.__uv = [[None, None], [None, None]]
        if cell_id is not None:
            self.__cell_id = cell_id
            face, i, j, orientation = cell_id.to_face_ij_orientation()
            ij = (i, j)
            self.__face = face
            self.__orientation = orientation
            self.__level = cell_id.level()

            cell_size = cell_id.get_size_ij()
            for ij_, uv_ in zip(ij, self.__uv):
                ij_lo = ij_ & -cell_size
                ij_hi = ij_lo + cell_size
                uv_[0] = CellId.st_to_uv((1.0 / CellId.MAX_SIZE) * ij_lo)
                uv_[1] = CellId.st_to_uv((1.0 / CellId.MAX_SIZE) * ij_hi)

    @classmethod
    def from_lat_lng(cls, lat_lng):
        return cls(CellId.from_lat_lng(lat_lng))

    @classmethod
    def from_point(cls, point):
        return cls(CellId.from_point(point))

    def __repr__(self):
        return '{}: face {}, level {}, orientation {}, id {}'.format(
            self.__class__.__name__, self.__face, self.__level,
            self.orientation(), self.__cell_id.id())

    @classmethod
    def from_face_pos_level(cls, face, pos, level):
        return cls(CellId.from_face_pos_level(face, pos, level))

    def id(self):
        return self.__cell_id

    def face(self):
        return self.__face

    def level(self):
        return self.__level

    def orientation(self):
        return self.__orientation

    def is_leaf(self):
        return self.__level == CellId.MAX_LEVEL

    def get_edge(self, k):
        """the k-th edge

        Return the inward-facing normal of the great circle passing through
        the edge from vertex k to vertex k+1 (mod 4).  The normals returned
        by GetEdgeRaw are not necessarily unit length.
        """
        return self.get_edge_raw(k).normalize()

    def get_edge_raw(self, k):
        if k == 0:
            return get_v_norm(self.__face, self.__uv[1][0])  # South
        elif k == 1:
            return get_u_norm(self.__face, self.__uv[0][1])  # East
        elif k == 2:
            return -get_v_norm(self.__face, self.__uv[1][1])  # North
        else:
            return -get_u_norm(self.__face, self.__uv[0][0])  # West

    def get_vertex(self, k):
        """Return the k-th vertex of the cell (k = 0,1,2,3).

        Vertices are returned in CCW order.
        The points returned by GetVertexRaw are not necessarily unit length.
        """
        return self.get_vertex_raw(k).normalize()

    def get_vertex_raw(self, k):
        return face_uv_to_xyz(
            self.__face,
            self.__uv[0][(k >> 1) ^ (k & 1)], self.__uv[1][k >> 1],
        )

    def exact_area(self):
        """cell area in steradians accurate to 6 digits but slow to compute

        Return the area of this cell as accurately as possible.  This method is
        more expensive but it is accurate to 6 digits of precision even for
        leaf cells (whose area is approximately 1e-18).
        """
        v0 = self.get_vertex(0)
        v1 = self.get_vertex(1)
        v2 = self.get_vertex(2)
        v3 = self.get_vertex(3)
        return area(v0, v1, v2) + area(v0, v2, v3)

    def average_area(self):
        """cell area in steradians"""
        return AVG_AREA.get_value(self.__level)

    def approx_area(self):
        """approximate cell area in steradians accurate to within 3%

        For cells at level 5 or higher (cells with edge length 350km or
        smaller), it is accurate to within 0.1%.
        """
        if self.__level < 2:
            return self.average_area()

        flat_area = (0.5 * (self.get_vertex(2) - self.get_vertex(0))
                     .cross_prod(self.get_vertex(3) - self.get_vertex(1))
                     .norm())

        return (flat_area * 2 /
                (1 + math.sqrt(1 - min((1.0 / math.pi) * flat_area, 1.0))))

    def subdivide(self):
        uv_mid = self.__cell_id.get_center_uv()

        for pos, cell_id in enumerate(self.__cell_id.children()):
            child = Cell()
            child.__face = self.__face
            child.__level = self.__level + 1
            child.__orientation = self.__orientation ^ POS_TO_ORIENTATION[pos]
            child.__cell_id = cell_id

            # We want to split the cell in half in "u" and "v".  To decide
            # which side to set equal to the midpoint value, we look at
            # cell's (i,j) position within its parent.  The index for "i"
            # is in bit 1 of ij.
            ij = POS_TO_IJ[self.__orientation][pos]
            i = ij >> 1
            j = ij & 1
            child.__uv[0][i] = self.__uv[0][i]
            child.__uv[0][1 - i] = uv_mid[0]
            child.__uv[1][j] = self.__uv[1][j]
            child.__uv[1][1 - j] = uv_mid[1]
            yield child

    def get_center(self):
        return self.get_center_raw().normalize()

    def get_center_raw(self):
        return self.__cell_id.to_point_raw()

    def contains(self, other):
        if isinstance(other, self.__class__):
            return self.__cell_id.contains(other.__cell_id)
        elif isinstance(other, Point):
            valid, u, v = face_xyz_to_uv(self.__face, other)
            if not valid:
                return False
            return (u >= self.__uv[0][0] and u <= self.__uv[0][1] and
                    v >= self.__uv[1][0] and v <= self.__uv[1][1])

    def may_intersect(self, cell):
        return self.__cell_id.intersects(cell.__cell_id)

    def get_latitude(self, i, j):
        p = face_uv_to_xyz(self.__face, self.__uv[0][i], self.__uv[1][j])
        return LatLng.latitude(p).radians

    def get_longitude(self, i, j):
        p = face_uv_to_xyz(self.__face, self.__uv[0][i], self.__uv[1][j])
        return LatLng.longitude(p).radians

    def get_cap_bound(self):
        u = 0.5 * (self.__uv[0][0] + self.__uv[0][1])
        v = 0.5 * (self.__uv[1][0] + self.__uv[1][1])
        cap = Cap.from_axis_height(
            face_uv_to_xyz(self.__face, u, v).normalize(), 0)
        for k in range(4):
            cap.add_point(self.get_vertex(k))
        return cap

    def get_rect_bound(self):
        if self.__level > 0:
            u = self.__uv[0][0] + self.__uv[0][1]
            v = self.__uv[1][0] + self.__uv[1][1]
            if get_u_axis(self.__face)[2] == 0:
                i = int(u < 0)
            else:
                i = int(u > 0)

            if get_v_axis(self.__face)[2] == 0:
                j = int(v < 0)
            else:
                j = int(v > 0)

            max_error = 1.0 / (1 << 51)
            lat = LineInterval.from_point_pair(self.get_latitude(i, j),
                                               self.get_latitude(1 - i, 1 - j))
            lat = lat.expanded(max_error).intersection(LatLngRect.full_lat())

            if lat.lo() == (-math.pi / 2.0) or lat.hi() == (math.pi / 2.0):
                return LatLngRect(lat, SphereInterval.full())

            lng = SphereInterval.from_point_pair(self.get_longitude(i, 1 - j),
                                                 self.get_longitude(1 - i, j))
            return LatLngRect(lat, lng.expanded(max_error))

        pole_min_lat = math.asin(math.sqrt(1.0 / 3.0))

        if self.__face == 0:
            return LatLngRect(
                LineInterval(-math.pi / 4.0, math.pi / 4.0),
                SphereInterval(-math.pi / 4.0, math.pi / 4.0))
        elif self.__face == 1:
            return LatLngRect(
                LineInterval(-math.pi / 4.0, math.pi / 4.0),
                SphereInterval(math.pi / 4.0, 3.0 * math.pi / 4.0))
        elif self.__face == 2:
            return LatLngRect(
                LineInterval(pole_min_lat, math.pi / 2.0),
                SphereInterval(-math.pi, math.pi))
        elif self.__face == 3:
            return LatLngRect(
                LineInterval(-math.pi / 4.0, math.pi / 4.0),
                SphereInterval(3.0 * math.pi / 4.0, -3.0 * math.pi / 4.0))
        elif self.__face == 4:
            return LatLngRect(
                LineInterval(-math.pi / 4.0, math.pi / 4.0),
                SphereInterval(-3.0 * math.pi / 4.0, -math.pi / 4.0))
        else:
            return LatLngRect(
                LineInterval(-math.pi / 2.0, -pole_min_lat),
                SphereInterval(-math.pi, math.pi))


class CellUnion(object):
    """Cell Union

    see :cpp:class:`S2CellUnion`
    """

    def __init__(self, cell_ids=None, raw=True):
        if cell_ids is None:
            self.__cell_ids = []
        else:
            self.__cell_ids = [cell_id
                               if isinstance(cell_id, CellId)
                               else CellId(cell_id)
                               for cell_id in cell_ids]
            if raw:
                self.normalize()

    def __eq__(self, other):
        return (isinstance(other, self.__class__) and
                self.__cell_ids == other.__cell_ids)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.__cell_ids)

    def __repr__(self):
        return '{}: {}'.format(self.__class__.__name__, self.__cell_ids)

    @classmethod
    def get_union(cls, x, y):
        return cls(x.__cell_ids + y.__cell_ids)

    @classmethod
    def get_intersection(cls, *args):
        if len(args) == 2 and isinstance(args[0], cls) \
                and isinstance(args[1], CellId):
            cell_union, cell_id = args
            if cell_union.contains(cell_id):
                return cls([cell_id])
            else:
                index = bisect.bisect_left(cell_union.__cell_ids,
                                           cell_id.range_min())
                idmax = cell_id.range_max()

                intersected_cell_ids = []
                while index != len(cell_union.__cell_ids) \
                        and cell_union.__cell_ids[index] <= idmax:
                    intersected_cell_ids.append(cell_union.__cell_ids[index])
                    index += 1
                return cls(intersected_cell_ids)
        elif len(args) == 2 and isinstance(args[0], cls) \
                and isinstance(args[1], cls):
            x, y = args
            i, j = 0, 0
            cell_ids = []
            while i < x.num_cells() and j < y.num_cells():
                imin = x.__cell_ids[i].range_min()
                jmin = y.__cell_ids[j].range_min()
                if imin > jmin:
                    if x.__cell_ids[i] <= y.__cell_ids[j].range_max():
                        cell_ids.append(x.__cell_ids[i])
                        i += 1
                    else:
                        j = bisect.bisect_left(y.__cell_ids, imin, lo=j + 1)
                        if x.__cell_ids[i] <= y.__cell_ids[j - 1].range_max():
                            j -= 1
                elif jmin > imin:
                    if y.__cell_ids[j] <= x.__cell_ids[i].range_max():
                        cell_ids.append(y.__cell_ids[j])
                        j += 1
                    else:
                        i = bisect.bisect_left(x.__cell_ids, jmin, lo=i + 1)
                        if y.__cell_ids[j] <= x.__cell_ids[i - 1].range_max():
                            i -= 1
                else:
                    if x.__cell_ids[i] < y.__cell_ids[j]:
                        cell_ids.append(x.__cell_ids[i])
                        i += 1
                    else:
                        cell_ids.append(y.__cell_ids[j])
                        j += 1

            cell_union = cls(cell_ids)
            assert all(cell_union.__cell_ids[i] <= cell_union.__cell_ids[i + 1]
                       for i in range(cell_union.num_cells() - 1))
            assert not cell_union.normalize()

            return cell_union
        else:
            raise NotImplementedError()

    def expand(self, *args):
        if len(args) == 1 and isinstance(args[0], int):
            level = args[0]
            output = []
            level_lsb = CellId.lsb_for_level(level)
            i = self.num_cells() - 1
            while i >= 0:
                cell_id = self.__cell_ids[i]
                if cell_id.lsb() < level_lsb:
                    cell_id = cell_id.parent(level)
                    while i > 0 and cell_id.contains(self.__cell_ids[i - 1]):
                        i -= 1
                output.append(cell_id)
                cell_id.append_all_neighbors(level, output)
                i -= 1
            self.__cell_ids = output
        elif len(args) == 2 and isinstance(args[0], Angle) \
                and isinstance(args[1], int):
            min_radius, max_level_diff = args
            min_level = CellId.MAX_LEVEL
            for cell_id in self.__cell_ids:
                min_level = min(min_level, cell_id.level())

            radius_level = CellId.min_width().get_max_level(min_radius.radians)
            if radius_level == 0 \
                    and min_radius.radians > CellId.min_width().get_value(0):
                self.expand(0)
            self.expand(min(min_level + max_level_diff, radius_level))
        else:
            raise NotImplementedError()

    @classmethod
    def get_difference(cls, x, y):
        cell_ids = []
        for cell_id in x.__cell_ids:
            cls.__get_difference(cell_id, y, cell_ids)

        cell_union = cls(cell_ids)
        assert all(cell_union.__cell_ids[i] <= cell_union.__cell_ids[i + 1]
                   for i in range(cell_union.num_cells() - 1))
        assert not cell_union.normalize()
        return cell_union

    @classmethod
    def __get_difference(cls, cell_id, y, cell_ids):
        if not y.intersects(cell_id):
            cell_ids.append(cell_id)
        elif not y.contains(cell_id):
            for child in cell_id.children():
                cls.__get_difference(child, y, cell_ids)

    def num_cells(self):
        return len(self.__cell_ids)

    def cell_id(self, i):
        return self.__cell_ids[i]

    def cell_ids(self):
        return self.__cell_ids

    def normalize(self):
        self.__cell_ids.sort()
        output = []
        for cell_id in self.__cell_ids:

            if output and output[-1].contains(cell_id):
                continue

            while output and cell_id.contains(output[-1]):
                output.pop()

            while len(output) >= 3:
                if (output[-3].id() ^ output[-2].id() ^ output[-1].id()) \
                        != cell_id.id():
                    break

                mask = cell_id.lsb() << 1
                mask = ~(mask + (mask << 1))
                id_masked = (cell_id.id() & mask)
                if (output[-3].id() & mask) != id_masked \
                        or (output[-2].id() & mask) != id_masked \
                        or (output[-1].id() & mask) != id_masked \
                        or cell_id.is_face():
                    break

                output.pop()
                output.pop()
                output.pop()
                cell_id = cell_id.parent()

            output.append(cell_id)

        if len(output) < self.num_cells():
            self.__cell_ids = output
            return True
        return False

    def denormalize(self, min_level, level_mod):
        assert min_level >= 0
        assert min_level <= CellId.MAX_LEVEL
        assert level_mod >= 1
        assert level_mod <= 3

        cell_ids = []
        for cell_id in self.__cell_ids:
            level = cell_id.level()
            new_level = max(min_level, level)
            if level_mod > 1:
                new_level += ((CellId.MAX_LEVEL - (new_level - min_level)) %
                              level_mod)
                new_level = min(CellId.MAX_LEVEL, new_level)
            if new_level == level:
                cell_ids.append(cell_id)
            else:
                # end = cell_id.child_end(new_level)
                for child in cell_id.children(new_level):
                    cell_ids.append(child)
        return cell_ids

    def contains(self, *args):
        if len(args) == 1 and isinstance(args[0], Cell):
            return self.contains(args[0].id())
        elif len(args) == 1 and isinstance(args[0], CellId):
            cell_id = args[0]
            index = bisect.bisect_left(self.__cell_ids, cell_id)
            if index < len(self.__cell_ids) \
                    and self.__cell_ids[index].range_min() <= cell_id:
                return True
            return (index != 0 and
                    self.__cell_ids[index - 1].range_max() >= cell_id)
        elif len(args) == 1 and isinstance(args[0], Point):
            return self.contains(CellId.from_point(args[0]))
        elif len(args) == 1 and isinstance(args[0], self.__class__):
            cell_union = args[0]
            for i in range(cell_union.num_cells()):
                if not self.contains(cell_union.cell_id(i)):
                    return False
            return True
        else:
            raise NotImplementedError()

    def intersects(self, *args):
        if len(args) == 1 and isinstance(args[0], CellId):
            cell_id = args[0]
            index = bisect.bisect_left(self.__cell_ids, cell_id)
            if index != len(self.__cell_ids) and \
               self.__cell_ids[index].range_min() <= cell_id.range_max():
                return True
            return (
                index != 0 and
                self.__cell_ids[index - 1].range_max() >= cell_id.range_min()
            )
        elif len(args) == 1 and isinstance(args[0], CellUnion):
            cell_union = args[0]
            for cell_id in cell_union.__cell_ids:
                if self.intersects(cell_id):
                    return True
            return False
        else:
            raise NotImplementedError()

    def get_rect_bound(self):
        """rectangular bound"""
        bound = LatLngRect.empty()
        for cell_id in self.__cell_ids:
            bound = bound.union(Cell(cell_id).get_rect_bound())
        return bound


FACE_CELLS = (Cell.from_face_pos_level(0, 0, 0),
              Cell.from_face_pos_level(1, 0, 0),
              Cell.from_face_pos_level(2, 0, 0),
              Cell.from_face_pos_level(3, 0, 0),
              Cell.from_face_pos_level(4, 0, 0),
              Cell.from_face_pos_level(5, 0, 0))


class RegionCoverer(object):
    """Region Coverer

    see :cpp:class:`S2RegionCoverer`
    """

    class Candidate(object):
        @property
        def num_children(self):
            return len(self.children)

        def __lt__(self, other):
            if not hasattr(self, 'cell') or \
               not hasattr(other, 'cell'):
                raise NotImplementedError()
            return self.cell.id() < other.cell.id()

    def __init__(self):
        self.__min_level = 0
        self.__max_level = CellId.MAX_LEVEL
        self.__level_mod = 1
        self.__max_cells = 8
        self.__region = None
        self.__result = []
        self.__pq = []

    @property
    def min_level(self):
        return self.__min_level

    @min_level.setter
    def min_level(self, value):
        assert value >= 0
        assert value <= CellId.MAX_LEVEL
        self.__min_level = max(0, min(CellId.MAX_LEVEL, value))

    @property
    def max_level(self):
        return self.__max_level

    @max_level.setter
    def max_level(self, value):
        assert value >= 0
        assert value <= CellId.MAX_LEVEL
        self.__max_level = max(0, min(CellId.MAX_LEVEL, value))

    @property
    def level_mod(self):
        return self.__level_mod

    @level_mod.setter
    def level_mod(self, value):
        assert value >= 1
        assert value <= 3
        self.__level_mod = max(1, min(3, value))

    @property
    def max_cells(self):
        return self.__max_cells

    @max_cells.setter
    def max_cells(self, value):
        self.__max_cells = value

    def get_covering(self, region):
        self.__result = []
        tmp_union = self.__get_cell_union(region)
        return tmp_union.denormalize(self.__min_level, self.__level_mod)

    def get_interior_covering(self, region):
        self.__result = []
        tmp_union = self.__get_interior_cell_union(region)
        return tmp_union.denormalize(self.__min_level, self.__level_mod)

    def __new_candidate(self, cell):
        if not self.__region.may_intersect(cell):
            return None
        is_terminal = False
        if cell.level() >= self.__min_level:
            if self.__interior_covering:
                if self.__region.contains(cell):
                    is_terminal = True
                elif cell.level() + self.__level_mod > self.__max_level:
                    return None
            else:
                if cell.level() + self.__level_mod > self.__max_level \
                        or self.__region.contains(cell):
                    is_terminal = True

        candidate = self.__class__.Candidate()
        candidate.cell = cell
        candidate.is_terminal = is_terminal
        candidate.children = []
        return candidate

    def __max_children_shift(self):
        return 2 * self.__level_mod

    def __expand_children(self, candidate, cell, num_levels):
        num_levels -= 1
        num_terminals = 0
        for child_cell in cell.subdivide():
            if num_levels > 0:
                if self.__region.may_intersect(child_cell):
                    num_terminals += self.__expand_children(
                        candidate, child_cell, num_levels)
                continue
            child = self.__new_candidate(child_cell)
            if child is not None:
                candidate.children.append(child)
                if child.is_terminal:
                    num_terminals += 1

        return num_terminals

    def __add_candidate(self, candidate):
        if candidate is None:
            return

        if candidate.is_terminal:
            self.__result.append(candidate.cell.id())
            return

        assert candidate.num_children == 0

        num_levels = self.__level_mod
        if candidate.cell.level() < self.__min_level:
            num_levels = 1
        num_terminals = self.__expand_children(candidate,
                                               candidate.cell,
                                               num_levels)

        if candidate.num_children == 0:
            """ Not needed due to GC """
        elif not self.__interior_covering \
                and num_terminals == 1 << self.__max_children_shift() \
                and candidate.cell.level() >= self.__min_level:
            candidate.is_terminal = True
            self.__add_candidate(candidate)
        else:
            priority = (
                (
                    (
                        (candidate.cell.level() <<
                         self.__max_children_shift()
                         ) + candidate.num_children
                    ) << self.__max_children_shift()
                ) + num_terminals
            )
            heapq.heappush(self.__pq, (priority, candidate))

    def __get_initial_candidates(self):
        if self.__max_cells >= 4:
            cap = self.__region.get_cap_bound()
            level = min(CellId.min_width().get_max_level(
                        2 * cap.angle().radians),
                        min(self.__max_level, CellId.MAX_LEVEL - 1))

            if self.__level_mod > 1 and level > self.__min_level:
                level -= (level - self.__min_level) % self.__level_mod

            if level > 0:
                cell_id = CellId.from_point(cap.axis())
                vertex_neighbors = cell_id.get_vertex_neighbors(level)
                for neighbor in vertex_neighbors:
                    self.__add_candidate(self.__new_candidate(Cell(neighbor)))
                return

        for face in range(6):
            self.__add_candidate(self.__new_candidate(FACE_CELLS[face]))

    def __get_covering(self, region):
        assert len(self.__pq) == 0
        assert len(self.__result) == 0
        self.__region = region

        self.__get_initial_candidates()
        while (len(self.__pq) > 0 and
               (not self.__interior_covering or
                len(self.__result) < self.__max_cells)
               ):
            candidate = heapq.heappop(self.__pq)[1]

            if self.__interior_covering:
                result_size = 0
            else:
                result_size = len(self.__pq)
            if candidate.cell.level() < self.__min_level \
                or candidate.num_children == 1 \
                or len(self.__result) + result_size + candidate.num_children \
                    <= self.__max_cells:
                for child in candidate.children:
                    self.__add_candidate(child)
            elif self.__interior_covering:
                """ Do nothing here """
            else:
                candidate.is_terminal = True
                self.__add_candidate(candidate)

        self.__pq = []
        self.__region = None

    def __get_cell_union(self, region):
        self.__interior_covering = False
        self.__get_covering(region)
        return CellUnion(self.__result)

    def __get_interior_cell_union(self, region):
        self.__interior_covering = True
        self.__get_covering(region)
        return CellUnion(self.__result)

    @classmethod
    def flood_fill(cls, region, start):
        all_nbrs = set()
        frontier = []
        all_nbrs.add(start)
        frontier.append(start)
        while len(frontier) != 0:
            cell_id = frontier.pop()
            if not region.may_intersect(Cell(cell_id)):
                continue
            yield cell_id

            neighbors = cell_id.get_edge_neighbors()
            for nbr in neighbors:
                if nbr not in all_nbrs:
                    all_nbrs.add(nbr)
                    frontier.append(nbr)

    @classmethod
    def get_simple_covering(cls, region, start, level):
        return cls.flood_fill(region, CellId.from_point(start).parent(level))
