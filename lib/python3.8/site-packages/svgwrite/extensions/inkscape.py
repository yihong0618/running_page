# Copyright (c) 2018 Manfred Moitzi
# License: MIT License
# based on work of:
# Copyright (c) 2018 Antonio Ospite <ao2@ao2.it>

from svgwrite.data.types import SVGAttribute

INKSCAPE_NAMESPACE = 'http://www.inkscape.org/namespaces/inkscape'
SODIPODI_NAMESPACE = 'http://sodipodi.sourceforge.net/DTD/sodipodi-0.dtd'
INKSCAPE_ATTRIBUTES = {
    'xmlns:inkscape': SVGAttribute('xmlns:inkscape',
                                   anim=False,
                                   types=[],
                                   const=frozenset([INKSCAPE_NAMESPACE])),
    'xmlns:sodipodi': SVGAttribute('xmlns:sodipodi',
                                   anim=False,
                                   types=[],
                                   const=frozenset([SODIPODI_NAMESPACE])),
    'inkscape:groupmode': SVGAttribute('inkscape:groupmode',
                                       anim=False,
                                       types=[],
                                       const=frozenset(['layer'])),
    'inkscape:label': SVGAttribute('inkscape:label',
                                   anim=False,
                                   types=frozenset(['string']),
                                   const=[]),
    'sodipodi:insensitive': SVGAttribute('sodipodi:insensitive',
                                         anim=False,
                                         types=[],
                                         const=frozenset(['true', 'false', '0', '1']))
}


def _setup_validator(validator):
    # setup already done?
    if 'xmlns:inkscape' in validator.attributes:
        return

    validator.attributes.update(INKSCAPE_ATTRIBUTES)
    elements = validator.elements

    # extend SVG attributes
    elements['svg'].valid_attributes = \
        {
            'xmlns:inkscape',
            'xmlns:sodipodi',
        } | elements['svg'].valid_attributes

    # extend group attributes
    elements['g'].valid_attributes = \
        {
            'inkscape:groupmode',
            'inkscape:label',
            'sodipodi:insensitive',
        } | elements['g'].valid_attributes


GROUP_MODE = 'inkscape:groupmode'
LABEL = 'inkscape:label'
INSENSITIVE = 'sodipodi:insensitive'


class Inkscape(object):
    """
    Extension to support SOME Inkscape features.

    """
    def __init__(self, drawing):
        self.svg = drawing
        _setup_validator(drawing.validator)
        drawing['xmlns:inkscape'] = INKSCAPE_NAMESPACE
        drawing['xmlns:sodipodi'] = SODIPODI_NAMESPACE

    def layer(self, label=None, locked=False, **kwargs):
        """
        Create new Inkscape layer.

        Args:
            label: layer name as string
            locked: when set to True, make objects at this layer unselectable

        """
        new_layer = self.svg.g(**kwargs)
        new_layer[GROUP_MODE] = 'layer'
        if label is not None:
            new_layer[LABEL] = label
        if locked:
            new_layer[INSENSITIVE] = 1
        return new_layer
