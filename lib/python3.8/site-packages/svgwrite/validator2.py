#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: validator2 module - new validator module
# Created: 01.10.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License

from svgwrite.data import full11
from svgwrite.data import tiny12
from svgwrite.data import pattern

validator_cache = {}


def cache_key(profile, debug):
    return str(profile) + str(debug)


def get_validator(profile, debug=True):
    """ Validator factory """
    try:
        return validator_cache[cache_key(profile, debug)]
    except KeyError:
        if profile == 'tiny':
            validator = Tiny12Validator(debug)
        elif profile in ('full', 'basic', 'none'):
            validator = Full11Validator(debug)
        else:
            raise ValueError("Unsupported profile: '%s'" % profile)
        validator_cache[cache_key(profile, debug)] = validator
        return validator


class Tiny12Validator(object):
    profilename = "Tiny 1.2"

    def __init__(self, debug=True):
        self.debug = debug
        self.attributes = tiny12.attributes
        self.elements = tiny12.elements
        self.typechecker = tiny12.TypeChecker()

    def check_all_svg_attribute_values(self, elementname, attributes):
        """
        Check if attributes are valid for object 'elementname' and all svg
        attributes have valid types and values.

        Raises ValueError.
        """
        for attributename, value in attributes.items():
            self.check_svg_attribute_value(elementname, attributename, value)

    def check_svg_attribute_value(self, elementname, attributename, value):
        """
        Check if 'attributename' is valid for object 'elementname' and 'value'
        is a valid svg type and value.

        Raises ValueError.
        """
        self._check_valid_svg_attribute_name(elementname, attributename)
        self._check_svg_value(elementname, attributename, value)

    def _check_svg_value(self, elementname, attributename, value):
        """
        Checks if 'value' is a valid svg-type for svg-attribute
        'attributename' at svg-element 'elementname'.

        Raises TypeError.
        """
        attribute = self.attributes[attributename]
        # check if 'value' match a valid datatype
        for typename in attribute.get_types(elementname):
            if self.typechecker.check(typename, value):
                return
        # check if 'value' is a valid constant
        valuestr = str(value)
        if not valuestr in attribute.get_const(elementname):
            raise TypeError("'%s' is not a valid value for attribute '%s' at svg-element <%s>." % (value, attributename, elementname))

    def _check_valid_svg_attribute_name(self, elementname, attributename):
        """ Check if 'attributename' is a valid svg-attribute for svg-element
        'elementname'.

        Raises ValueError.
        """
        if not self.is_valid_svg_attribute(elementname, attributename):
            raise ValueError("Invalid attribute '%s' for svg-element <%s>." % (attributename, elementname))

    def _get_element(self, elementname):
        try:
            return self.elements[elementname]
        except KeyError:
            raise KeyError("<%s> is not valid for selected profile: '%s'." % (elementname, self.profilename))

    def check_svg_type(self, value, typename='string'):
        """
        Check if 'value' matches svg type 'typename'.

        Raises TypeError.
        """
        if self.typechecker.check(typename, value):
            return value
        else:
            raise TypeError("%s is not of type '%s'." % (value, typename))

    def is_valid_svg_type(self, value, typename):
        return self.typechecker.check(typename, value)

    def is_valid_elementname(self, elementname):
        """ True if 'elementname' is a valid svg-element name. """
        return elementname in self.elements

    def is_valid_svg_attribute(self, elementname, attributename):
        """ True if 'attributename' is a valid svg-attribute for svg-element
        'elementname'.
        """
        element = self._get_element(elementname)
        return attributename in element.valid_attributes

    def is_valid_children(self, elementname, childrenname):
        """ True if svg-element 'childrenname' is a valid children of
        svg-element 'elementname'.
        """
        element = self._get_element(elementname)
        return childrenname in element.valid_children

    def check_valid_children(self, elementname, childrenname):
        """ Checks if svg-element 'childrenname' is a valid children of
        svg-element 'elementname'.

        Raises ValueError.
        """
        if not self.is_valid_children(elementname, childrenname):
            raise ValueError("Invalid children '%s' for svg-element <%s>." % (childrenname, elementname))

    def get_coordinate(self, value):
        """ Split value in (number, unit) if value has an unit or (number, None).

        Raises ValueError.
        """

        if value is None:
            raise TypeError("Invalid type 'None'.")
        if isinstance(value, (int, float)):
            result = (value, None)
        else:
            result = pattern.coordinate.match(value.strip())
            if result:
                number, tmp, unit = result.groups()
                number = float(number)
            else:
                raise ValueError("'%s' is not a valid svg-coordinate." % value)
            result = (number, unit)
        if self.typechecker.is_number(result[0]):
            return result
        else:
            version = "SVG %s %s" % self.typechecker.get_version()
            raise ValueError("%s is not a valid number for: %s." % (value, version))
    get_length = get_coordinate


class Full11Validator(Tiny12Validator):
    profilename = "Full 1.1"

    def __init__(self, debug=True):
        self.debug = debug
        self.attributes = full11.attributes
        self.elements = full11.elements
        self.typechecker = full11.TypeChecker()
