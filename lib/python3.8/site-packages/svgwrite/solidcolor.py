#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: solidColor paint serve (Tiny 1.2 profile)
# Created: 26.10.2016
# Copyright (C) 2016, Manfred Moitzi
# License: MIT License

from svgwrite.base import BaseElement
from svgwrite.mixins import XLink


class SolidColor(BaseElement, XLink):
    """
    The `solidColor` element is a paint server that provides a single color with opacity.
    It can be referenced like the other paint servers (i.e. gradients).
    The `color` parameter specifies the color that shall be used for this `solidColor` element.
    The keyword ``"currentColor"`` can be specified in the same manner as within a <paint> specification for the `fill`
    and `stroke` properties. The `opacity` parameter defines the opacity of the `solidColor`.
    """
    elementname = 'solidColor'

    def __init__(self, color="currentColor", opacity=None, **extra):
        """
        :param color: solid color like the other paint servers (i.e. gradients).
        :param float opacity: opacity of the solid color in the range `0.0` (fully transparent) to `1.0` (fully opaque)

        """
        super(SolidColor, self).__init__(**extra)
        if self.profile != 'tiny':
            raise TypeError("Paint server 'solidColor' requires the Tiny SVG profile.")
        self['solid-color'] = color
        if opacity is not None:
            self['solid-opacity'] = opacity

        if self.debug:
            self.validator.check_all_svg_attribute_values(self.elementname, self.attribs)

    def get_paint_server(self, default='none'):
        """ Returns the <FuncIRI> of the gradient. """
        return "%s %s" % (self.get_funciri(), default)
