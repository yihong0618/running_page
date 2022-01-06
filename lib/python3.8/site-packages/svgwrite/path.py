#coding:utf-8
# Author:  mozman
# Purpose: svg path element
# Created: 08.09.2010
# License: MIT License

from svgwrite.base import BaseElement
from svgwrite.utils import strlist
from svgwrite.mixins import Presentation, Markers, Transform


class Path(BaseElement, Transform, Presentation, Markers):
    """ The <path> element represent the outline of a shape which can be filled,
    stroked, used as a clipping path, or any combination of the three.

    """
    elementname = 'path'

    def __init__(self, d=None, **extra):
        """
        :param `iterable` d: *coordinates*, *length* and *commands*
        :param dict attribs: additional SVG attributes
        :param extra: additional SVG attributes as keyword-arguments

        """
        super(Path, self).__init__(**extra)
        self.commands = []
        self.push(d)
        if self.debug:
            self.validator.check_all_svg_attribute_values(self.elementname, self.attribs)

    def push(self, *elements):
        """ Push commands and coordinates onto the command stack.

        :param `iterable` elements: *coordinates*, *length* and *commands*

        """
        self.commands.extend(elements)

    @staticmethod
    def arc_flags(large_arc=True, angle_dir='+'):
        large_arc_flag = int(large_arc)
        sweep_flag = {'+': 1, '-': 0}[angle_dir]
        return "%d,%d" % (large_arc_flag, sweep_flag)

    def push_arc(self, target, rotation, r, large_arc=True, angle_dir='+', absolute=False):
        """ Helper function for the elliptical-arc command.

        see SVG-Reference: http://www.w3.org/TR/SVG11/paths.html#PathData

        :param 2-tuple target: *coordinate* of the arc end point
        :param number rotation: x-axis-rotation of the ellipse in degrees
        :param number|2-tuple r: radii rx, ry when r is a *2-tuple* or rx=ry=r if r is a *number*
        :param bool large_arc: draw the arc sweep of greater than or equal to 180 degrees (**large-arc-flag**)
        :param angle_dir: ``'+|-'`` ``'+'`` means the arc will be drawn in a "positive-angle" direction (**sweep-flag**)
        :param bool absolute: indicates that target *coordinates* are absolute else they are relative to the current point

        """
        self.push({True: 'A', False: 'a'}[absolute])
        if isinstance(r, (float, int)):
            self.push(r, r)
        else:
            self.push(r)
        self.push(rotation)
        self.push(Path.arc_flags(large_arc, angle_dir))
        self.push(target)

    def get_xml(self):
        """ Get the XML representation as `ElementTree` object.

        :return: XML `ElementTree` of this object and all its subelements

        """
        self.attribs['d'] = str(strlist(self.commands, ' '))
        return super(Path, self).get_xml()
