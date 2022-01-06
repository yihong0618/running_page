#!/usr/bin/env python
#coding:utf-8
# Author:  mozman
# Purpose: svg base element
# Created: 08.09.2010
# Copyright (c) 2010-2020, Manfred Moitzi
# License: MIT License
"""
The **BaseElement** is the root for all SVG elements.
"""

from svgwrite.etree import etree

import copy

from svgwrite.params import Parameter
from svgwrite.utils import AutoID


class BaseElement(object):
    """
    The **BaseElement** is the root for all SVG elements. The SVG attributes
    are stored in **attribs**, and the SVG subelements are stored in
    **elements**.

    """
    elementname = 'baseElement'

    def __init__(self, **extra):
        """
        :param extra: extra SVG attributes (keyword arguments)

          * add trailing '_' to reserved keywords: ``'class_'``, ``'from_'``
          * replace inner '-' by '_': ``'stroke_width'``


        SVG attribute names will be checked, if **debug** is `True`.

        workaround for removed **attribs** parameter in Version 0.2.2::

            # replace
            element = BaseElement(attribs=adict)

            #by
            element = BaseElement()
            element.update(adict)

        """
        # the keyword 'factory' specifies the object creator
        factory = extra.pop('factory', None)
        if factory is not None:
            # take parameter from 'factory'
            self._parameter = factory._parameter
        else:
            # default parameter debug=True profile='full'
            self._parameter = Parameter()

        # override debug setting
        debug = extra.pop('debug', None)
        if debug is not None:
            self._parameter.debug = debug

        # override profile setting
        profile = extra.pop('profile', None)
        if profile is not None:
            self._parameter.profile = profile

        self.attribs = dict()
        self.update(extra)
        self.elements = list()

    def update(self, attribs):
        """ Update SVG Attributes from `dict` attribs.

        Rules for keys:

        1. trailing '_' will be removed (``'class_'`` -> ``'class'``)
        2. inner '_' will be replaced by '-' (``'stroke_width'`` -> ``'stroke-width'``)

        """
        for key, value in attribs.items():
            # remove trailing underscores
            # and replace inner underscores
            key = key.rstrip('_').replace('_', '-')
            self.__setitem__(key, value)

    def copy(self):
        newobj = copy.copy(self)  # shallow copy of object
        newobj.attribs = copy.copy(self.attribs)  # shallow copy of attributes
        newobj.elements = copy.copy(self.elements)  # shallow copy of subelements
        if 'id' in newobj.attribs:  # create a new 'id'
            newobj['id'] = newobj.next_id()
        return newobj

    @property
    def debug(self):
        return self._parameter.debug

    @property
    def profile(self):
        return self._parameter.profile

    @property
    def validator(self):
        return self._parameter.validator

    @validator.setter
    def validator(self, value):
        self._parameter.validator = value

    @property
    def version(self):
        return self._parameter.get_version()

    def set_parameter(self, parameter):
        self._parameter = parameter

    def next_id(self, value=None):
        return AutoID.next_id(value)

    def get_id(self):
        """ Get the object `id` string, if the object does not have an `id`,
        a new `id` will be created.

        :returns: `string`
        """
        if 'id' not in self.attribs:
            self.attribs['id'] = self.next_id()
        return self.attribs['id']

    def get_iri(self):
        """
        Get the `IRI` reference string of the object. (i.e., ``'#id'``).

        :returns: `string`
        """
        return "#%s" % self.get_id()

    def get_funciri(self):
        """
        Get the `FuncIRI` reference string of the object. (i.e. ``'url(#id)'``).

        :returns: `string`
        """
        return "url(%s)" % self.get_iri()

    def __getitem__(self, key):
        """ Get SVG attribute by `key`.

        :param string key: SVG attribute name
        :return: SVG attribute value

        """
        return self.attribs[key]

    def __setitem__(self, key, value):
        """ Set SVG attribute by `key` to `value`.

        :param string key: SVG attribute name
        :param object value: SVG attribute value

        """
        # Attribute checking is only done by using the __setitem__() method or
        # by self['attribute'] = value
        if self.debug:
            self.validator.check_svg_attribute_value(self.elementname, key, value)
        self.attribs[key] = value

    def add(self, element):
        """ Add an SVG element as subelement.

        :param element: append this SVG element
        :returns: the added element

        """
        if self.debug:
            self.validator.check_valid_children(self.elementname, element.elementname)
        self.elements.append(element)
        return element

    def tostring(self):
        """ Get the XML representation as unicode `string`.

        :return: unicode XML string of this object and all its subelements

        """
        xml = self.get_xml()
        # required for Python 2 support
        xml_utf8_str = etree.tostring(xml, encoding='utf-8')
        return xml_utf8_str.decode('utf-8')
        # just Python 3: return etree.tostring(xml, encoding='unicode')
    
    def _repr_svg_(self):
        """ Show SVG in IPython, Jupyter Notebook, and Jupyter Lab

        :return: unicode XML string of this object and all its subelements

        """
        return self.tostring()

    def get_xml(self):
        """ Get the XML representation as `ElementTree` object.

        :return: XML `ElementTree` of this object and all its subelements

        """
        xml = etree.Element(self.elementname)
        if self.debug:
            self.validator.check_all_svg_attribute_values(self.elementname, self.attribs)
        for attribute, value in sorted(self.attribs.items()):
            # filter 'None' values
            if value is not None:
                value = self.value_to_string(value)
                if value:  # just add not empty attributes
                    xml.set(attribute, value)

        for element in self.elements:
            xml.append(element.get_xml())
        return xml

    def value_to_string(self, value):
        """
        Converts *value* into a <string> includes a value check, depending
        on :attr:`self.debug` and :attr:`self.profile`.

        """
        if isinstance(value, (int, float)):
            if self.debug:
                self.validator.check_svg_type(value, 'number')
            if isinstance(value, float) and self.profile == 'tiny':
                value = round(value, 4)
        return str(value)

    def set_desc(self, title=None, desc=None):
        """ Insert a **title** and/or a **desc** element as first subelement.
        """
        if desc is not None:
            self.elements.insert(0, Desc(desc))
        if title is not None:
            self.elements.insert(0, Title(title))

    def set_metadata(self, xmldata):
        """
        :param xmldata: an xml.etree.ElementTree - Element() object.
        """
        metadata = Metadata(xmldata)
        if len(self.elements) == 0:
            self.elements.append(metadata)
        else:
            pos = 0
            while self.elements[pos].elementname in ('title', 'desc'):
                pos += 1
                if pos == len(self.elements):
                    self.elements.append(metadata)
                    return
            if self.elements[pos].elementname == 'metadata':
                self.elements[pos].xml.append(xmldata)
            else:
                self.elements.insert(pos, metadata)


class Title(object):
    elementname = 'title'

    def __init__(self, text):
        self.xml = etree.Element(self.elementname)
        self.xml.text = str(text)

    def get_xml(self):
        return self.xml


class Desc(Title):
    elementname = 'desc'


class Metadata(Title):
    elementname = 'metadata'

    def __init__(self, xmldata):
        """
        :param xmldata: an xml.etree.ElementTree - Element() object.
        """
        self.xml = etree.Element('metadata')
        self.xml.append(xmldata)
