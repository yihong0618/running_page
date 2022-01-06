#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: svg image element
# Created: 09.10.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License

from svgwrite.base import BaseElement
from svgwrite.mixins import Transform, _vert, _horiz, Clipping

class Image(BaseElement, Transform, Clipping):
    """ The **image** element indicates that the contents of a complete file are
    to be rendered into a given rectangle within the current user coordinate
    system. The **image** element can refer to raster image files such as PNG
    or JPEG or to files with MIME type of "image/svg+xml".

    """
    elementname = 'image'

    def __init__(self, href, insert=None, size=None, **extra):
        """
        :param string href: hyperlink to the image resource
        :param 2-tuple insert: insert point (**x**, **y**)
        :param 2-tuple size: (**width**, **height**)
        :param dict attribs: additional SVG attributes
        :param extra: additional SVG attributes as keyword-arguments
        """
        super(Image, self).__init__(**extra)
        self['xlink:href'] = href
        if insert is not None:
            self['x'] = insert[0]
            self['y'] = insert[1]
        if size is not None:
            self['width'] = size[0]
            self['height'] = size[1]

    def stretch(self):
        """ Stretch viewBox in x and y direction to fill viewport, does not
        preserve aspect ratio.
        """
        self['preserveAspectRatio'] = 'none'

    def fit(self, horiz="center", vert="middle", scale="meet"):
        """ Set the preserveAspectRatio attribute.

        :param string horiz: horizontal alignment ``'left'|'center'|'right'``
        :param string vert: vertical alignment ``'top'|'middle'|'bottom'``
        :param string scale: scale method ``'meet'|'slice'``

        ============= ===========
        Scale methods Description
        ============= ===========
        ``meet``      preserve aspect ration and zoom to limits of viewBox
        ``slice``     preserve aspect ration and viewBox touch viewport on all bounds, viewBox will extend beyond the bounds of the viewport
        ============= ===========

        """
        if self.debug and scale not in ('meet', 'slice'):
            raise ValueError("Invalid scale parameter '%s'" % scale)
        self.attribs['preserveAspectRatio'] = "%s%s %s" % (_horiz[horiz],_vert[vert], scale)
