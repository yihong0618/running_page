#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: mixins
# Created: 19.10.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License

from svgwrite.utils import strlist
from svgwrite.utils import is_string

_horiz = {'center': 'xMid', 'left': 'xMin', 'right': 'xMax'}
_vert  = {'middle': 'YMid', 'top': 'YMin', 'bottom':'YMax'}

class ViewBox(object):
    """ The **ViewBox** mixin provides the ability to specify that a
    given set of graphics stretch to fit a particular container element.

    The value of the **viewBox** attribute is a list of four numbers
    **min-x**, **min-y**, **width** and **height**, separated by whitespace
    and/or a comma, which specify a rectangle in **user space** which should
    be mapped to the bounds of the viewport established by the given element,
    taking into account attribute **preserveAspectRatio**.

    """
    def viewbox(self, minx=0, miny=0, width=0, height=0):
        """ Specify a rectangle in **user space** (no units allowed) which
        should be mapped to the bounds of the viewport established by the
        given element.

        :param number minx: left border of the viewBox
        :param number miny: top border of the viewBox
        :param number width: width of the viewBox
        :param number height: height of the viewBox

        """
        self['viewBox'] = strlist( [minx, miny, width, height] )

    def stretch(self):
        """ Stretch viewBox in x and y direction to fill viewport, does not
        preserve aspect ratio.
        """
        self['preserveAspectRatio'] = 'none'

    def fit(self, horiz="center", vert="middle", scale="meet"):
        """ Set the **preserveAspectRatio** attribute.

        :param string horiz: horizontal alignment ``'left | center | right'``
        :param string vert: vertical alignment ``'top | middle | bottom'``
        :param string scale: scale method ``'meet | slice'``

        ============= =======================================================
        Scale methods Description
        ============= =======================================================
        ``'meet'``    preserve aspect ration and zoom to limits of viewBox
        ``'slice'``   preserve aspect ration and viewBox touch viewport on
                      all bounds, viewBox will extend beyond the bounds of
                      the viewport
        ============= =======================================================

        """
        if self.debug and scale not in ('meet', 'slice'):
            raise ValueError("Invalid scale parameter '%s'" % scale)
        self['preserveAspectRatio'] = "%s%s %s" % (_horiz[horiz],_vert[vert], scale)

class Transform(object):
    """ The **Transform** mixin operates on the **transform** attribute.
    The value of the **transform** attribute is a `<transform-list>`, which
    is defined as a list of transform definitions, which are applied in the
    order provided. The individual transform definitions are separated by
    whitespace and/or a comma. All coordinates are **user
    space coordinates**.

    """
    transformname = 'transform'
    def translate(self, tx, ty=None):
        """
        Specifies a translation by **tx** and **ty**. If **ty** is not provided,
        it is assumed to be zero.

        :param number tx: user coordinate - no units allowed
        :param number ty: user coordinate - no units allowed
        """
        self._add_transformation("translate(%s)" % strlist( [tx, ty] ))

    def rotate(self, angle, center=None):
        """
        Specifies a rotation by **angle** degrees about a given point.
        If optional parameter **center** are not supplied, the rotate is
        about the origin of the current user coordinate system.

        :param number angle: rotate-angle in degrees
        :param 2-tuple center: rotate-center as user coordinate - no units allowed

        """
        self._add_transformation("rotate(%s)" % strlist( [angle, center] ))

    def scale(self, sx, sy=None):
        """
        Specifies a scale operation by **sx** and **sy**. If **sy** is not
        provided, it is assumed to be equal to **sx**.

        :param number sx: scalar factor x-axis, no units allowed
        :param number sy: scalar factor y-axis, no units allowed

        """
        self._add_transformation("scale(%s)" % strlist([sx, sy]))

    def skewX(self, angle):
        """ Specifies a skew transformation along the x-axis.

        :param number angle: skew-angle in degrees, no units allowed

        """
        self._add_transformation("skewX(%s)" % angle)

    def skewY(self, angle):
        """ Specifies a skew transformation along the y-axis.

        :param number angle: skew-angle in degrees, no units allowed

        """
        self._add_transformation("skewY(%s)" % angle)

    def matrix(self, a, b, c, d, e, f):
        self._add_transformation("matrix(%s)" % strlist( [a, b, c, d, e, f] ))

    def _add_transformation(self, new_transform):
        old_transform = self.attribs.get(self.transformname, '')
        self[self.transformname] = ("%s %s" % (old_transform, new_transform)).strip()


