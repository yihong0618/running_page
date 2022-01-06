#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: pattern module
# Created: 29.10.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License

from svgwrite.base import BaseElement
from svgwrite.mixins import XLink, ViewBox, Transform, Presentation
from svgwrite.utils import is_string

class Pattern(BaseElement, XLink, ViewBox, Transform, Presentation):
    """
    A pattern is used to fill or stroke an object using a pre-defined graphic
    object which can be replicated ("tiled") at fixed intervals in x and y to
    cover the areas to be painted. Patterns are defined using a `pattern` element
    and then referenced by properties `fill` and `stroke` on a given graphics
    element to indicate that the given element shall be filled or stroked with
    the referenced pattern.
    """
    elementname = 'pattern'
    transformname = 'patternTransform'

    def __init__(self, insert=None, size=None, inherit=None, **extra):
        """
        :param 2-tuple insert: base point of the pattern (**x**, **y**)
        :param 2-tuple size: size of the pattern (**width**, **height**)
        :param inherit: pattern inherits properties from `inherit` see: **xlink:href**

        """
        super(Pattern, self).__init__(**extra)
        if insert is not None:
            self['x'] = insert[0]
            self['y'] = insert[1]
        if size is not None:
            self['width'] = size[0]
            self['height'] = size[1]
        if inherit is not None:
            if is_string(inherit):
                self.set_href(inherit)
            else:
                self.set_href(inherit.get_iri())

        if self.debug:
            self.validator.check_all_svg_attribute_values(self.elementname, self.attribs)

    def get_paint_server(self, default='none'):
        """ Returns the <FuncIRI> of the gradient. """
        return "%s %s" % (self.get_funciri(), default)
