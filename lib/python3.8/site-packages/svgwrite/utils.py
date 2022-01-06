#!/usr/bin/env python
# coding:utf-8
# Author:  mozman
# Purpose: svg util functions and classes
# Created: 08.09.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License
"""

.. autofunction:: rgb

.. autofunction:: iterflatlist

.. autofunction:: strlist

.. autofunction:: get_unit

.. autofunction:: split_coordinate

.. autofunction:: split_angle

.. autofunction:: rect_top_left_corner

.. autofunction:: pretty_xml

"""
import base64
from pathlib import Path
from svgwrite.data import pattern


def is_string(value):
    return isinstance(value, str)


def rgb(r=0, g=0, b=0, mode='RGB'):
    """
    Convert **r**, **g**, **b** values to a `string`.

    :param r: red part
    :param g: green part
    :param b: blue part
    :param string mode: ``'RGB | %'``

    :rtype: string

    ========= =============================================================
    mode      Description
    ========= =============================================================
    ``'RGB'`` returns a rgb-string format: ``'rgb(r, g, b)'``
    ``'%'``   returns percent-values as rgb-string format: ``'rgb(r%, g%, b%)'``
    ========= =============================================================

    """

    def percent(value):
        value = float(value)
        if value < 0:
            value = 0
        if value > 100:
            value = 100
        return value

    if mode.upper() == 'RGB':
        return "rgb(%d,%d,%d)" % (int(r) & 255, int(g) & 255, int(b) & 255)
    elif mode == "%":
        # see http://www.w3.org/TR/SVG11/types.html#DataTypeColor
        # percentage is an 'number' value
        return "rgb(%d%%,%d%%,%d%%)" % (percent(r), percent(g), percent(b))
    else:
        raise ValueError("Invalid mode '%s'" % mode)


def iterflatlist(values):
    """
    Flatten nested *values*, returns an `iterator`.

    """
    for element in values:
        if hasattr(element, "__iter__") and not is_string(element):
            for item in iterflatlist(element):
                yield item
        else:
            yield element


def strlist(values, seperator=","):
    """
    Concatenate **values** with **sepertator**, `None` values will be excluded.

    :param values: `iterable` object
    :returns: `string`

    """
    if is_string(values):
        return values
    else:
        return seperator.join([str(value) for value in iterflatlist(values) if value is not None])


def get_unit(coordinate):
    """
    Get the `unit` identifier of **coordinate**, if **coordinate** has a valid
    `unit` identifier appended, else returns `None`.

    """
    if isinstance(coordinate, (int, float)):
        return None
    result = pattern.coordinate.match(coordinate)
    if result:
        return result.group(3)
    else:
        raise ValueError("Invalid format: '%s'" % coordinate)


def split_coordinate(coordinate):
    """
    Split coordinate into `<number>` and 'unit` identifier.

    :returns: <2-tuple> (number, unit-identifier) or (number, None) if no unit-identifier
      is present or coordinate is an int or float.

    """
    if isinstance(coordinate, (int, float)):
        return (float(coordinate), None)
    result = pattern.coordinate.match(coordinate)
    if result:
        return (float(result.group(1)), result.group(3))
    else:
        raise ValueError("Invalid format: '%s'" % coordinate)


def split_angle(angle):
    """
    Split angle into `<number>` and `<angle>` identifier.

    :returns: <2-tuple> (number, angle-identifier) or (number, None) if no angle-identifier
      is present or angle is an int or float.

    """

    if isinstance(angle, (int, float)):
        return (float(angle), None)
    result = pattern.angle.match(angle)
    if result:
        return (float(result.group(1)), result.group(3))
    else:
        raise ValueError("Invalid format: '%s'" % angle)


def rect_top_left_corner(insert, size, pos='top-left'):
    """
    Calculate top-left corner of a rectangle.

    **insert** and **size** must have the same units.

    :param 2-tuple insert: insert point
    :param 2-tuple size: (width, height)
    :param string pos: insert position ``'vert-horiz'``
    :return: ``'top-left'`` corner of the rect
    :rtype: 2-tuple

    ========== ==============================
    pos        valid values
    ========== ==============================
    **vert**   ``'top | middle | bottom'``
    **horiz**  ``'left'|'center'|'right'``
    ========== ==============================
    """
    vert, horiz = pos.lower().split('-')
    x, xunit = split_coordinate(insert[0])
    y, yunit = split_coordinate(insert[1])
    width, wunit = split_coordinate(size[0])
    height, hunit = split_coordinate(size[1])

    if xunit != wunit:
        raise ValueError("x-coordinate and width has to have the same unit")
    if yunit != hunit:
        raise ValueError("y-coordinate and height has to have the same unit")

    if horiz == 'center':
        x = x - width / 2.
    elif horiz == 'right':
        x = x - width
    elif horiz != 'left':
        raise ValueError("Invalid horizontal position: '%s'" % horiz)

    if vert == 'middle':
        y = y - height / 2.
    elif vert == 'bottom':
        y = y - height
    elif vert != 'top':
        raise ValueError("Invalid vertical position: '%s'" % vert)

    if xunit:
        x = "%s%s" % (x, xunit)
    if yunit:
        y = "%s%s" % (y, yunit)
    return x, y


class AutoID(object):
    _nextid = 1

    def __init__(self, value=None):
        self._set_value(value)

    @classmethod
    def _set_value(cls, value=None):
        if value is not None:
            cls._nextid = value

    @classmethod
    def next_id(cls, value=None):
        cls._set_value(value)
        retval = "id%d" % cls._nextid
        cls._nextid += 1
        return retval


def pretty_xml(xml_string, indent=2):
    """
    Create human readable XML string.

    :param xml_string: input xml string without line breaks and indentation
    :indent int: how much to indent, by default 2 spaces
    :return: xml_string with linebreaks and indentation

    """
    import xml.dom.minidom as minidom

    # check for empty string, len check avoids unnecessary string manipulation with large XML strings
    if len(xml_string) < 20 and xml_string.strip() == "":
        return ""
    xml_tree = minidom.parseString(xml_string)
    lines = xml_tree.toprettyxml(indent=' ' * indent).split('\n')
    # remove 1. line = xml declaration
    return '\n'.join(lines[1:])


FONT_MIMETYPES = {
    'ttf': "application/x-font-ttf",
    'otf': "application/x-font-opentype",
    'woff': "application/font-woff",
    'woff2': "application/font-woff2",
    'eot': "application/vnd.ms-fontobject",
    'sfnt': "application/font-sfnt",
}


def font_mimetype(name):
    return FONT_MIMETYPES[Path(name.lower()).suffix[1:]]


def base64_data(data, mimetype):
    data = base64.b64encode(data).decode()
    return "data:{mimetype};charset=utf-8;base64,{data}".format(mimetype=mimetype, data=data)


def find_first_url(text):
    import re
    result = re.findall(r"url\((.*?)\)", text)
    if result:
        return result[0]
    else:
        return None
