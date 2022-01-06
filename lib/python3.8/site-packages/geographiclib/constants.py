"""Define the WGS84 ellipsoid"""
# constants.py
#
# This is a translation of the GeographicLib::Constants class to python.  See
# the documentation for the C++ class for more information at
#
#    https://geographiclib.sourceforge.io/html/annotated.html
#
# Copyright (c) Charles Karney (2011-2016) <charles@karney.com> and
# licensed under the MIT/X11 License.  For more information, see
# https://geographiclib.sourceforge.io/
######################################################################

class Constants(object):
  """
  Constants describing the WGS84 ellipsoid
  """

  WGS84_a = 6378137.0           # meters
  """the equatorial radius in meters of the WGS84 ellipsoid in meters"""
  WGS84_f = 1/298.257223563
  """the flattening of the WGS84 ellipsoid, 1/298.257223563"""
