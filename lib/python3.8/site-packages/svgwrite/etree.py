#!/usr/bin/env python
#coding:utf-8
# Author:  mozman
# Purpose: a hack to generate XML containing CDATA by ElementTree
# Created: 26.05.2012
# Copyright (C) 2012, Manfred Moitzi
# License: MIT License

# usage:
#
# from svgwrite.etree import etree, CDATA
#
# element = etree.Element('myTag')
# element.append(CDATA("< and >"))
#
# assert etree.tostring(element) == "<myTag><![CDATA[< and >]]></myTag>"


import sys
PY3 = sys.version_info[0] > 2

import xml.etree.ElementTree as etree

CDATA_TPL = "<![CDATA[%s]]>"
CDATA_TAG = CDATA_TPL


def CDATA(text):
    element = etree.Element(CDATA_TAG)
    element.text = text
    return element

original_serialize_xml = etree._serialize_xml

if PY3:
    def _serialize_xml_with_CDATA_support(write, elem, qnames, namespaces, **kwargs):
        if elem.tag == CDATA_TAG:
            write(CDATA_TPL % elem.text)
        else:
            original_serialize_xml(write, elem, qnames, namespaces, **kwargs)
else:
    def _serialize_xml_with_CDATA_support(write, elem, encoding, qnames, namespaces):
        if elem.tag == CDATA_TAG:
            write(CDATA_TPL % elem.text.encode(encoding))
        else:
            original_serialize_xml(write, elem, encoding, qnames, namespaces)

# ugly, ugly, ugly patching
etree._serialize_xml = _serialize_xml_with_CDATA_support
