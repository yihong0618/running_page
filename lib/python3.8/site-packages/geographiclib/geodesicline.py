"""Define the :class:`~geographiclib.geodesicline.GeodesicLine` class

The constructor defines the starting point of the line.  Points on the
line are given by

  * :meth:`~geographiclib.geodesicline.GeodesicLine.Position` position
    given in terms of distance
  * :meth:`~geographiclib.geodesicline.GeodesicLine.ArcPosition` position
    given in terms of spherical arc length

A reference point 3 can be defined with

  * :meth:`~geographiclib.geodesicline.GeodesicLine.SetDistance` set
    position of 3 in terms of the distance from the starting point
  * :meth:`~geographiclib.geodesicline.GeodesicLine.SetArc` set
    position of 3 in terms of the spherical arc length from the starting point

The object can also be constructed by

  * :meth:`Geodesic.Line <geographiclib.geodesic.Geodesic.Line>`
  * :meth:`Geodesic.DirectLine <geographiclib.geodesic.Geodesic.DirectLine>`
  * :meth:`Geodesic.ArcDirectLine
    <geographiclib.geodesic.Geodesic.ArcDirectLine>`
  * :meth:`Geodesic.InverseLine <geographiclib.geodesic.Geodesic.InverseLine>`

The public attributes for this class are

  * :attr:`~geographiclib.geodesicline.GeodesicLine.a`
    :attr:`~geographiclib.geodesicline.GeodesicLine.f`
    :attr:`~geographiclib.geodesicline.GeodesicLine.caps`
    :attr:`~geographiclib.geodesicline.GeodesicLine.lat1`
    :attr:`~geographiclib.geodesicline.GeodesicLine.lon1`
    :attr:`~geographiclib.geodesicline.GeodesicLine.azi1`
    :attr:`~geographiclib.geodesicline.GeodesicLine.salp1`
    :attr:`~geographiclib.geodesicline.GeodesicLine.calp1`
    :attr:`~geographiclib.geodesicline.GeodesicLine.s13`
    :attr:`~geographiclib.geodesicline.GeodesicLine.a13`

"""
# geodesicline.py
#
# This is a rather literal translation of the GeographicLib::GeodesicLine class
# to python.  See the documentation for the C++ class for more information at
#
#    https://geographiclib.sourceforge.io/html/annotated.html
#
# The algorithms are derived in
#
#    Charles F. F. Karney,
#    Algorithms for geodesics, J. Geodesy 87, 43-55 (2013),
#    https://doi.org/10.1007/s00190-012-0578-z
#    Addenda: https://geographiclib.sourceforge.io/geod-addenda.html
#
# Copyright (c) Charles Karney (2011-2019) <charles@karney.com> and licensed
# under the MIT/X11 License.  For more information, see
# https://geographiclib.sourceforge.io/
######################################################################

import math
from geographiclib.geomath import Math
from geographiclib.geodesiccapability import GeodesicCapability