class XLink(object):
    """ XLink mixin """
    def set_href(self, element):
        """
        Create a reference to **element**.

        :param element: if element is a `string` its the **id** name of the
          referenced element, if element is a **BaseElement** class the **id**
          SVG Attribute is used to create the reference.

        """
        self.href = element
        self.update_id()

    def set_xlink(self, title=None, show=None, role=None, arcrole=None):
        """ Set XLink attributes (for `href` use :meth:`set_href`).
        """
        if role is not None:
            self['xlink:role'] = role
        if arcrole is not None:
            self['xlink:arcrole'] = arcrole
        if title is not None:
            self['xlink:title'] = title
        if show is not None:
            self['xlink:show'] = show

    def update_id(self):
        if not hasattr(self, 'href'):
            return
        if is_string(self.href):
            idstr = self.href
        else:
            idstr = self.href.get_iri()
        self.attribs['xlink:href'] = idstr


class Presentation(object):
    """
    Helper methods to set presentation attributes.
    """
    def fill(self, color=None, rule=None, opacity=None):
        """
        Set SVG Properties **fill**, **fill-rule** and **fill-opacity**.

        """
        if color is not None:
            if is_string(color):
                self['fill'] = color
            else:
                self['fill'] = color.get_paint_server()
        if rule is not None:
            self['fill-rule'] = rule
        if opacity is not None:
            self['fill-opacity'] = opacity
        return self

    def stroke(self, color=None, width=None, opacity=None, linecap=None,
               linejoin=None, miterlimit=None):
        """
        Set SVG Properties **stroke**, **stroke-width**, **stroke-opacity**,
        **stroke-linecap** and **stroke-miterlimit**.

        """

        if color is not None:
            if is_string(color):
                self['stroke'] = color
            else:
                self['stroke'] = color.get_paint_server()
        if width is not None:
            self['stroke-width'] = width
        if opacity is not None:
            self['stroke-opacity'] = opacity
        if linecap is not None:
            self['stroke-linecap'] = linecap
        if linejoin is not None:
            self['stroke-linejoin'] = linejoin
        if miterlimit is not None:
            self['stroke-miterlimit'] = miterlimit
        return self

    def dasharray(self, dasharray=None, offset=None):
        """
        Set SVG Properties **stroke-dashoffset** and **stroke-dasharray**.

        Where *dasharray* specify the lengths of alternating dashes and gaps as
        <list> of <int> or <float> values or a <string> of comma and/or white
        space separated <lengths> or <percentages>. (e.g. as <list> dasharray=[1, 0.5]
        or as <string> dasharray='1 0.5')
        """
        if dasharray is not None:
            self['stroke-dasharray'] = strlist(dasharray, ' ')
        if offset is not None:
            self['stroke-dashoffset'] = offset
        return self


class MediaGroup(object):
    """
    Helper methods to set media group attributes.

    """

    def viewport_fill(self, color=None, opacity=None):
        """
        Set SVG Properties **viewport-fill** and **viewport-fill-opacity**.

        """
        if color is not None:
            self['viewport-fill'] = color
        if opacity is not None:
            self['viewport-fill-opacity'] = opacity
        return self


class Markers(object):
    """
    Helper methods to set marker attributes.

    """
    def set_markers(self, markers):
        """
        Set markers for line elements (line, polygon, polyline, path) to
        values specified by  `markers`.

        * if `markers` is a 3-tuple:

          * attribute 'marker-start' = markers[0]
          * attribute 'marker-mid' = markers[1]
          * attribute 'marker-end' = markers[2]

        * `markers` is a `string` or a `Marker` class:

          * attribute 'marker' = `FuncIRI` of markers

        """
        def get_funciri(value):
            if is_string(value):
                # strings has to be a valid reference including the '#'
                return 'url(%s)' % value
            else:
                # else create a reference to the object '#id'
                return 'url(#%s)' % value['id']

        if is_string(markers):
            self['marker'] = get_funciri(markers)
        else:
            try:
                start_marker, mid_marker, end_marker = markers
                if start_marker:
                    self['marker-start'] = get_funciri(start_marker)
                if mid_marker:
                    self['marker-mid'] = get_funciri(mid_marker)
                if end_marker:
                    self['marker-end'] = get_funciri(end_marker)
            except (TypeError, KeyError):
                self['marker'] = get_funciri(markers)


class Clipping(object):
    def clip_rect(self, top='auto', right='auto', bottom='auto', left='auto'):
        """
        Set SVG Property **clip**.

        """
        self['clip'] = "rect(%s,%s,%s,%s)" % (top, right, bottom, left)
