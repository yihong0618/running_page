#coding:utf-8
# Author:  mozman
# Purpose: svg container classes
# Created: 15.09.2010
# Copyright (C) 2010, Manfred Moitzi
# License: MIT License
"""
The **container** module provides following structural objects:

* :class:`svgwrite.Group`
* :class:`svgwrite.SVG`
* :class:`svgwrite.Defs`
* :class:`svgwrite.Symbol`
* :class:`svgwrite.Marker`
* :class:`svgwrite.Use`
* :class:`svgwrite.Hyperlink`
* :class:`svgwrite.Script`
* :class:`svgwrite.Style`

set/get SVG attributes::

    element['attribute'] = value
    value = element['attribute']

"""
from urllib.request import urlopen
from svgwrite.utils import font_mimetype, base64_data, find_first_url
from svgwrite.base import BaseElement
from svgwrite.mixins import ViewBox, Transform, XLink
from svgwrite.mixins import Presentation, Clipping
from svgwrite.etree import CDATA


class Group(BaseElement, Transform, Presentation):
    """ The **Group** (SVG **g**) element is a container element for grouping
    together related graphics elements.

    Grouping constructs, when used in conjunction with the **desc** and **title**
    elements, provide information about document structure and semantics.
    Documents that are rich in structure may be rendered graphically, as speech,
    or as braille, and thus promote accessibility.

    A group of elements, as well as individual objects, can be given a name using
    the **id** attribute. Named groups are needed for several purposes such as
    animation and re-usable objects.

    """
    elementname = 'g'


class Defs(Group):
    """ The **defs** element is a container element for referenced elements. For
    understandability and accessibility reasons, it is recommended that, whenever
    possible, referenced elements be defined inside of a **defs**.
    """
    elementname = 'defs'


class Symbol(BaseElement, ViewBox, Presentation, Clipping):
    """ The **symbol** element is used to define graphical template objects which
    can be instantiated by a **use** element. The use of **symbol** elements for
    graphics that are used multiple times in the same document adds structure and
    semantics. Documents that are rich in structure may be rendered graphically,
    as speech, or as braille, and thus promote accessibility.
    """
    # ITransform interface is not valid for Symbol -> do not inherit from Group
    elementname = 'symbol'


class Marker(BaseElement, ViewBox, Presentation):
    """ The **marker** element defines the graphics that is to be used for
    drawing arrowheads or polymarkers on a given **path**, **line**, **polyline**
    or **polygon** element.

    Add Marker definitions to a **defs** section, preferred to the **defs** section
    of the **main drawing**.

    """
    elementname = 'marker'

    def __init__(self, insert=None, size=None, orient=None, **extra):
        """
        :param 2-tuple insert: reference point (**refX**, **refY**)
        :param 2-tuple size: (**markerWidth**, **markerHeight**)
        :param orient: ``'auto'`` | `angle`
        :param extra: additional SVG attributes as keyword-arguments
        """
        super(Marker, self).__init__(**extra)
        if insert is not None:
            self['refX'] = insert[0]
            self['refY'] = insert[1]
        if size is not None:
            self['markerWidth'] = size[0]
            self['markerHeight'] = size[1]
        if orient is not None:
            self['orient'] = orient
        if 'id' not in self.attribs:  # an 'id' is necessary
            self['id'] = self.next_id()


FONT_TEMPLATE = """@font-face{{ 
    font-family: "{name}"; 
    src: url("{data}"); 
}}
"""


class SVG(Symbol):
    """ A SVG document fragment consists of any number of SVG elements contained
    within an **svg** element.

    An SVG document fragment can range from an empty fragment (i.e., no content
    inside of the **svg** element), to a very simple SVG document fragment containing
    a single SVG graphics element such as a **rect**, to a complex, deeply nested
    collection of container elements and graphics elements.
    """
    elementname = 'svg'

    def __init__(self, insert=None, size=None, **extra):
        """
        :param 2-tuple insert: insert position (**x**, **y**)
        :param 2-tuple size: (**width**, **height**)
        :param extra: additional SVG attributes as keyword-arguments
        """
        super(SVG, self).__init__(**extra)
        if insert is not None:
            self['x'] = insert[0]
            self['y'] = insert[1]
        if size is not None:
            self['width'] = size[0]
            self['height'] = size[1]

        self.defs = Defs(factory=self)  # defs container
        self.add(self.defs)  # add defs as first element

    def embed_stylesheet(self, content):
        """ Add <style> tag to the defs section.

        :param content: style sheet content as string
        :return: :class:`~svgwrite.container.Style` object
        """
        return self.defs.add(Style(content))

    def embed_font(self, name, filename):
        """ Embed font as base64 encoded data from font file.

        :param name: font name
        :param filename: file name of local stored font
        """
        data = open(filename, 'rb').read()
        self._embed_font_data(name, data, font_mimetype(filename))

    def embed_google_web_font(self, name, uri):
        """ Embed font as base64 encoded data acquired from google fonts.

        :param name: font name
        :param uri: google fonts request uri like 'http://fonts.googleapis.com/css?family=Indie+Flower'
        """
        font_info = urlopen(uri).read()
        font_url = find_first_url(font_info.decode())
        if font_url is None:
            raise ValueError("Got no font data from uri: '{}'".format(uri))
        else:
            data = urlopen(font_url).read()
            self._embed_font_data(name, data, font_mimetype(font_url))

    def _embed_font_data(self, name, data, mimetype):
        content = FONT_TEMPLATE.format(name=name, data=base64_data(data, mimetype))
        self.embed_stylesheet(content)


