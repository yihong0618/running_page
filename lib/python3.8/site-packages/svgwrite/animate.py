#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: animate elements
# Created: 31.10.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License

from svgwrite.base import BaseElement
from svgwrite.mixins import XLink
from svgwrite.utils import strlist, is_string


class Set(BaseElement, XLink):
    """ The **set** element provides a simple means of just setting the value
    of an attribute for a specified duration. It supports all attribute types,
    including those that cannot reasonably be interpolated, such as string
    and boolean values. The **set** element is non-additive. The additive and
    accumulate attributes are not allowed, and will be ignored if specified.
    """
    elementname = 'set'

    def __init__(self, href=None, **extra):
        """ Set constructor.

        :param href: target svg element, if **href** is not `None`; else
            the target SVG Element is the parent SVG Element.
        """
        super(Set, self).__init__(**extra)
        if href is not None:
            self.set_href(href)

    def get_xml(self):
        self.update_id() # if href is an object - 'id' - attribute may be changed!
        return super(Set, self).get_xml()

    def set_target(self, attributeName, attributeType=None):
        """
        Set animation attributes :ref:`attributeName` and :ref:`attributeType`.
        """
        self['attributeName'] = attributeName
        if attributeType is not None:
            self['attributeType'] = attributeType


    def set_event(self, onbegin=None, onend=None, onrepeat=None, onload=None):
        """
        Set animation attributes :ref:`onbegin`, :ref:`onend`, :ref:`onrepeat`
        and :ref:`onload`.
        """
        if onbegin is not None:
            self['onbegin'] = onbegin
        if onend is not None:
            self['onend'] = onend
        if onrepeat is not None:
            self['onrepeat'] = onrepeat
        if onload is not None:
            self['onload'] = onload

    def set_timing(self, begin=None, end=None, dur=None, min=None, max=None,
                   restart=None, repeatCount=None, repeatDur=None):
        """
        Set animation attributes :ref:`begin`, :ref:`end`, :ref:`dur`,
        :ref:`min`, :ref:`max`, :ref:`restart`, :ref:`repeatCount` and
        :ref:`repeatDur`.
        """
        if begin is not None:
            self['begin'] = begin
        if end is not None:
            self['end'] = end
        if dur is not None:
            self['dur'] = dur
        if min is not None:
            self['min'] = min
        if max is not None:
            self['max'] = max
        if restart is not None:
            self['restart'] = restart
        if repeatCount is not None:
            self['repeatCount'] = repeatCount
        if repeatDur is not None:
            self['repeatDur'] = repeatDur

    def freeze(self):
        """ Freeze the animation effect. (see also :ref:`fill <animateFill>`)
        """
        self['fill'] = 'freeze'

class AnimateMotion(Set):
    """ The **animateMotion** element causes a referenced element to move
    along a motion path.
    """
    elementname = 'animateMotion'

    def __init__(self, path=None, href=None, **extra):
        """
        :param path: the motion path
        :param href: target svg element, if **href** is not `None`; else
          the target SVG Element is the parent SVG Element.
        """
        super(AnimateMotion, self).__init__(href=href, **extra)
        if path is not None:
            self['path'] = path

    def set_value(self, path=None, calcMode=None, keyPoints=None, rotate=None):
        """
        Set animation attributes `path`, `calcMode`, `keyPoints` and `rotate`.
        """
        if path is not None:
            self['path'] = path
        if calcMode is not None:
            self['calcMode'] = calcMode
        if keyPoints is not None:
            self['keyPoints'] = keyPoints
        if rotate is not None:
            self['rotate'] = rotate


class Animate(Set):
    """ The **animate** element allows scalar attributes and properties to be
    assigned different values over time .
    """
    elementname = 'animate'

    def __init__(self, attributeName=None, values=None, href=None, **extra):
        """
        :param attributeName: name of the SVG Attribute to animate
        :param values: interpolation values, `string` as `<semicolon-list>` or a python `list`
        :param href: target svg element, if **href** is not `None`; else
          the target SVG Element is the parent SVG Element.
        """
        super(Animate, self).__init__(href=href, **extra)
        if values is not None:
            self.set_value(values)
        if attributeName is not None:
            self.set_target(attributeName)

    def set_value(self, values, calcMode=None, keyTimes=None, keySplines=None,
                  from_=None, to=None, by=None):
        """
        Set animation attributes :ref:`values`, :ref:`calcMode`, :ref:`keyTimes`,
        :ref:`keySplines`, :ref:`from`, :ref:`to` and :ref:`by`.
        """
        if values is not None:
            if not is_string(values):
                values = strlist(values, ';')
            self['values'] = values

        if calcMode is not None:
            self['calcMode'] = calcMode
        if keyTimes is not None:
            self['keyTimes'] = keyTimes
        if keySplines is not None:
            self['keySplines'] = keySplines
        if from_ is not None:
            self['from'] = from_
        if to is not None:
            self['to'] = to
        if by is not None:
            self['by'] = by


class AnimateColor(Animate):
    """ The **animateColor** element specifies a color transformation over
    time.
    """
    elementname = 'animateColor'


class AnimateTransform(Animate):
    """ The **animateTransform** element animates a transformation attribute
    on a target element, thereby allowing animations to control translation,
    scaling, rotation and/or skewing.
    """
    elementname = 'animateTransform'
    def __init__(self, transform, element=None, **extra):
        """
        :param element: target svg element, if element is not `None`; else
          the target svg element is the parent svg element.
        :param string transform: ``'translate | scale | rotate | skewX | skewY'``
        """
        super(AnimateTransform, self).__init__(element, **extra)
        self['type'] = transform
