#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: svg types
# Created: 30.09.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License


class SVGAttribute(object):
    def __init__(self, name, anim, types, const):
        self.name = name
        self._anim = anim
        self._types = types
        self._const = const

    # 'elementname' is ignored, but necessary because of the signatures of
    # the SVGMultiAttribute class methods get_...()

    def get_anim(self, elementname='*'):
        return self._anim

    def get_types(self, elementname='*'):
        return self._types

    def get_const(self, elementname='*'):
        return self._const


class SVGMultiAttribute(object):
    # example: SVGMultiAttribute({'*':SVGAttribute(...), 'text tref':SVGAttribute(...)} )
    # parametr is a dict-like object
    # '*' is the default attribute definition
    # 'text' and 'tref' share the same attribute definition

    def __init__(self, attributes):
        self.name = None
        self._attributes = {}

        for names, attribute in attributes.items():
            for name in names.split():
                name = name.strip()
                self._attributes[name] = attribute
                if not self.name:
                    self.name = attribute.name
                elif self.name != attribute.name:
                    raise ValueError("Different attribute-names for SVGMultiAttribute "\
                                     "(%s != %s)." % (self.name, attribute.name))

        if '*' not in self._attributes and len(self._attributes):
            # if no default attribute definition were given
            # set the first attribute definition as the default attribute definition
            firstkey = sorted(self._attributes.keys())[0]
            self._attributes['*'] = self._attributes[firstkey]

    def get_attribute(self, elementname):
        if elementname in self._attributes:
            return self._attributes[elementname]
        else:
            return self._attributes['*']

    def get_anim(self, elementname='*'):
        attribute = self.get_attribute(elementname)
        return attribute.get_anim()

    def get_types(self, elementname='*'):
        attribute = self.get_attribute(elementname)
        return attribute.get_types()

    def get_const(self, elementname='*'):
        attribute = self.get_attribute(elementname)
        return attribute.get_const()


class SVGElement(object):
    def __init__(self, name, attributes, properties, children):
        self.name = name
        s = set(attributes)
        s.update(properties)
        self.valid_attributes = frozenset(s)
        self.valid_children = frozenset(children)