class Use(BaseElement, Transform, XLink, Presentation):
    """ The **use** element references another element and indicates that the graphical
    contents of that element is included/drawn at that given point in the document.

    Link to objects by href = ``'#object-id'`` or use the object itself as
    href-argument, if the given element has no **id** attribute it gets an
    automatic generated id.

    """
    elementname = 'use'

    def __init__(self, href, insert=None, size=None, **extra):
        """
        :param string href: object link (id-string) or an object with an id-attribute
        :param 2-tuple insert: insert point (**x**, **y**)
        :param 2-tuple size: (**width**, **height**)
        :param extra: additional SVG attributes as keyword-arguments
        """
        super(Use, self).__init__(**extra)
        self.set_href(href)
        if insert is not None:
            self['x'] = insert[0]
            self['y'] = insert[1]
        if size is not None:
            self['width'] = size[0]
            self['height'] = size[1]

    def get_xml(self):
        self.update_id()  # if href is an object - 'id' - attribute may be changed!
        return super(Use, self).get_xml()


class Hyperlink(BaseElement, Transform, Presentation):
    """ The **a** element indicate links (also known as Hyperlinks or Web links).

    The remote resource (the destination for the link) is defined by a `<URI>`
    specified by the XLink **xlink:href** attribute. The remote resource may be
    any Web resource (e.g., an image, a video clip, a sound bite, a program,
    another SVG document, an HTML document, an element within the current
    document, an element within a different document, etc.). By activating
    these links (by clicking with the mouse, through keyboard input, voice
    commands, etc.), users may visit these resources.

    A **Hyperlink** is defined for each separate rendered element
    contained within the **Hyperlink** class; add sublements as usual with
    the `add` method.

    """
    elementname = 'a'

    def __init__(self, href, target='_blank', **extra):
        """
        :param string href: hyperlink to the target resource
        :param string target: ``'_blank|_replace|_self|_parent|_top|<XML-name>'``
        :param extra: additional SVG attributes as keyword-arguments
        """
        super(Hyperlink, self).__init__(**extra)
        self['xlink:href'] = href
        if target is not None:
            self['target'] = target


class Script(BaseElement):
    """ The **script** element indicate links to a client-side language.  This
    is normally a  (also known as Hyperlinks or Web links).

    The remote resource (the source of the script) is defined by a `<URI>`
    specified by the XLink **xlink:href** attribute. The remote resource must
    be a text-file that contains the script contents.  This script can be used
    within the SVG file by catching events or adding the mouseover/mousedown/
    mouseup elements to the markup.

    """
    elementname = 'script'

    def __init__(self, href=None, content="", **extra):
        """
        :param string href: hyperlink to the target resource or *None* if using *content*
        :param string content: script content
        :param extra: additional attributes as keyword-arguments

        Use *href* **or** *content*, but not both at the same time.

        """
        # removed type parameter, default is "application/ecmascript"
        super(Script, self).__init__(**extra)
        if href is not None:
            self['xlink:href'] = href
        self._content = content

    def get_xml(self):
        xml = super(Script, self).get_xml()
        if self._content:
            xml.append(CDATA(self._content))
        return xml

    def append(self, content):
        """ Append content to the existing element-content. """
        self._content += content


class Style(Script):
    """ The *style* element allows style sheets to be embedded directly within
    SVG content. SVG's *style* element has the same attributes as the
    corresponding element in HTML.

    """
    elementname = 'style'

    def __init__(self, content="", **extra):
        """
        :param string content: stylesheet content
        """
        super(Style, self).__init__(content=content, **extra)
        self['type'] = "text/css"

