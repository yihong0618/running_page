#!/usr/bin/env python
#coding:utf-8
# Author:  mozman --<mozman@gmx.at>
# Purpose: element factory
# Created: 15.10.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License

from svgwrite import container
from svgwrite import shapes
from svgwrite import path
from svgwrite import image
from svgwrite import text
from svgwrite import gradients
from svgwrite import pattern
from svgwrite import masking
from svgwrite import animate
from svgwrite import filters
from svgwrite import solidcolor

factoryelements = {
    'g': container.Group,
    'svg': container.SVG,
    'defs': container.Defs,
    'symbol': container.Symbol,
    'marker': container.Marker,
    'use': container.Use,
    'a': container.Hyperlink,
    'script': container.Script,
    'style': container.Style,
    'line': shapes.Line,
    'rect': shapes.Rect,
    'circle': shapes.Circle,
    'ellipse': shapes.Ellipse,
    'polyline': shapes.Polyline,
    'polygon': shapes.Polygon,
    'path': path.Path,
    'image': image.Image,
    'text': text.Text,
    'tspan': text.TSpan,
    'tref': text.TRef,
    'textPath': text.TextPath,
    'textArea': text.TextArea,
    'linearGradient': gradients.LinearGradient,
    'radialGradient': gradients.RadialGradient,
    'pattern': pattern.Pattern,
    'solidColor': solidcolor.SolidColor,
    'clipPath': masking.ClipPath,
    'mask': masking.Mask,
    'animate': animate.Animate,
    'set': animate.Set,
    'animateColor': animate.AnimateColor,
    'animateMotion': animate.AnimateMotion,
    'animateTransform': animate.AnimateTransform,
    'filter': filters.Filter,
}


class ElementBuilder(object):
    def __init__(self, cls, factory):
        self.cls = cls
        self.factory = factory

    def __call__(self, *args, **kwargs):
        # inject creator object - inherit _parameter from factory
        kwargs['factory'] = self.factory
        # create an object of type 'cls'
        return self.cls(*args, **kwargs)


class ElementFactory(object):
    def __getattr__(self, name):
        if name in factoryelements:
            return ElementBuilder(factoryelements[name], self)
        else:
            raise AttributeError("'%s' has no attribute '%s'" % (self.__class__.__name__, name))
