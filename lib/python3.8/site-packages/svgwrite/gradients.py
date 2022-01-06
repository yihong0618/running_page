#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: gradients module
# Created: 26.10.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License
"""
Gradients consist of continuously smooth color transitions along a vector
from one color to another, possibly followed by additional transitions along
the same vector to other colors. SVG provides for two types of gradients:
linear gradients and radial gradients.
"""

from svgwrite.base import BaseElement
from svgwrite.mixins import Transform, XLink
from svgwrite.utils import is_string


class _GradientStop(BaseElement):
    elementname = 'stop'

    def __init__(self, offset=None, color=None, opacity=None, **extra):
        super(_GradientStop, self).__init__(**extra)

        if offset is not None:
            self['offset'] = offset
        if color is not None:
            self['stop-color'] = color
        if opacity is not None:
            self['stop-opacity'] = opacity


class _AbstractGradient(BaseElement, Transform, XLink):
    transformname = 'gradientTransform'

    def __init__(self, inherit=None, **extra):
        super(_AbstractGradient, self).__init__(**extra)
        if inherit is not None:
            if is_string(inherit):
                self.set_href(inherit)
            else:
                self.set_href(inherit.get_iri())

    def get_paint_server(self, default='none'):
        """ Returns the <FuncIRI> of the gradient. """
        return "%s %s" % (self.get_funciri(), default)

    def add_stop_color(self, offset=None, color=None, opacity=None):
        """ Adds a stop-color to the gradient.

        :param offset: is either a <number> (usually ranging from 0 to 1) or
          a `<percentage>` (usually ranging from 0% to 100%) which indicates where
          the gradient stop is placed. Represents a location along the gradient
          vector. For radial gradients, it represents a percentage distance from
          (fx,fy) to the edge of the outermost/largest circle.
        :param color: indicates what color to use at that gradient stop
        :param opacity: defines the opacity of a given gradient stop
        """
        self.add(_GradientStop(offset, color, opacity, factory=self))
        return self

    def add_colors(self, colors, sweep=(0., 1.), opacity=None):
        """ Add stop-colors from colors with linear offset distributuion
        from sweep[0] to sweep[1].

        i.e. colors=['white', 'red', 'blue']
          'white': offset = 0.0
          'red': offset = 0.5
          'blue': offset = 1.0
        """
        delta = (sweep[1] - sweep[0]) / (len(colors) - 1)
        offset = sweep[0]
        for color in colors:
            self.add_stop_color(round(offset, 3), color, opacity)
            offset += delta
        return self

    def get_xml(self):
        if hasattr(self, 'href'):
            self.update_id()
        return super(_AbstractGradient, self).get_xml()


class LinearGradient(_AbstractGradient):
    """ Linear gradients are defined by a SVG <linearGradient> element.
    """
    elementname = 'linearGradient'

    def __init__(self, start=None, end=None, inherit=None, **extra):
        """
        :param 2-tuple start: start point of the gradient (**x1**, **y1**)
        :param 2-tuple end: end point of the gradient (**x2**, **y2**)
        :param inherit: gradient inherits properties from `inherit` see: **xlink:href**

        """
        super(LinearGradient, self).__init__(inherit=inherit, **extra)
        if start is not None:
            self['x1'] = start[0]
            self['y1'] = start[1]
        if end is not None:
            self['x2'] = end[0]
            self['y2'] = end[1]


class RadialGradient(_AbstractGradient):
    """ Radial gradients are defined by a SVG <radialGradient> element.
    """
    elementname = 'radialGradient'

    def __init__(self, center=None, r=None, focal=None, inherit=None, **extra):
        """
        :param 2-tuple center: center point for the gradient (**cx**, **cy**)
        :param r: radius for the gradient
        :param 2-tuple focal: focal point for the radial gradient (**fx**, **fy**)
        :param inherit: gradient inherits properties from `inherit` see: **xlink:href**

        """

        super(RadialGradient, self).__init__(inherit=inherit, **extra)
        if center is not None:
            self['cx'] = center[0]
            self['cy'] = center[1]
        if r is not None:
            self['r'] = r
        if focal is not None:
            self['fx'] = focal[0]
            self['fy'] = focal[1]
