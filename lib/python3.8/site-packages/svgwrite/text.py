#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: text objects
# Created: 20.09.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License
"""
Text that is to be rendered as part of an SVG document fragment is specified
using the **text** element. The characters to be drawn are expressed as XML
character data inside the **text** element.

"""

from svgwrite.base import BaseElement
from svgwrite.mixins import Presentation, Transform, XLink
from svgwrite.utils import iterflatlist, strlist, is_string


class TSpan(BaseElement, Presentation):
    """
    Within a **Text** element, text and font properties
    and the current text position can be adjusted with absolute or relative
    coordinate values by using the **TSpan** element.
    The characters to be drawn are expressed as XML character data inside the
    **TSpan** element.

    """
    elementname = 'tspan'

    def __init__(self, text, insert=None, x=None, y=None, dx=None, dy=None, rotate=None,
                 **extra):
        """
        :param string text: **tspan** content
        :param 2-tuple insert: The **insert** parameter is the absolute insert point
                               of the text, don't use this parameter in combination
                               with the **x** or the **y** parameter.
        :param list x: list of absolute x-axis values for characters
        :param list y: list of absolute y-axis values for characters
        :param list dx: list of relative x-axis values for characters
        :param list dy: list of relative y-axis values for characters
        :param list rotate: list of rotation-values for characters (in degrees)

        """
        super(TSpan, self).__init__(**extra)
        self.text = text
        if insert is not None:
            if is_string(insert):
                raise TypeError("'insert' should be a <tuple> or a <list>  with"
                                " at least two elements.")
            if x or y:
                raise ValueError("Use 'insert' and 'x' or 'y' parameter not"
                                 " at the same time!")
            x = [insert[0]]
            y = [insert[1]]

        if x is not None:
            self['x'] = strlist(list(iterflatlist(x)), ' ')
        if y is not None:
            self['y'] = strlist(list(iterflatlist(y)), ' ')
        if dx is not None:
            self['dx'] = strlist(list(iterflatlist(dx)), ' ')
        if dy is not None:
            self['dy'] = strlist(list(iterflatlist(dy)), ' ')
        if rotate is not None:
            self['rotate'] = strlist(list(iterflatlist(rotate)), ' ')

    def get_xml(self):
        xml = super(TSpan, self).get_xml()
        xml.text = str(self.text)
        return xml


class Text(TSpan, Transform):
    """
    The **Text** element defines a graphics element consisting of text.
    The characters to be drawn are expressed as XML character data inside the
    **Text** element.

    """
    elementname = 'text'


class TRef(BaseElement, XLink, Presentation):
    """
    The textual content for a **Text** can be either character data directly
    embedded within the <text> element or the character data content of a
    referenced element, where the referencing is specified with a **TRef**
    element.

    """
    elementname = 'tref'

    def __init__(self, element, **extra):
        """
        :param element: create a reference this element, if element is a \
                        `string` its the **id** name of the referenced element, \
                        if element is a :class:`~svgwrite.base.BaseElement` \
                        the **id** SVG Attribute is used to create the reference.

        """
        super(TRef, self).__init__(**extra)
        self.set_href(element)

    def get_xml(self):
        self.update_id()  # if href is an object - 'id' - attribute may be changed!
        return super(TRef, self).get_xml()


class TextPath(BaseElement, XLink, Presentation):
    """
    In addition to text drawn in a straight line, SVG also includes the
    ability to place text along the shape of a **path** element. To specify that
    a block of text is to be rendered along the shape of a **path**, include
    the given text within a **textPath** element which includes an **xlink:href**
    attribute with a IRI reference to a **path** element.

    """
    elementname = 'textPath'

    def __init__(self, path, text, startOffset=None, method='align', spacing='exact',
                 **extra):
        """
        :param path: link to **path**, **id** string or **Path** object
        :param string text: **textPath** content
        :param number startOffset: text starts with offset from begin of path.
        :param string method: ``align|stretch``
        :param string spacing: ``exact|auto``

        """
        super(TextPath, self).__init__(**extra)
        self.text = text
        if method == 'stretch':
            self['method'] = method
        if spacing == 'auto':
            self['spacing'] = spacing
        if startOffset is not None:
            self['startOffset'] = startOffset
        self.set_href(path)

    def get_xml(self):
        self.update_id() # if href is an object - 'id' - attribute may be changed!
        xml = super(TextPath, self).get_xml()
        xml.text = str(self.text)
        return xml


class TBreak(BaseElement):
    elementname = 'tbreak'

    def __init__(self, **extra):
        super(TBreak, self).__init__(**extra)

    def __getitem__(self, key):
        raise NotImplementedError("__getitem__() not supported by TBreak class.")

    def __setitem__(self, key, value):
        raise NotImplementedError("__setitem__() not supported by TBreak class.")

    def add(self, element):
        raise NotImplementedError("add() not supported by TBreak class.")


class TextArea(BaseElement, Transform, Presentation):
    """
    At this time **textArea** is only available for SVG 1.2 Tiny profile.

    The **textArea**  element allows simplistic wrapping of text content within a
    given region. The `tiny` profile of SVG specifies a single rectangular region.
    Other profiles may allow a sequence of arbitrary shapes.

    Text wrapping via the **textArea** element is available as a lightweight and
    convenient facility for simple text wrapping where a complete box model layout
    engine is not required.

    The layout of wrapped text is user agent dependent; thus, content developers
    need to be aware that there might be different results, particularly with
    regard to where line breaks occur.

    The TextArea class wraps every text added by write() or writeline() as
    **tspan** element.

    """
    elementname = 'textArea'

    def __init__(self, text=None, insert=None, size=None, **extra):
        super(TextArea, self).__init__(**extra)
        if text is not None:
            self.write(text)
        if insert is not None:
            self['x'] = insert[0]
            self['y'] = insert[1]
        if size is not None:
            self['width'] = size[0]
            self['height'] = size[1]

    def line_increment(self, value):
        """ Set the line-spacing to *value*. """
        self['line-increment'] = value

    def write(self, text, **extra):
        """
        Add text as **tspan** elements, with extra-params for the **tspan** element.

        Use the '\\\\n' character for line breaks.
        """
        if '\n' not in text:
            self.add(TSpan(text, **extra))
        else:
            lines = text.split('\n')
            for line in lines[:-1]:
                if line:  # no text between '\n'+
                    self.add(TSpan(line, **extra))
                self.add(TBreak())
            # case "text\n" : last element is ''
            # case "texta\ntextb : last element is 'textb'
            if lines[-1]:
                self.add(TSpan(lines[-1], **extra))