class GeodesicLine(object):
  """Points on a geodesic path"""

  def __init__(self, geod, lat1, lon1, azi1,
               caps = GeodesicCapability.STANDARD |
               GeodesicCapability.DISTANCE_IN,
               salp1 = Math.nan, calp1 = Math.nan):
    """Construct a GeodesicLine object

    :param geod: a :class:`~geographiclib.geodesic.Geodesic` object
    :param lat1: latitude of the first point in degrees
    :param lon1: longitude of the first point in degrees
    :param azi1: azimuth at the first point in degrees
    :param caps: the :ref:`capabilities <outmask>`

    This creates an object allowing points along a geodesic starting at
    (*lat1*, *lon1*), with azimuth *azi1* to be found.  The default
    value of *caps* is STANDARD | DISTANCE_IN.  The optional parameters
    *salp1* and *calp1* should not be supplied; they are part of the
    private interface.

    """

    from geographiclib.geodesic import Geodesic
    self.a = geod.a
    """The equatorial radius in meters (readonly)"""
    self.f = geod.f
    """The flattening (readonly)"""
    self._b = geod._b
    self._c2 = geod._c2
    self._f1 = geod._f1
    self.caps = (caps | Geodesic.LATITUDE | Geodesic.AZIMUTH |
                  Geodesic.LONG_UNROLL)
    """the capabilities (readonly)"""

    # Guard against underflow in salp0
    self.lat1 = Math.LatFix(lat1)
    """the latitude of the first point in degrees (readonly)"""
    self.lon1 = lon1
    """the longitude of the first point in degrees (readonly)"""
    if Math.isnan(salp1) or Math.isnan(calp1):
      self.azi1 = Math.AngNormalize(azi1)
      self.salp1, self.calp1 = Math.sincosd(Math.AngRound(azi1))
    else:
      self.azi1 = azi1
      """the azimuth at the first point in degrees (readonly)"""
      self.salp1 = salp1
      """the sine of the azimuth at the first point (readonly)"""
      self.calp1 = calp1
      """the cosine of the azimuth at the first point (readonly)"""

    # real cbet1, sbet1
    sbet1, cbet1 = Math.sincosd(Math.AngRound(self.lat1)); sbet1 *= self._f1
    # Ensure cbet1 = +epsilon at poles
    sbet1, cbet1 = Math.norm(sbet1, cbet1); cbet1 = max(Geodesic.tiny_, cbet1)
    self._dn1 = math.sqrt(1 + geod._ep2 * Math.sq(sbet1))

    # Evaluate alp0 from sin(alp1) * cos(bet1) = sin(alp0),
    self._salp0 = self.salp1 * cbet1 # alp0 in [0, pi/2 - |bet1|]
    # Alt: calp0 = hypot(sbet1, calp1 * cbet1).  The following
    # is slightly better (consider the case salp1 = 0).
    self._calp0 = math.hypot(self.calp1, self.salp1 * sbet1)
    # Evaluate sig with tan(bet1) = tan(sig1) * cos(alp1).
    # sig = 0 is nearest northward crossing of equator.
    # With bet1 = 0, alp1 = pi/2, we have sig1 = 0 (equatorial line).
    # With bet1 =  pi/2, alp1 = -pi, sig1 =  pi/2
    # With bet1 = -pi/2, alp1 =  0 , sig1 = -pi/2
    # Evaluate omg1 with tan(omg1) = sin(alp0) * tan(sig1).
    # With alp0 in (0, pi/2], quadrants for sig and omg coincide.
    # No atan2(0,0) ambiguity at poles since cbet1 = +epsilon.
    # With alp0 = 0, omg1 = 0 for alp1 = 0, omg1 = pi for alp1 = pi.
    self._ssig1 = sbet1; self._somg1 = self._salp0 * sbet1
    self._csig1 = self._comg1 = (cbet1 * self.calp1
                                 if sbet1 != 0 or self.calp1 != 0 else 1)
    # sig1 in (-pi, pi]
    self._ssig1, self._csig1 = Math.norm(self._ssig1, self._csig1)
    # No need to normalize
    # self._somg1, self._comg1 = Math.norm(self._somg1, self._comg1)

    self._k2 = Math.sq(self._calp0) * geod._ep2
    eps = self._k2 / (2 * (1 + math.sqrt(1 + self._k2)) + self._k2)

    if self.caps & Geodesic.CAP_C1:
      self._A1m1 = Geodesic._A1m1f(eps)
      self._C1a = list(range(Geodesic.nC1_ + 1))
      Geodesic._C1f(eps, self._C1a)
      self._B11 = Geodesic._SinCosSeries(
        True, self._ssig1, self._csig1, self._C1a)
      s = math.sin(self._B11); c = math.cos(self._B11)
      # tau1 = sig1 + B11
      self._stau1 = self._ssig1 * c + self._csig1 * s
      self._ctau1 = self._csig1 * c - self._ssig1 * s
      # Not necessary because C1pa reverts C1a
      #    _B11 = -_SinCosSeries(true, _stau1, _ctau1, _C1pa)

    if self.caps & Geodesic.CAP_C1p:
      self._C1pa = list(range(Geodesic.nC1p_ + 1))
      Geodesic._C1pf(eps, self._C1pa)

    if self.caps & Geodesic.CAP_C2:
      self._A2m1 = Geodesic._A2m1f(eps)
      self._C2a = list(range(Geodesic.nC2_ + 1))
      Geodesic._C2f(eps, self._C2a)
      self._B21 = Geodesic._SinCosSeries(
        True, self._ssig1, self._csig1, self._C2a)

    if self.caps & Geodesic.CAP_C3:
      self._C3a = list(range(Geodesic.nC3_))
      geod._C3f(eps, self._C3a)
      self._A3c = -self.f * self._salp0 * geod._A3f(eps)
      self._B31 = Geodesic._SinCosSeries(
        True, self._ssig1, self._csig1, self._C3a)

    if self.caps & Geodesic.CAP_C4:
      self._C4a = list(range(Geodesic.nC4_))
      geod._C4f(eps, self._C4a)
      # Multiplier = a^2 * e^2 * cos(alpha0) * sin(alpha0)
      self._A4 = Math.sq(self.a) * self._calp0 * self._salp0 * geod._e2
      self._B41 = Geodesic._SinCosSeries(
        False, self._ssig1, self._csig1, self._C4a)
    self.s13 = Math.nan
    """the distance between point 1 and point 3 in meters (readonly)"""
    self.a13 = Math.nan
    """the arc length between point 1 and point 3 in degrees (readonly)"""

  # return a12, lat2, lon2, azi2, s12, m12, M12, M21, S12
  def _GenPosition(self, arcmode, s12_a12, outmask):
    """Private: General solution of position along geodesic"""
    from geographiclib.geodesic import Geodesic
    a12 = lat2 = lon2 = azi2 = s12 = m12 = M12 = M21 = S12 = Math.nan
    outmask &= self.caps & Geodesic.OUT_MASK
    if not (arcmode or
            (self.caps & (Geodesic.OUT_MASK & Geodesic.DISTANCE_IN))):
      # Uninitialized or impossible distance calculation requested
      return a12, lat2, lon2, azi2, s12, m12, M12, M21, S12

    # Avoid warning about uninitialized B12.
    B12 = 0.0; AB1 = 0.0
    if arcmode:
      # Interpret s12_a12 as spherical arc length
      sig12 = math.radians(s12_a12)
      ssig12, csig12 = Math.sincosd(s12_a12)
    else:
      # Interpret s12_a12 as distance
      tau12 = s12_a12 / (self._b * (1 + self._A1m1))
      tau12 = tau12 if Math.isfinite(tau12) else Math.nan
      s = math.sin(tau12); c = math.cos(tau12)
      # tau2 = tau1 + tau12
      B12 = - Geodesic._SinCosSeries(True,
                                    self._stau1 * c + self._ctau1 * s,
                                    self._ctau1 * c - self._stau1 * s,
                                    self._C1pa)
      sig12 = tau12 - (B12 - self._B11)
      ssig12 = math.sin(sig12); csig12 = math.cos(sig12)
      if abs(self.f) > 0.01:
        # Reverted distance series is inaccurate for |f| > 1/100, so correct
        # sig12 with 1 Newton iteration.  The following table shows the
        # approximate maximum error for a = WGS_a() and various f relative to
        # GeodesicExact.
        #     erri = the error in the inverse solution (nm)
        #     errd = the error in the direct solution (series only) (nm)
        #     errda = the error in the direct solution (series + 1 Newton) (nm)
        #
        #       f     erri  errd errda
        #     -1/5    12e6 1.2e9  69e6
        #     -1/10  123e3  12e6 765e3
        #     -1/20   1110 108e3  7155
        #     -1/50  18.63 200.9 27.12
        #     -1/100 18.63 23.78 23.37
        #     -1/150 18.63 21.05 20.26
        #      1/150 22.35 24.73 25.83
        #      1/100 22.35 25.03 25.31
        #      1/50  29.80 231.9 30.44
        #      1/20   5376 146e3  10e3
        #      1/10  829e3  22e6 1.5e6
        #      1/5   157e6 3.8e9 280e6
        ssig2 = self._ssig1 * csig12 + self._csig1 * ssig12
        csig2 = self._csig1 * csig12 - self._ssig1 * ssig12
        B12 = Geodesic._SinCosSeries(True, ssig2, csig2, self._C1a)
        serr = ((1 + self._A1m1) * (sig12 + (B12 - self._B11)) -
                s12_a12 / self._b)
        sig12 = sig12 - serr / math.sqrt(1 + self._k2 * Math.sq(ssig2))
        ssig12 = math.sin(sig12); csig12 = math.cos(sig12)
        # Update B12 below

    # real omg12, lam12, lon12
    # real ssig2, csig2, sbet2, cbet2, somg2, comg2, salp2, calp2
    # sig2 = sig1 + sig12
    ssig2 = self._ssig1 * csig12 + self._csig1 * ssig12
    csig2 = self._csig1 * csig12 - self._ssig1 * ssig12
    dn2 = math.sqrt(1 + self._k2 * Math.sq(ssig2))
    if outmask & (
      Geodesic.DISTANCE | Geodesic.REDUCEDLENGTH | Geodesic.GEODESICSCALE):
      if arcmode or abs(self.f) > 0.01:
        B12 = Geodesic._SinCosSeries(True, ssig2, csig2, self._C1a)
      AB1 = (1 + self._A1m1) * (B12 - self._B11)
    # sin(bet2) = cos(alp0) * sin(sig2)
    sbet2 = self._calp0 * ssig2
    # Alt: cbet2 = hypot(csig2, salp0 * ssig2)
    cbet2 = math.hypot(self._salp0, self._calp0 * csig2)
    if cbet2 == 0:
      # I.e., salp0 = 0, csig2 = 0.  Break the degeneracy in this case
      cbet2 = csig2 = Geodesic.tiny_
    # tan(alp0) = cos(sig2)*tan(alp2)
    salp2 = self._salp0; calp2 = self._calp0 * csig2 # No need to normalize

    if outmask & Geodesic.DISTANCE:
      s12 = self._b * ((1 + self._A1m1) * sig12 + AB1) if arcmode else s12_a12

    if outmask & Geodesic.LONGITUDE:
      # tan(omg2) = sin(alp0) * tan(sig2)
      somg2 = self._salp0 * ssig2; comg2 = csig2 # No need to normalize
      E = Math.copysign(1, self._salp0)          # East or west going?
      # omg12 = omg2 - omg1
      omg12 = (E * (sig12
                    - (math.atan2(          ssig2,       csig2) -
                       math.atan2(    self._ssig1, self._csig1))
                    + (math.atan2(E *       somg2,       comg2) -
                       math.atan2(E * self._somg1, self._comg1)))
               if outmask & Geodesic.LONG_UNROLL
               else math.atan2(somg2 * self._comg1 - comg2 * self._somg1,
                               comg2 * self._comg1 + somg2 * self._somg1))
      lam12 = omg12 + self._A3c * (
        sig12 + (Geodesic._SinCosSeries(True, ssig2, csig2, self._C3a)
                 - self._B31))
      lon12 = math.degrees(lam12)
      lon2 = (self.lon1 + lon12 if outmask & Geodesic.LONG_UNROLL else
              Math.AngNormalize(Math.AngNormalize(self.lon1) +
                                Math.AngNormalize(lon12)))

    if outmask & Geodesic.LATITUDE:
      lat2 = Math.atan2d(sbet2, self._f1 * cbet2)

    if outmask & Geodesic.AZIMUTH:
      azi2 = Math.atan2d(salp2, calp2)

    if outmask & (Geodesic.REDUCEDLENGTH | Geodesic.GEODESICSCALE):
      B22 = Geodesic._SinCosSeries(True, ssig2, csig2, self._C2a)
      AB2 = (1 + self._A2m1) * (B22 - self._B21)
      J12 = (self._A1m1 - self._A2m1) * sig12 + (AB1 - AB2)
      if outmask & Geodesic.REDUCEDLENGTH:
        # Add parens around (_csig1 * ssig2) and (_ssig1 * csig2) to ensure
        # accurate cancellation in the case of coincident points.
        m12 = self._b * ((      dn2 * (self._csig1 * ssig2) -
                          self._dn1 * (self._ssig1 * csig2))
                         - self._csig1 * csig2 * J12)
      if outmask & Geodesic.GEODESICSCALE:
        t = (self._k2 * (ssig2 - self._ssig1) *
             (ssig2 + self._ssig1) / (self._dn1 + dn2))
        M12 = csig12 + (t * ssig2 - csig2 * J12) * self._ssig1 / self._dn1
        M21 = csig12 - (t * self._ssig1 - self._csig1 * J12) * ssig2 / dn2

    if outmask & Geodesic.AREA:
      B42 = Geodesic._SinCosSeries(False, ssig2, csig2, self._C4a)
      # real salp12, calp12
      if self._calp0 == 0 or self._salp0 == 0:
        # alp12 = alp2 - alp1, used in atan2 so no need to normalize
        salp12 = salp2 * self.calp1 - calp2 * self.salp1
        calp12 = calp2 * self.calp1 + salp2 * self.salp1
      else:
        # tan(alp) = tan(alp0) * sec(sig)
        # tan(alp2-alp1) = (tan(alp2) -tan(alp1)) / (tan(alp2)*tan(alp1)+1)
        # = calp0 * salp0 * (csig1-csig2) / (salp0^2 + calp0^2 * csig1*csig2)
        # If csig12 > 0, write
        #   csig1 - csig2 = ssig12 * (csig1 * ssig12 / (1 + csig12) + ssig1)
        # else
        #   csig1 - csig2 = csig1 * (1 - csig12) + ssig12 * ssig1
        # No need to normalize
        salp12 = self._calp0 * self._salp0 * (
          self._csig1 * (1 - csig12) + ssig12 * self._ssig1 if csig12 <= 0
          else ssig12 * (self._csig1 * ssig12 / (1 + csig12) + self._ssig1))
        calp12 = (Math.sq(self._salp0) +
                  Math.sq(self._calp0) * self._csig1 * csig2)
      S12 = (self._c2 * math.atan2(salp12, calp12) +
             self._A4 * (B42 - self._B41))

    a12 = s12_a12 if arcmode else math.degrees(sig12)
    return a12, lat2, lon2, azi2, s12, m12, M12, M21, S12

  def Position(self, s12, outmask = GeodesicCapability.STANDARD):
    """Find the position on the line given *s12*

    :param s12: the distance from the first point to the second in
      meters
    :param outmask: the :ref:`output mask <outmask>`
    :return: a :ref:`dict`

    The default value of *outmask* is STANDARD, i.e., the *lat1*,
    *lon1*, *azi1*, *lat2*, *lon2*, *azi2*, *s12*, *a12* entries are
    returned.  The :class:`~geographiclib.geodesicline.GeodesicLine`
    object must have been constructed with the DISTANCE_IN capability.

    """

    from geographiclib.geodesic import Geodesic
    result = {'lat1': self.lat1,
              'lon1': self.lon1 if outmask & Geodesic.LONG_UNROLL else
              Math.AngNormalize(self.lon1),
              'azi1': self.azi1, 's12': s12}
    a12, lat2, lon2, azi2, s12, m12, M12, M21, S12 = self._GenPosition(
      False, s12, outmask)
    outmask &= Geodesic.OUT_MASK
    result['a12'] = a12
    if outmask & Geodesic.LATITUDE: result['lat2'] = lat2
    if outmask & Geodesic.LONGITUDE: result['lon2'] = lon2
    if outmask & Geodesic.AZIMUTH: result['azi2'] = azi2
    if outmask & Geodesic.REDUCEDLENGTH: result['m12'] = m12
    if outmask & Geodesic.GEODESICSCALE:
      result['M12'] = M12; result['M21'] = M21
    if outmask & Geodesic.AREA: result['S12'] = S12
    return result

  def ArcPosition(self, a12, outmask = GeodesicCapability.STANDARD):
    """Find the position on the line given *a12*

    :param a12: spherical arc length from the first point to the second
      in degrees
    :param outmask: the :ref:`output mask <outmask>`
    :return: a :ref:`dict`

    The default value of *outmask* is STANDARD, i.e., the *lat1*,
    *lon1*, *azi1*, *lat2*, *lon2*, *azi2*, *s12*, *a12* entries are
    returned.

    """

    from geographiclib.geodesic import Geodesic
    result = {'lat1': self.lat1,
              'lon1': self.lon1 if outmask & Geodesic.LONG_UNROLL else
              Math.AngNormalize(self.lon1),
              'azi1': self.azi1, 'a12': a12}
    a12, lat2, lon2, azi2, s12, m12, M12, M21, S12 = self._GenPosition(
      True, a12, outmask)
    outmask &= Geodesic.OUT_MASK
    if outmask & Geodesic.DISTANCE: result['s12'] = s12
    if outmask & Geodesic.LATITUDE: result['lat2'] = lat2
    if outmask & Geodesic.LONGITUDE: result['lon2'] = lon2
    if outmask & Geodesic.AZIMUTH: result['azi2'] = azi2
    if outmask & Geodesic.REDUCEDLENGTH: result['m12'] = m12
    if outmask & Geodesic.GEODESICSCALE:
      result['M12'] = M12; result['M21'] = M21
    if outmask & Geodesic.AREA: result['S12'] = S12
    return result

  def SetDistance(self, s13):
    """Specify the position of point 3 in terms of distance

    :param s13: distance from point 1 to point 3 in meters

    """

    self.s13 = s13
    self.a13, _, _, _, _, _, _, _, _ = self._GenPosition(False, self.s13, 0)

  def SetArc(self, a13):
    """Specify the position of point 3 in terms of arc length

    :param a13: spherical arc length from point 1 to point 3 in degrees

    """

    from geographiclib.geodesic import Geodesic
    self.a13 = a13
    _, _, _, _, self.s13, _, _, _, _ = self._GenPosition(True, self.a13,
                                                         Geodesic.DISTANCE)
