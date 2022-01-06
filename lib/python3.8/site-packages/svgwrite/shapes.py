#!/usr/bin/env python
#coding:utf-8
# Author:  mozman <me@mozman.at>
# Purpose: svg shapes
# Created: 08.09.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License

from svgwrite.base import BaseElement
from svgwrite.mixins import Presentation, Markers, Transform


class Line(BaseElement, Transform, Presentation, Markers):
    """ The **line** element defines a line segment that starts at one point
    and ends at another.
    """
    elementname = 'line'

    def __init__(self, start=(0, 0), end=(0, 0), **extra):
        """
        :param 2-tuple start: start point (**x1**, **y1**)
        :param 2-tuple end: end point (**x2**, **y2**)
        :param extra: additional SVG attributes as keyword-arguments

        """
        super(Line, self).__init__(**extra)
        x1, y1 = start
        x2, y2 = end
        self['x1'] = x1
        self['y1'] = y1
        self['x2'] = x2
        self['y2'] = y2


class Rect(BaseElement, Transform, Presentation):
    """ The **rect** element defines a rectangle which is axis-aligned with the current
    user coordinate system. Rounded rectangles can be achieved by setting appropriate
    values for attributes **rx** and **ry**.
    """
    elementname = 'rect'

    def __init__(self, insert=(0, 0), size=(1, 1), rx=None, ry=None, **extra):
        """
        :param 2-tuple insert: insert point (**x**, **y**), left-upper point
        :param 2-tuple size: (**width**, **height**)
        :param <length> rx: corner x-radius
        :param <length> ry: corner y-radius
        :param extra: additional SVG attributes as keyword-arguments

        """
        super(Rect, self).__init__(**extra)
        x, y = insert
        width, height = size
        self['x'] = x
        self['y'] = y
        self['width'] = width
        self['height'] = height
        if rx is not None:
            self['rx'] = rx
        if ry is not None:
            self['ry'] = ry


class Circle(BaseElement, Transform, Presentation):
    """ The **circle** element defines a circle based on a center point and a radius.
    """
    elementname = 'circle'

    def __init__(self, center=(0, 0), r=1, **extra):
        """
        :param 2-tuple center: circle center point (**cx**, **cy**)
        :param length r: circle-radius **r**
        :param extra: additional SVG attributes as keyword-arguments

        """
        super(Circle, self).__init__(**extra)
        cx, cy = center
        self['cx'] = cx
        self['cy'] = cy
        self['r'] = r


class Ellipse(BaseElement, Transform, Presentation):
    """ The **ellipse** element defines an ellipse which is axis-aligned with the
    current user coordinate system based on a center point and two radii.
    """
    elementname = 'ellipse'

    def __init__(self, center=(0, 0), r=(1, 1), **extra):
        """
        :param 2-tuple center: ellipse center point (**cx**, **cy**)
        :param 2-tuple r: ellipse radii (**rx**, **ry**)
        :param extra: additional SVG attributes as keyword-arguments

        """
        super(Ellipse, self).__init__(**extra)
        cx, cy = center
        rx, ry = r
        self['cx'] = cx
        self['cy'] = cy
        self['rx'] = rx
        self['ry'] = ry


class Polyline(BaseElement, Transform, Presentation, Markers):
    """ The **polyline** element defines a set of connected straight line
    segments. Typically, **polyline** elements define open shapes.
    """
    elementname = 'polyline'

    def __init__(self, points=[], **extra):
        """
        :param `iterable` points: `iterable` of points (points are `2-tuples`)
        :param extra: additional SVG attributes as keyword-arguments

        """
        super(Polyline, self).__init__(**extra)
        self.points = list(points)
        if self.debug:
            for point in self.points:
                x, y = point
                self.validator.check_svg_type(x, 'number')
                self.validator.check_svg_type(y, 'number')

    def get_xml(self):
        self.attribs['points'] = self.points_to_string(self.points)
        return super(Polyline, self).get_xml()

    def points_to_string(self, points):
        """
        Convert a `list` of points `2-tuples` to a `string` ``'p1x,p1y p2x,p2y ...'``.

        """
        strings = []
        for point in points:
            if len(point) != 2:
                raise TypeError('got %s values, but expected 2 values.' % len(point))
            x, y = point
            if self.debug:
                self.validator.check_svg_type(x, 'coordinate')
                self.validator.check_svg_type(y, 'coordinate')
            if self.profile == 'tiny':
                if isinstance(x, float):
                    x = round(x, 4)
                if isinstance(y, float):
                    y = round(y, 4)
            point = "%s,%s" % (x, y)
            strings.append(point)
        return ' '.join(strings)


class Polygon(Polyline):
    """ The **polygon** element defines a closed shape consisting of a set of
    connected straight line segments.

    Same as :class:`~svgwrite.shapes.Polyline` but closed.
    """
    elementname = 'polygon'

