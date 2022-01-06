"""geodesiccapability.py: capability constants for geodesic{,line}.py"""
# geodesiccapability.py
#
# This gathers the capability constants need by geodesic.py and
# geodesicline.py.  See the documentation for the GeographicLib::Geodesic class
# for more information at
#
#    https://geographiclib.sourceforge.io/html/annotated.html
#
# Copyright (c) Charles Karney (2011-2014) <charles@karney.com> and licensed
# under the MIT/X11 License.  For more information, see
# https://geographiclib.sourceforge.io/
######################################################################

class GeodesicCapability(object):
  """
  Capability constants shared between Geodesic and GeodesicLine.
  """

  CAP_NONE = 0
  CAP_C1   = 1 << 0
  CAP_C1p  = 1 << 1
  CAP_C2   = 1 << 2
  CAP_C3   = 1 << 3
  CAP_C4   = 1 << 4
  CAP_ALL  = 0x1F
  CAP_MASK = CAP_ALL
  OUT_ALL  = 0x7F80
  OUT_MASK = 0xFF80             # Includes LONG_UNROLL
  EMPTY         = 0
  LATITUDE      = 1 << 7  | CAP_NONE
  LONGITUDE     = 1 << 8  | CAP_C3
  AZIMUTH       = 1 << 9  | CAP_NONE
  DISTANCE      = 1 << 10 | CAP_C1
  STANDARD      = LATITUDE | LONGITUDE | AZIMUTH | DISTANCE
  DISTANCE_IN   = 1 << 11 | CAP_C1 | CAP_C1p
  REDUCEDLENGTH = 1 << 12 | CAP_C1 | CAP_C2
  GEODESICSCALE = 1 << 13 | CAP_C1 | CAP_C2
  AREA          = 1 << 14 | CAP_C4
  LONG_UNROLL   = 1 << 15
  ALL           = OUT_ALL | CAP_ALL # Does not include LONG_UNROLL
