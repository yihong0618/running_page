"""Define the :class:`~geographiclib.geodesic.Geodesic` class

The ellipsoid parameters are defined by the constructor.  The direct and
inverse geodesic problems are solved by

  * :meth:`~geographiclib.geodesic.Geodesic.Inverse` Solve the inverse
    geodesic problem
  * :meth:`~geographiclib.geodesic.Geodesic.Direct` Solve the direct
    geodesic problem
  * :meth:`~geographiclib.geodesic.Geodesic.ArcDirect` Solve the direct
    geodesic problem in terms of spherical arc length

:class:`~geographiclib.geodesicline.GeodesicLine` objects can be created
with

  * :meth:`~geographiclib.geodesic.Geodesic.Line`
  * :meth:`~geographiclib.geodesic.Geodesic.DirectLine`
  * :meth:`~geographiclib.geodesic.Geodesic.ArcDirectLine`
  * :meth:`~geographiclib.geodesic.Geodesic.InverseLine`

:class:`~geographiclib.polygonarea.PolygonArea` objects can be created
with

  * :meth:`~geographiclib.geodesic.Geodesic.Polygon`

The public attributes for this class are

  * :attr:`~geographiclib.geodesic.Geodesic.a`
    :attr:`~geographiclib.geodesic.Geodesic.f`

*outmask* and *caps* bit masks are

  * :const:`~geographiclib.geodesic.Geodesic.EMPTY`
  * :const:`~geographiclib.geodesic.Geodesic.LATITUDE`
  * :const:`~geographiclib.geodesic.Geodesic.LONGITUDE`
  * :const:`~geographiclib.geodesic.Geodesic.AZIMUTH`
  * :const:`~geographiclib.geodesic.Geodesic.DISTANCE`
  * :const:`~geographiclib.geodesic.Geodesic.STANDARD`
  * :const:`~geographiclib.geodesic.Geodesic.DISTANCE_IN`
  * :const:`~geographiclib.geodesic.Geodesic.REDUCEDLENGTH`
  * :const:`~geographiclib.geodesic.Geodesic.GEODESICSCALE`
  * :const:`~geographiclib.geodesic.Geodesic.AREA`
  * :const:`~geographiclib.geodesic.Geodesic.ALL`
  * :const:`~geographiclib.geodesic.Geodesic.LONG_UNROLL`

:Example:

    >>> from geographiclib.geodesic import Geodesic
    >>> # The geodesic inverse problem
    ... Geodesic.WGS84.Inverse(-41.32, 174.81, 40.96, -5.50)
    {'lat1': -41.32,
     'a12': 179.6197069334283,
     's12': 19959679.26735382,
     'lat2': 40.96,
     'azi2': 18.825195123248392,
     'azi1': 161.06766998615882,
     'lon1': 174.81,
     'lon2': -5.5}

"""
# geodesic.py
#
# This is a rather literal translation of the GeographicLib::Geodesic class to
# python.  See the documentation for the C++ class for more information at
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
# Copyright (c) Charles Karney (2011-2021) <charles@karney.com> and licensed
# under the MIT/X11 License.  For more information, see
# https://geographiclib.sourceforge.io/
######################################################################

import math
from geographiclib.geomath import Math
from geographiclib.constants import Constants
from geographiclib.geodesiccapability import GeodesicCapability

class Geodesic(object):
  """Solve geodesic problems"""

  GEOGRAPHICLIB_GEODESIC_ORDER = 6
  nA1_ = GEOGRAPHICLIB_GEODESIC_ORDER
  nC1_ = GEOGRAPHICLIB_GEODESIC_ORDER
  nC1p_ = GEOGRAPHICLIB_GEODESIC_ORDER
  nA2_ = GEOGRAPHICLIB_GEODESIC_ORDER
  nC2_ = GEOGRAPHICLIB_GEODESIC_ORDER
  nA3_ = GEOGRAPHICLIB_GEODESIC_ORDER
  nA3x_ = nA3_
  nC3_ = GEOGRAPHICLIB_GEODESIC_ORDER
  nC3x_ = (nC3_ * (nC3_ - 1)) // 2
  nC4_ = GEOGRAPHICLIB_GEODESIC_ORDER
  nC4x_ = (nC4_ * (nC4_ + 1)) // 2
  maxit1_ = 20
  maxit2_ = maxit1_ + Math.digits + 10

  tiny_ = math.sqrt(Math.minval)
  tol0_ = Math.epsilon
  tol1_ = 200 * tol0_
  tol2_ = math.sqrt(tol0_)
  tolb_ = tol0_ * tol2_
  xthresh_ = 1000 * tol2_

  CAP_NONE = GeodesicCapability.CAP_NONE
  CAP_C1   = GeodesicCapability.CAP_C1
  CAP_C1p  = GeodesicCapability.CAP_C1p
  CAP_C2   = GeodesicCapability.CAP_C2
  CAP_C3   = GeodesicCapability.CAP_C3
  CAP_C4   = GeodesicCapability.CAP_C4
  CAP_ALL  = GeodesicCapability.CAP_ALL
  CAP_MASK = GeodesicCapability.CAP_MASK
  OUT_ALL  = GeodesicCapability.OUT_ALL
  OUT_MASK = GeodesicCapability.OUT_MASK

  def _SinCosSeries(sinp, sinx, cosx, c):
    """Private: Evaluate a trig series using Clenshaw summation."""
    # Evaluate
    # y = sinp ? sum(c[i] * sin( 2*i    * x), i, 1, n) :
    #            sum(c[i] * cos((2*i+1) * x), i, 0, n-1)
    # using Clenshaw summation.  N.B. c[0] is unused for sin series
    # Approx operation count = (n + 5) mult and (2 * n + 2) add
    k = len(c)                  # Point to one beyond last element
    n = k - sinp
    ar = 2 * (cosx - sinx) * (cosx + sinx) # 2 * cos(2 * x)
    y1 = 0                                 # accumulators for sum
    if n & 1:
      k -= 1; y0 = c[k]
    else:
      y0 = 0
    # Now n is even
    n = n // 2
    while n:                    # while n--:
      n -= 1
      # Unroll loop x 2, so accumulators return to their original role
      k -= 1; y1 = ar * y0 - y1 + c[k]
      k -= 1; y0 = ar * y1 - y0 + c[k]
    return ( 2 * sinx * cosx * y0 if sinp # sin(2 * x) * y0
             else cosx * (y0 - y1) )      # cos(x) * (y0 - y1)
  _SinCosSeries = staticmethod(_SinCosSeries)

  def _Astroid(x, y):
    """Private: solve astroid equation."""
    # Solve k^4+2*k^3-(x^2+y^2-1)*k^2-2*y^2*k-y^2 = 0 for positive root k.
    # This solution is adapted from Geocentric::Reverse.
    p = Math.sq(x)
    q = Math.sq(y)
    r = (p + q - 1) / 6
    if not(q == 0 and r <= 0):
      # Avoid possible division by zero when r = 0 by multiplying equations
      # for s and t by r^3 and r, resp.
      S = p * q / 4            # S = r^3 * s
      r2 = Math.sq(r)
      r3 = r * r2
      # The discriminant of the quadratic equation for T3.  This is zero on
      # the evolute curve p^(1/3)+q^(1/3) = 1
      disc = S * (S + 2 * r3)
      u = r
      if disc >= 0:
        T3 = S + r3
        # Pick the sign on the sqrt to maximize abs(T3).  This minimizes loss
        # of precision due to cancellation.  The result is unchanged because
        # of the way the T is used in definition of u.
        T3 += -math.sqrt(disc) if T3 < 0 else math.sqrt(disc) # T3 = (r * t)^3
        # N.B. cbrt always returns the real root.  cbrt(-8) = -2.
        T = Math.cbrt(T3)       # T = r * t
        # T can be zero; but then r2 / T -> 0.
        u += T + (r2 / T if T != 0 else 0)
      else:
        # T is complex, but the way u is defined the result is real.
        ang = math.atan2(math.sqrt(-disc), -(S + r3))
        # There are three possible cube roots.  We choose the root which
        # avoids cancellation.  Note that disc < 0 implies that r < 0.
        u += 2 * r * math.cos(ang / 3)
      v = math.sqrt(Math.sq(u) + q) # guaranteed positive
      # Avoid loss of accuracy when u < 0.
      uv = q / (v - u) if u < 0 else u + v # u+v, guaranteed positive
      w = (uv - q) / (2 * v)               # positive?
      # Rearrange expression for k to avoid loss of accuracy due to
      # subtraction.  Division by 0 not possible because uv > 0, w >= 0.
      k = uv / (math.sqrt(uv + Math.sq(w)) + w) # guaranteed positive
    else:                                       # q == 0 && r <= 0
      # y = 0 with |x| <= 1.  Handle this case directly.
      # for y small, positive root is k = abs(y)/sqrt(1-x^2)
      k = 0
    return k
  _Astroid = staticmethod(_Astroid)

  def _A1m1f(eps):
    """Private: return A1-1."""
    coeff = [
      1, 4, 64, 0, 256,
    ]
    m = Geodesic.nA1_//2
    t = Math.polyval(m, coeff, 0, Math.sq(eps)) / coeff[m + 1]
    return (t + eps) / (1 - eps)
  _A1m1f = staticmethod(_A1m1f)

  def _C1f(eps, c):
    """Private: return C1."""
    coeff = [
      -1, 6, -16, 32,
      -9, 64, -128, 2048,
      9, -16, 768,
      3, -5, 512,
      -7, 1280,
      -7, 2048,
    ]
    eps2 = Math.sq(eps)
    d = eps
    o = 0
    for l in range(1, Geodesic.nC1_ + 1): # l is index of C1p[l]
      m = (Geodesic.nC1_ - l) // 2        # order of polynomial in eps^2
      c[l] = d * Math.polyval(m, coeff, o, eps2) / coeff[o + m + 1]
      o += m + 2
      d *= eps
  _C1f = staticmethod(_C1f)

  def _C1pf(eps, c):
    """Private: return C1'"""
    coeff = [
      205, -432, 768, 1536,
      4005, -4736, 3840, 12288,
      -225, 116, 384,
      -7173, 2695, 7680,
      3467, 7680,
      38081, 61440,
    ]
    eps2 = Math.sq(eps)
    d = eps
    o = 0
    for l in range(1, Geodesic.nC1p_ + 1): # l is index of C1p[l]
      m = (Geodesic.nC1p_ - l) // 2 # order of polynomial in eps^2
      c[l] = d * Math.polyval(m, coeff, o, eps2) / coeff[o + m + 1]
      o += m + 2
      d *= eps
  _C1pf = staticmethod(_C1pf)

  def _A2m1f(eps):
    """Private: return A2-1"""
    coeff = [
      -11, -28, -192, 0, 256,
    ]
    m = Geodesic.nA2_//2
    t = Math.polyval(m, coeff, 0, Math.sq(eps)) / coeff[m + 1]
    return (t - eps) / (1 + eps)
  _A2m1f = staticmethod(_A2m1f)

  def _C2f(eps, c):
    """Private: return C2"""
    coeff = [
      1, 2, 16, 32,
      35, 64, 384, 2048,
      15, 80, 768,
      7, 35, 512,
      63, 1280,
      77, 2048,
    ]
    eps2 = Math.sq(eps)
    d = eps
    o = 0
    for l in range(1, Geodesic.nC2_ + 1): # l is index of C2[l]
      m = (Geodesic.nC2_ - l) // 2        # order of polynomial in eps^2
      c[l] = d * Math.polyval(m, coeff, o, eps2) / coeff[o + m + 1]
      o += m + 2
      d *= eps
  _C2f = staticmethod(_C2f)

  def __init__(self, a, f):
    """Construct a Geodesic object

    :param a: the equatorial radius of the ellipsoid in meters
    :param f: the flattening of the ellipsoid

    An exception is thrown if *a* or the polar semi-axis *b* = *a* (1 -
    *f*) is not a finite positive quantity.

    """

    self.a = float(a)
    """The equatorial radius in meters (readonly)"""
    self.f = float(f)
    """The flattening (readonly)"""
    self._f1 = 1 - self.f
    self._e2 = self.f * (2 - self.f)
    self._ep2 = self._e2 / Math.sq(self._f1) # e2 / (1 - e2)
    self._n = self.f / ( 2 - self.f)
    self._b = self.a * self._f1
    # authalic radius squared
    self._c2 = (Math.sq(self.a) + Math.sq(self._b) *
                (1 if self._e2 == 0 else
                 (Math.atanh(math.sqrt(self._e2)) if self._e2 > 0 else
                  math.atan(math.sqrt(-self._e2))) /
                 math.sqrt(abs(self._e2))))/2
    # The sig12 threshold for "really short".  Using the auxiliary sphere
    # solution with dnm computed at (bet1 + bet2) / 2, the relative error in
    # the azimuth consistency check is sig12^2 * abs(f) * min(1, 1-f/2) / 2.
    # (Error measured for 1/100 < b/a < 100 and abs(f) >= 1/1000.  For a given
    # f and sig12, the max error occurs for lines near the pole.  If the old
    # rule for computing dnm = (dn1 + dn2)/2 is used, then the error increases
    # by a factor of 2.)  Setting this equal to epsilon gives sig12 = etol2.
    # Here 0.1 is a safety factor (error decreased by 100) and max(0.001,
    # abs(f)) stops etol2 getting too large in the nearly spherical case.
    self._etol2 = 0.1 * Geodesic.tol2_ / math.sqrt( max(0.001, abs(self.f)) *
                                                    min(1.0, 1-self.f/2) / 2 )
    if not(Math.isfinite(self.a) and self.a > 0):
      raise ValueError("Equatorial radius is not positive")
    if not(Math.isfinite(self._b) and self._b > 0):
      raise ValueError("Polar semi-axis is not positive")
    self._A3x = list(range(Geodesic.nA3x_))
    self._C3x = list(range(Geodesic.nC3x_))
    self._C4x = list(range(Geodesic.nC4x_))
    self._A3coeff()
    self._C3coeff()
    self._C4coeff()

  def _A3coeff(self):
    """Private: return coefficients for A3"""
    coeff = [
      -3, 128,
      -2, -3, 64,
      -1, -3, -1, 16,
      3, -1, -2, 8,
      1, -1, 2,
      1, 1,
    ]
    o = 0; k = 0
    for j in range(Geodesic.nA3_ - 1, -1, -1): # coeff of eps^j
      m = min(Geodesic.nA3_ - j - 1, j) # order of polynomial in n
      self._A3x[k] = Math.polyval(m, coeff, o, self._n) / coeff[o + m + 1]
      k += 1
      o += m + 2

  def _C3coeff(self):
    """Private: return coefficients for C3"""
    coeff = [
      3, 128,
      2, 5, 128,
      -1, 3, 3, 64,
      -1, 0, 1, 8,
      -1, 1, 4,
      5, 256,
      1, 3, 128,
      -3, -2, 3, 64,
      1, -3, 2, 32,
      7, 512,
      -10, 9, 384,
      5, -9, 5, 192,
      7, 512,
      -14, 7, 512,
      21, 2560,
    ]
    o = 0; k = 0
    for l in range(1, Geodesic.nC3_): # l is index of C3[l]
      for j in range(Geodesic.nC3_ - 1, l - 1, -1): # coeff of eps^j
        m = min(Geodesic.nC3_ - j - 1, j) # order of polynomial in n
        self._C3x[k] = Math.polyval(m, coeff, o, self._n) / coeff[o + m + 1]
        k += 1
        o += m + 2

  def _C4coeff(self):
    """Private: return coefficients for C4"""
    coeff = [
      97, 15015,
      1088, 156, 45045,
      -224, -4784, 1573, 45045,
      -10656, 14144, -4576, -858, 45045,
      64, 624, -4576, 6864, -3003, 15015,
      100, 208, 572, 3432, -12012, 30030, 45045,
      1, 9009,
      -2944, 468, 135135,
      5792, 1040, -1287, 135135,
      5952, -11648, 9152, -2574, 135135,
      -64, -624, 4576, -6864, 3003, 135135,
      8, 10725,
      1856, -936, 225225,
      -8448, 4992, -1144, 225225,
      -1440, 4160, -4576, 1716, 225225,
      -136, 63063,
      1024, -208, 105105,
      3584, -3328, 1144, 315315,
      -128, 135135,
      -2560, 832, 405405,
      128, 99099,
    ]
    o = 0; k = 0
    for l in range(Geodesic.nC4_): # l is index of C4[l]
      for j in range(Geodesic.nC4_ - 1, l - 1, -1): # coeff of eps^j
        m = Geodesic.nC4_ - j - 1 # order of polynomial in n
        self._C4x[k] = Math.polyval(m, coeff, o, self._n) / coeff[o + m + 1]
        k += 1
        o += m + 2

  def _A3f(self, eps):
    """Private: return A3"""
    # Evaluate A3
    return Math.polyval(Geodesic.nA3_ - 1, self._A3x, 0, eps)

  def _C3f(self, eps, c):
    """Private: return C3"""
    # Evaluate C3
    # Elements c[1] thru c[nC3_ - 1] are set
    mult = 1
    o = 0
    for l in range(1, Geodesic.nC3_): # l is index of C3[l]
      m = Geodesic.nC3_ - l - 1       # order of polynomial in eps
      mult *= eps
      c[l] = mult * Math.polyval(m, self._C3x, o, eps)
      o += m + 1

  def _C4f(self, eps, c):
    """Private: return C4"""
    # Evaluate C4 coeffs by Horner's method
    # Elements c[0] thru c[nC4_ - 1] are set
    mult = 1
    o = 0
    for l in range(Geodesic.nC4_): # l is index of C4[l]
      m = Geodesic.nC4_ - l - 1    # order of polynomial in eps
      c[l] = mult * Math.polyval(m, self._C4x, o, eps)
      o += m + 1
      mult *= eps

  # return s12b, m12b, m0, M12, M21
  def _Lengths(self, eps, sig12,
               ssig1, csig1, dn1, ssig2, csig2, dn2, cbet1, cbet2, outmask,
               # Scratch areas of the right size
               C1a, C2a):
    """Private: return a bunch of lengths"""
    # Return s12b, m12b, m0, M12, M21, where
    # m12b = (reduced length)/_b; s12b = distance/_b,
    # m0 = coefficient of secular term in expression for reduced length.
    outmask &= Geodesic.OUT_MASK
    # outmask & DISTANCE: set s12b
    # outmask & REDUCEDLENGTH: set m12b & m0
    # outmask & GEODESICSCALE: set M12 & M21

    s12b = m12b = m0 = M12 = M21 = Math.nan
    if outmask & (Geodesic.DISTANCE | Geodesic.REDUCEDLENGTH |
                  Geodesic.GEODESICSCALE):
      A1 = Geodesic._A1m1f(eps)
      Geodesic._C1f(eps, C1a)
      if outmask & (Geodesic.REDUCEDLENGTH | Geodesic.GEODESICSCALE):
        A2 = Geodesic._A2m1f(eps)
        Geodesic._C2f(eps, C2a)
        m0x = A1 - A2
        A2 = 1 + A2
      A1 = 1 + A1
    if outmask & Geodesic.DISTANCE:
      B1 = (Geodesic._SinCosSeries(True, ssig2, csig2, C1a) -
            Geodesic._SinCosSeries(True, ssig1, csig1, C1a))
      # Missing a factor of _b
      s12b = A1 * (sig12 + B1)
      if outmask & (Geodesic.REDUCEDLENGTH | Geodesic.GEODESICSCALE):
        B2 = (Geodesic._SinCosSeries(True, ssig2, csig2, C2a) -
              Geodesic._SinCosSeries(True, ssig1, csig1, C2a))
        J12 = m0x * sig12 + (A1 * B1 - A2 * B2)
    elif outmask & (Geodesic.REDUCEDLENGTH | Geodesic.GEODESICSCALE):
      # Assume here that nC1_ >= nC2_
      for l in range(1, Geodesic.nC2_):
        C2a[l] = A1 * C1a[l] - A2 * C2a[l]
      J12 = m0x * sig12 + (Geodesic._SinCosSeries(True, ssig2, csig2, C2a) -
                           Geodesic._SinCosSeries(True, ssig1, csig1, C2a))
    if outmask & Geodesic.REDUCEDLENGTH:
      m0 = m0x
      # Missing a factor of _b.
      # Add parens around (csig1 * ssig2) and (ssig1 * csig2) to ensure
      # accurate cancellation in the case of coincident points.
      m12b = (dn2 * (csig1 * ssig2) - dn1 * (ssig1 * csig2) -
              csig1 * csig2 * J12)
    if outmask & Geodesic.GEODESICSCALE:
      csig12 = csig1 * csig2 + ssig1 * ssig2
      t = self._ep2 * (cbet1 - cbet2) * (cbet1 + cbet2) / (dn1 + dn2)
      M12 = csig12 + (t * ssig2 - csig2 * J12) * ssig1 / dn1
      M21 = csig12 - (t * ssig1 - csig1 * J12) * ssig2 / dn2
    return s12b, m12b, m0, M12, M21

  # return sig12, salp1, calp1, salp2, calp2, dnm
  def _InverseStart(self, sbet1, cbet1, dn1, sbet2, cbet2, dn2,
                    lam12, slam12, clam12,
                    # Scratch areas of the right size
                    C1a, C2a):
    """Private: Find a starting value for Newton's method."""
    # Return a starting point for Newton's method in salp1 and calp1 (function
    # value is -1).  If Newton's method doesn't need to be used, return also
    # salp2 and calp2 and function value is sig12.
    sig12 = -1; salp2 = calp2 = dnm = Math.nan # Return values
    # bet12 = bet2 - bet1 in [0, pi); bet12a = bet2 + bet1 in (-pi, 0]
    sbet12 = sbet2 * cbet1 - cbet2 * sbet1
    cbet12 = cbet2 * cbet1 + sbet2 * sbet1
    # Volatile declaration needed to fix inverse cases
    # 88.202499451857 0 -88.202499451857 179.981022032992859592
    # 89.262080389218 0 -89.262080389218 179.992207982775375662
    # 89.333123580033 0 -89.333123580032997687 179.99295812360148422
    # which otherwise fail with g++ 4.4.4 x86 -O3
    sbet12a = sbet2 * cbet1
    sbet12a += cbet2 * sbet1

    shortline = cbet12 >= 0 and sbet12 < 0.5 and cbet2 * lam12 < 0.5
    if shortline:
      sbetm2 = Math.sq(sbet1 + sbet2)
      # sin((bet1+bet2)/2)^2
      # =  (sbet1 + sbet2)^2 / ((sbet1 + sbet2)^2 + (cbet1 + cbet2)^2)
      sbetm2 /= sbetm2 + Math.sq(cbet1 + cbet2)
      dnm = math.sqrt(1 + self._ep2 * sbetm2)
      omg12 = lam12 / (self._f1 * dnm)
      somg12 = math.sin(omg12); comg12 = math.cos(omg12)
    else:
      somg12 = slam12; comg12 = clam12

    salp1 = cbet2 * somg12
    calp1 = (
      sbet12 + cbet2 * sbet1 * Math.sq(somg12) / (1 + comg12) if comg12 >= 0
      else sbet12a - cbet2 * sbet1 * Math.sq(somg12) / (1 - comg12))

    ssig12 = math.hypot(salp1, calp1)
    csig12 = sbet1 * sbet2 + cbet1 * cbet2 * comg12

    if shortline and ssig12 < self._etol2:
      # really short lines
      salp2 = cbet1 * somg12
      calp2 = sbet12 - cbet1 * sbet2 * (Math.sq(somg12) / (1 + comg12)
                                        if comg12 >= 0 else 1 - comg12)
      salp2, calp2 = Math.norm(salp2, calp2)
      # Set return value
      sig12 = math.atan2(ssig12, csig12)
    elif (abs(self._n) >= 0.1 or # Skip astroid calc if too eccentric
          csig12 >= 0 or
          ssig12 >= 6 * abs(self._n) * math.pi * Math.sq(cbet1)):
      # Nothing to do, zeroth order spherical approximation is OK
      pass
    else:
      # Scale lam12 and bet2 to x, y coordinate system where antipodal point
      # is at origin and singular point is at y = 0, x = -1.
      # real y, lamscale, betscale
      # Volatile declaration needed to fix inverse case
      # 56.320923501171 0 -56.320923501171 179.664747671772880215
      # which otherwise fails with g++ 4.4.4 x86 -O3
      # volatile real x
      lam12x = math.atan2(-slam12, -clam12)
      if self.f >= 0:            # In fact f == 0 does not get here
        # x = dlong, y = dlat
        k2 = Math.sq(sbet1) * self._ep2
        eps = k2 / (2 * (1 + math.sqrt(1 + k2)) + k2)
        lamscale = self.f * cbet1 * self._A3f(eps) * math.pi
        betscale = lamscale * cbet1
        x = lam12x / lamscale
        y = sbet12a / betscale
      else:                     # _f < 0
        # x = dlat, y = dlong
        cbet12a = cbet2 * cbet1 - sbet2 * sbet1
        bet12a = math.atan2(sbet12a, cbet12a)
        # real m12b, m0, dummy
        # In the case of lon12 = 180, this repeats a calculation made in
        # Inverse.
        dummy, m12b, m0, dummy, dummy = self._Lengths(
          self._n, math.pi + bet12a, sbet1, -cbet1, dn1, sbet2, cbet2, dn2,
          cbet1, cbet2, Geodesic.REDUCEDLENGTH, C1a, C2a)
        x = -1 + m12b / (cbet1 * cbet2 * m0 * math.pi)
        betscale = (sbet12a / x if x < -0.01
                    else -self.f * Math.sq(cbet1) * math.pi)
        lamscale = betscale / cbet1
        y = lam12x / lamscale

      if y > -Geodesic.tol1_ and x > -1 - Geodesic.xthresh_:
        # strip near cut
        if self.f >= 0:
          salp1 = min(1.0, -x); calp1 = - math.sqrt(1 - Math.sq(salp1))
        else:
          calp1 = max((0.0 if x > -Geodesic.tol1_ else -1.0), x)
          salp1 = math.sqrt(1 - Math.sq(calp1))
      else:
        # Estimate alp1, by solving the astroid problem.
        #
        # Could estimate alpha1 = theta + pi/2, directly, i.e.,
        #   calp1 = y/k; salp1 = -x/(1+k);  for _f >= 0
        #   calp1 = x/(1+k); salp1 = -y/k;  for _f < 0 (need to check)
        #
        # However, it's better to estimate omg12 from astroid and use
        # spherical formula to compute alp1.  This reduces the mean number of
        # Newton iterations for astroid cases from 2.24 (min 0, max 6) to 2.12
        # (min 0 max 5).  The changes in the number of iterations are as
        # follows:
        #
        # change percent
        #    1       5
        #    0      78
        #   -1      16
        #   -2       0.6
        #   -3       0.04
        #   -4       0.002
        #
        # The histogram of iterations is (m = number of iterations estimating
        # alp1 directly, n = number of iterations estimating via omg12, total
        # number of trials = 148605):
        #
        #  iter    m      n
        #    0   148    186
        #    1 13046  13845
        #    2 93315 102225
        #    3 36189  32341
        #    4  5396      7
        #    5   455      1
        #    6    56      0
        #
        # Because omg12 is near pi, estimate work with omg12a = pi - omg12
        k = Geodesic._Astroid(x, y)
        omg12a = lamscale * ( -x * k/(1 + k) if self.f >= 0
                              else -y * (1 + k)/k )
        somg12 = math.sin(omg12a); comg12 = -math.cos(omg12a)
        # Update spherical estimate of alp1 using omg12 instead of lam12
        salp1 = cbet2 * somg12
        calp1 = sbet12a - cbet2 * sbet1 * Math.sq(somg12) / (1 - comg12)
    # Sanity check on starting guess.  Backwards check allows NaN through.
    if not (salp1 <= 0):
      salp1, calp1 = Math.norm(salp1, calp1)
    else:
      salp1 = 1; calp1 = 0
    return sig12, salp1, calp1, salp2, calp2, dnm

  # return lam12, salp2, calp2, sig12, ssig1, csig1, ssig2, csig2, eps,
  # domg12, dlam12
  def _Lambda12(self, sbet1, cbet1, dn1, sbet2, cbet2, dn2, salp1, calp1,
                slam120, clam120, diffp,
                # Scratch areas of the right size
                C1a, C2a, C3a):
    """Private: Solve hybrid problem"""
    if sbet1 == 0 and calp1 == 0:
      # Break degeneracy of equatorial line.  This case has already been
      # handled.
      calp1 = -Geodesic.tiny_

    # sin(alp1) * cos(bet1) = sin(alp0)
    salp0 = salp1 * cbet1
    calp0 = math.hypot(calp1, salp1 * sbet1) # calp0 > 0

    # real somg1, comg1, somg2, comg2, lam12
    # tan(bet1) = tan(sig1) * cos(alp1)
    # tan(omg1) = sin(alp0) * tan(sig1) = tan(omg1)=tan(alp1)*sin(bet1)
    ssig1 = sbet1; somg1 = salp0 * sbet1
    csig1 = comg1 = calp1 * cbet1
    ssig1, csig1 = Math.norm(ssig1, csig1)
    # Math.norm(somg1, comg1); -- don't need to normalize!

    # Enforce symmetries in the case abs(bet2) = -bet1.  Need to be careful
    # about this case, since this can yield singularities in the Newton
    # iteration.
    # sin(alp2) * cos(bet2) = sin(alp0)
    salp2 = salp0 / cbet2 if cbet2 != cbet1 else salp1
    # calp2 = sqrt(1 - sq(salp2))
    #       = sqrt(sq(calp0) - sq(sbet2)) / cbet2
    # and subst for calp0 and rearrange to give (choose positive sqrt
    # to give alp2 in [0, pi/2]).
    calp2 = (math.sqrt(Math.sq(calp1 * cbet1) +
                       ((cbet2 - cbet1) * (cbet1 + cbet2) if cbet1 < -sbet1
                        else (sbet1 - sbet2) * (sbet1 + sbet2))) / cbet2
             if cbet2 != cbet1 or abs(sbet2) != -sbet1 else abs(calp1))
    # tan(bet2) = tan(sig2) * cos(alp2)
    # tan(omg2) = sin(alp0) * tan(sig2).
    ssig2 = sbet2; somg2 = salp0 * sbet2
    csig2 = comg2 = calp2 * cbet2
    ssig2, csig2 = Math.norm(ssig2, csig2)
    # Math.norm(somg2, comg2); -- don't need to normalize!

    # sig12 = sig2 - sig1, limit to [0, pi]
    sig12 = math.atan2(max(0.0, csig1 * ssig2 - ssig1 * csig2),
                                csig1 * csig2 + ssig1 * ssig2)

    # omg12 = omg2 - omg1, limit to [0, pi]
    somg12 = max(0.0, comg1 * somg2 - somg1 * comg2)
    comg12 =          comg1 * comg2 + somg1 * somg2
    # eta = omg12 - lam120
    eta = math.atan2(somg12 * clam120 - comg12 * slam120,
                     comg12 * clam120 + somg12 * slam120)

    # real B312
    k2 = Math.sq(calp0) * self._ep2
    eps = k2 / (2 * (1 + math.sqrt(1 + k2)) + k2)
    self._C3f(eps, C3a)
    B312 = (Geodesic._SinCosSeries(True, ssig2, csig2, C3a) -
            Geodesic._SinCosSeries(True, ssig1, csig1, C3a))
    domg12 =  -self.f * self._A3f(eps) * salp0 * (sig12 + B312)
    lam12 = eta + domg12

    if diffp:
      if calp2 == 0:
        dlam12 = - 2 * self._f1 * dn1 / sbet1
      else:
        dummy, dlam12, dummy, dummy, dummy = self._Lengths(
          eps, sig12, ssig1, csig1, dn1, ssig2, csig2, dn2, cbet1, cbet2,
          Geodesic.REDUCEDLENGTH, C1a, C2a)
        dlam12 *= self._f1 / (calp2 * cbet2)
    else:
      dlam12 = Math.nan

    return (lam12, salp2, calp2, sig12, ssig1, csig1, ssig2, csig2, eps,
            domg12, dlam12)

  # return a12, s12, salp1, calp1, salp2, calp2, m12, M12, M21, S12
  def _GenInverse(self, lat1, lon1, lat2, lon2, outmask):
    """Private: General version of the inverse problem"""
    a12 = s12 = m12 = M12 = M21 = S12 = Math.nan # return vals

    outmask &= Geodesic.OUT_MASK
    # Compute longitude difference (AngDiff does this carefully).  Result is
    # in [-180, 180] but -180 is only for west-going geodesics.  180 is for
    # east-going and meridional geodesics.
    lon12, lon12s = Math.AngDiff(lon1, lon2)
    # Make longitude difference positive.
    lonsign = 1 if lon12 >= 0 else -1
    # If very close to being on the same half-meridian, then make it so.
    lon12 = lonsign * Math.AngRound(lon12)
    lon12s = Math.AngRound((180 - lon12) - lonsign * lon12s)
    lam12 = math.radians(lon12)
    if lon12 > 90:
      slam12, clam12 = Math.sincosd(lon12s); clam12 = -clam12
    else:
      slam12, clam12 = Math.sincosd(lon12)

    # If really close to the equator, treat as on equator.
    lat1 = Math.AngRound(Math.LatFix(lat1))
    lat2 = Math.AngRound(Math.LatFix(lat2))
    # Swap points so that point with higher (abs) latitude is point 1
    # If one latitude is a nan, then it becomes lat1.
    swapp = -1 if abs(lat1) < abs(lat2) else 1
    if swapp < 0:
      lonsign *= -1
      lat2, lat1 = lat1, lat2
    # Make lat1 <= 0
    latsign = 1 if lat1 < 0 else -1
    lat1 *= latsign
    lat2 *= latsign
    # Now we have
    #
    #     0 <= lon12 <= 180
    #     -90 <= lat1 <= 0
    #     lat1 <= lat2 <= -lat1
    #
    # longsign, swapp, latsign register the transformation to bring the
    # coordinates to this canonical form.  In all cases, 1 means no change was
    # made.  We make these transformations so that there are few cases to
    # check, e.g., on verifying quadrants in atan2.  In addition, this
    # enforces some symmetries in the results returned.

    # real phi, sbet1, cbet1, sbet2, cbet2, s12x, m12x

    sbet1, cbet1 = Math.sincosd(lat1); sbet1 *= self._f1
    # Ensure cbet1 = +epsilon at poles
    sbet1, cbet1 = Math.norm(sbet1, cbet1); cbet1 = max(Geodesic.tiny_, cbet1)

    sbet2, cbet2 = Math.sincosd(lat2); sbet2 *= self._f1
    # Ensure cbet2 = +epsilon at poles
    sbet2, cbet2 = Math.norm(sbet2, cbet2); cbet2 = max(Geodesic.tiny_, cbet2)

    # If cbet1 < -sbet1, then cbet2 - cbet1 is a sensitive measure of the
    # |bet1| - |bet2|.  Alternatively (cbet1 >= -sbet1), abs(sbet2) + sbet1 is
    # a better measure.  This logic is used in assigning calp2 in Lambda12.
    # Sometimes these quantities vanish and in that case we force bet2 = +/-
    # bet1 exactly.  An example where is is necessary is the inverse problem
    # 48.522876735459 0 -48.52287673545898293 179.599720456223079643
    # which failed with Visual Studio 10 (Release and Debug)

    if cbet1 < -sbet1:
      if cbet2 == cbet1:
        sbet2 = sbet1 if sbet2 < 0 else -sbet1
    else:
      if abs(sbet2) == -sbet1:
        cbet2 = cbet1

    dn1 = math.sqrt(1 + self._ep2 * Math.sq(sbet1))
    dn2 = math.sqrt(1 + self._ep2 * Math.sq(sbet2))

    # real a12, sig12, calp1, salp1, calp2, salp2
    # index zero elements of these arrays are unused
    C1a = list(range(Geodesic.nC1_ + 1))
    C2a = list(range(Geodesic.nC2_ + 1))
    C3a = list(range(Geodesic.nC3_))

    meridian = lat1 == -90 or slam12 == 0

    if meridian:

      # Endpoints are on a single full meridian, so the geodesic might lie on
      # a meridian.

      calp1 = clam12; salp1 = slam12 # Head to the target longitude
      calp2 = 1.0; salp2 = 0.0       # At the target we're heading north

      # tan(bet) = tan(sig) * cos(alp)
      ssig1 = sbet1; csig1 = calp1 * cbet1
      ssig2 = sbet2; csig2 = calp2 * cbet2

      # sig12 = sig2 - sig1
      sig12 = math.atan2(max(0.0, csig1 * ssig2 - ssig1 * csig2),
                                  csig1 * csig2 + ssig1 * ssig2)

      s12x, m12x, dummy, M12, M21 = self._Lengths(
        self._n, sig12, ssig1, csig1, dn1, ssig2, csig2, dn2, cbet1, cbet2,
        outmask | Geodesic.DISTANCE | Geodesic.REDUCEDLENGTH, C1a, C2a)

      # Add the check for sig12 since zero length geodesics might yield m12 <
      # 0.  Test case was
      #
      #    echo 20.001 0 20.001 0 | GeodSolve -i
      #
      # In fact, we will have sig12 > pi/2 for meridional geodesic which is
      # not a shortest path.
      if sig12 < 1 or m12x >= 0:
        if (sig12 < 3 * Geodesic.tiny_ or
            # Prevent negative s12 or m12 for short lines
            (sig12 < Geodesic.tol0_ and (s12x < 0 or m12x < 0))):
          sig12 = m12x = s12x = 0.0
        m12x *= self._b
        s12x *= self._b
        a12 = math.degrees(sig12)
      else:
        # m12 < 0, i.e., prolate and too close to anti-podal
        meridian = False
    # end if meridian:

    # somg12 > 1 marks that it needs to be calculated
    somg12 = 2.0; comg12 = 0.0; omg12 = 0.0
    if (not meridian and
        sbet1 == 0 and   # and sbet2 == 0
        # Mimic the way Lambda12 works with calp1 = 0
        (self.f <= 0 or lon12s >= self.f * 180)):

      # Geodesic runs along equator
      calp1 = calp2 = 0.0; salp1 = salp2 = 1.0
      s12x = self.a * lam12
      sig12 = omg12 = lam12 / self._f1
      m12x = self._b * math.sin(sig12)
      if outmask & Geodesic.GEODESICSCALE:
        M12 = M21 = math.cos(sig12)
      a12 = lon12 / self._f1

    elif not meridian:

      # Now point1 and point2 belong within a hemisphere bounded by a
      # meridian and geodesic is neither meridional or equatorial.

      # Figure a starting point for Newton's method
      sig12, salp1, calp1, salp2, calp2, dnm = self._InverseStart(
        sbet1, cbet1, dn1, sbet2, cbet2, dn2, lam12, slam12, clam12, C1a, C2a)

      if sig12 >= 0:
        # Short lines (InverseStart sets salp2, calp2, dnm)
        s12x = sig12 * self._b * dnm
        m12x = (Math.sq(dnm) * self._b * math.sin(sig12 / dnm))
        if outmask & Geodesic.GEODESICSCALE:
          M12 = M21 = math.cos(sig12 / dnm)
        a12 = math.degrees(sig12)
        omg12 = lam12 / (self._f1 * dnm)
      else:

        # Newton's method.  This is a straightforward solution of f(alp1) =
        # lambda12(alp1) - lam12 = 0 with one wrinkle.  f(alp) has exactly one
        # root in the interval (0, pi) and its derivative is positive at the
        # root.  Thus f(alp) is positive for alp > alp1 and negative for alp <
        # alp1.  During the course of the iteration, a range (alp1a, alp1b) is
        # maintained which brackets the root and with each evaluation of f(alp)
        # the range is shrunk if possible.  Newton's method is restarted
        # whenever the derivative of f is negative (because the new value of
        # alp1 is then further from the solution) or if the new estimate of
        # alp1 lies outside (0,pi); in this case, the new starting guess is
        # taken to be (alp1a + alp1b) / 2.
        # real ssig1, csig1, ssig2, csig2, eps
        numit = 0
        tripn = tripb = False
        # Bracketing range
        salp1a = Geodesic.tiny_; calp1a = 1.0
        salp1b = Geodesic.tiny_; calp1b = -1.0

        while numit < Geodesic.maxit2_:
          # the WGS84 test set: mean = 1.47, sd = 1.25, max = 16
          # WGS84 and random input: mean = 2.85, sd = 0.60
          (v, salp2, calp2, sig12, ssig1, csig1, ssig2, csig2,
           eps, domg12, dv) = self._Lambda12(
             sbet1, cbet1, dn1, sbet2, cbet2, dn2,
             salp1, calp1, slam12, clam12, numit < Geodesic.maxit1_,
             C1a, C2a, C3a)
          # Reversed test to allow escape with NaNs
          if tripb or not (abs(v) >= (8 if tripn else 1) * Geodesic.tol0_):
            break
          # Update bracketing values
          if v > 0 and (numit > Geodesic.maxit1_ or
                        calp1/salp1 > calp1b/salp1b):
            salp1b = salp1; calp1b = calp1
          elif v < 0 and (numit > Geodesic.maxit1_ or
                          calp1/salp1 < calp1a/salp1a):
            salp1a = salp1; calp1a = calp1

          numit += 1
          if numit < Geodesic.maxit1_ and dv > 0:
            dalp1 = -v/dv
            sdalp1 = math.sin(dalp1); cdalp1 = math.cos(dalp1)
            nsalp1 = salp1 * cdalp1 + calp1 * sdalp1
            if nsalp1 > 0 and abs(dalp1) < math.pi:
              calp1 = calp1 * cdalp1 - salp1 * sdalp1
              salp1 = nsalp1
              salp1, calp1 = Math.norm(salp1, calp1)
              # In some regimes we don't get quadratic convergence because
              # slope -> 0.  So use convergence conditions based on epsilon
              # instead of sqrt(epsilon).
              tripn = abs(v) <= 16 * Geodesic.tol0_
              continue
          # Either dv was not positive or updated value was outside
          # legal range.  Use the midpoint of the bracket as the next
          # estimate.  This mechanism is not needed for the WGS84
          # ellipsoid, but it does catch problems with more eccentric
          # ellipsoids.  Its efficacy is such for
          # the WGS84 test set with the starting guess set to alp1 = 90deg:
          # the WGS84 test set: mean = 5.21, sd = 3.93, max = 24
          # WGS84 and random input: mean = 4.74, sd = 0.99
          salp1 = (salp1a + salp1b)/2
          calp1 = (calp1a + calp1b)/2
          salp1, calp1 = Math.norm(salp1, calp1)
          tripn = False
          tripb = (abs(salp1a - salp1) + (calp1a - calp1) < Geodesic.tolb_ or
                   abs(salp1 - salp1b) + (calp1 - calp1b) < Geodesic.tolb_)

        lengthmask = (outmask |
                      (Geodesic.DISTANCE
                       if (outmask & (Geodesic.REDUCEDLENGTH |
                                      Geodesic.GEODESICSCALE))
                       else Geodesic.EMPTY))
        s12x, m12x, dummy, M12, M21 = self._Lengths(
          eps, sig12, ssig1, csig1, dn1, ssig2, csig2, dn2, cbet1, cbet2,
          lengthmask, C1a, C2a)

        m12x *= self._b
        s12x *= self._b
        a12 = math.degrees(sig12)
        if outmask & Geodesic.AREA:
          # omg12 = lam12 - domg12
          sdomg12 = math.sin(domg12); cdomg12 = math.cos(domg12)
          somg12 = slam12 * cdomg12 - clam12 * sdomg12
          comg12 = clam12 * cdomg12 + slam12 * sdomg12

    # end elif not meridian

    if outmask & Geodesic.DISTANCE:
      s12 = 0.0 + s12x          # Convert -0 to 0

    if outmask & Geodesic.REDUCEDLENGTH:
      m12 = 0.0 + m12x          # Convert -0 to 0

    if outmask & Geodesic.AREA:
      # From Lambda12: sin(alp1) * cos(bet1) = sin(alp0)
      salp0 = salp1 * cbet1
      calp0 = math.hypot(calp1, salp1 * sbet1) # calp0 > 0
      # real alp12
      if calp0 != 0 and salp0 != 0:
        # From Lambda12: tan(bet) = tan(sig) * cos(alp)
        ssig1 = sbet1; csig1 = calp1 * cbet1
        ssig2 = sbet2; csig2 = calp2 * cbet2
        k2 = Math.sq(calp0) * self._ep2
        eps = k2 / (2 * (1 + math.sqrt(1 + k2)) + k2)
        # Multiplier = a^2 * e^2 * cos(alpha0) * sin(alpha0).
        A4 = Math.sq(self.a) * calp0 * salp0 * self._e2
        ssig1, csig1 = Math.norm(ssig1, csig1)
        ssig2, csig2 = Math.norm(ssig2, csig2)
        C4a = list(range(Geodesic.nC4_))
        self._C4f(eps, C4a)
        B41 = Geodesic._SinCosSeries(False, ssig1, csig1, C4a)
        B42 = Geodesic._SinCosSeries(False, ssig2, csig2, C4a)
        S12 = A4 * (B42 - B41)
      else:
        # Avoid problems with indeterminate sig1, sig2 on equator
        S12 = 0.0

      if not meridian and somg12 > 1:
        somg12 = math.sin(omg12); comg12 = math.cos(omg12)

      if (not meridian and
          # omg12 < 3/4 * pi
          comg12 > -0.7071 and   # Long difference not too big
          sbet2 - sbet1 < 1.75): # Lat difference not too big
        # Use tan(Gamma/2) = tan(omg12/2)
        # * (tan(bet1/2)+tan(bet2/2))/(1+tan(bet1/2)*tan(bet2/2))
        # with tan(x/2) = sin(x)/(1+cos(x))
        domg12 = 1 + comg12; dbet1 = 1 + cbet1; dbet2 = 1 + cbet2
        alp12 = 2 * math.atan2( somg12 * ( sbet1 * dbet2 + sbet2 * dbet1 ),
                                domg12 * ( sbet1 * sbet2 + dbet1 * dbet2 ) )
      else:
        # alp12 = alp2 - alp1, used in atan2 so no need to normalize
        salp12 = salp2 * calp1 - calp2 * salp1
        calp12 = calp2 * calp1 + salp2 * salp1
        # The right thing appears to happen if alp1 = +/-180 and alp2 = 0, viz
        # salp12 = -0 and alp12 = -180.  However this depends on the sign
        # being attached to 0 correctly.  The following ensures the correct
        # behavior.
        if salp12 == 0 and calp12 < 0:
          salp12 = Geodesic.tiny_ * calp1
          calp12 = -1.0
        alp12 = math.atan2(salp12, calp12)
      S12 += self._c2 * alp12
      S12 *= swapp * lonsign * latsign
      # Convert -0 to 0
      S12 += 0.0

    # Convert calp, salp to azimuth accounting for lonsign, swapp, latsign.
    if swapp < 0:
      salp2, salp1 = salp1, salp2
      calp2, calp1 = calp1, calp2
      if outmask & Geodesic.GEODESICSCALE:
        M21, M12 = M12, M21

    salp1 *= swapp * lonsign; calp1 *= swapp * latsign
    salp2 *= swapp * lonsign; calp2 *= swapp * latsign

    return a12, s12, salp1, calp1, salp2, calp2, m12, M12, M21, S12

  def Inverse(self, lat1, lon1, lat2, lon2,
              outmask = GeodesicCapability.STANDARD):
    """Solve the inverse geodesic problem

    :param lat1: latitude of the first point in degrees
    :param lon1: longitude of the first point in degrees
    :param lat2: latitude of the second point in degrees
    :param lon2: longitude of the second point in degrees
    :param outmask: the :ref:`output mask <outmask>`
    :return: a :ref:`dict`

    Compute geodesic between (*lat1*, *lon1*) and (*lat2*, *lon2*).
    The default value of *outmask* is STANDARD, i.e., the *lat1*,
    *lon1*, *azi1*, *lat2*, *lon2*, *azi2*, *s12*, *a12* entries are
    returned.

    """

    a12, s12, salp1,calp1, salp2,calp2, m12, M12, M21, S12 = self._GenInverse(
      lat1, lon1, lat2, lon2, outmask)
    outmask &= Geodesic.OUT_MASK
    if outmask & Geodesic.LONG_UNROLL:
      lon12, e = Math.AngDiff(lon1, lon2)
      lon2 = (lon1 + lon12) + e
    else:
      lon2 = Math.AngNormalize(lon2)
    result = {'lat1': Math.LatFix(lat1),
              'lon1': lon1 if outmask & Geodesic.LONG_UNROLL else
              Math.AngNormalize(lon1),
              'lat2': Math.LatFix(lat2),
              'lon2': lon2}
    result['a12'] = a12
    if outmask & Geodesic.DISTANCE: result['s12'] = s12
    if outmask & Geodesic.AZIMUTH:
      result['azi1'] = Math.atan2d(salp1, calp1)
      result['azi2'] = Math.atan2d(salp2, calp2)
    if outmask & Geodesic.REDUCEDLENGTH: result['m12'] = m12
    if outmask & Geodesic.GEODESICSCALE:
      result['M12'] = M12; result['M21'] = M21
    if outmask & Geodesic.AREA: result['S12'] = S12
    return result

  # return a12, lat2, lon2, azi2, s12, m12, M12, M21, S12
  def _GenDirect(self, lat1, lon1, azi1, arcmode, s12_a12, outmask):
    """Private: General version of direct problem"""
    from geographiclib.geodesicline import GeodesicLine
    # Automatically supply DISTANCE_IN if necessary
    if not arcmode: outmask |= Geodesic.DISTANCE_IN
    line = GeodesicLine(self, lat1, lon1, azi1, outmask)
    return line._GenPosition(arcmode, s12_a12, outmask)

  def Direct(self, lat1, lon1, azi1, s12,
             outmask = GeodesicCapability.STANDARD):
    """Solve the direct geodesic problem

    :param lat1: latitude of the first point in degrees
    :param lon1: longitude of the first point in degrees
    :param azi1: azimuth at the first point in degrees
    :param s12: the distance from the first point to the second in
      meters
    :param outmask: the :ref:`output mask <outmask>`
    :return: a :ref:`dict`

    Compute geodesic starting at (*lat1*, *lon1*) with azimuth *azi1*
    and length *s12*.  The default value of *outmask* is STANDARD, i.e.,
    the *lat1*, *lon1*, *azi1*, *lat2*, *lon2*, *azi2*, *s12*, *a12*
    entries are returned.

    """

    a12, lat2, lon2, azi2, s12, m12, M12, M21, S12 = self._GenDirect(
      lat1, lon1, azi1, False, s12, outmask)
    outmask &= Geodesic.OUT_MASK
    result = {'lat1': Math.LatFix(lat1),
              'lon1': lon1 if outmask & Geodesic.LONG_UNROLL else
              Math.AngNormalize(lon1),
              'azi1': Math.AngNormalize(azi1),
              's12': s12}
    result['a12'] = a12
    if outmask & Geodesic.LATITUDE: result['lat2'] = lat2
    if outmask & Geodesic.LONGITUDE: result['lon2'] = lon2
    if outmask & Geodesic.AZIMUTH: result['azi2'] = azi2
    if outmask & Geodesic.REDUCEDLENGTH: result['m12'] = m12
    if outmask & Geodesic.GEODESICSCALE:
      result['M12'] = M12; result['M21'] = M21
    if outmask & Geodesic.AREA: result['S12'] = S12
    return result

  def ArcDirect(self, lat1, lon1, azi1, a12,
                outmask = GeodesicCapability.STANDARD):
    """Solve the direct geodesic problem in terms of spherical arc length

    :param lat1: latitude of the first point in degrees
    :param lon1: longitude of the first point in degrees
    :param azi1: azimuth at the first point in degrees
    :param a12: spherical arc length from the first point to the second
      in degrees
    :param outmask: the :ref:`output mask <outmask>`
    :return: a :ref:`dict`

    Compute geodesic starting at (*lat1*, *lon1*) with azimuth *azi1*
    and arc length *a12*.  The default value of *outmask* is STANDARD,
    i.e., the *lat1*, *lon1*, *azi1*, *lat2*, *lon2*, *azi2*, *s12*,
    *a12* entries are returned.

    """

    a12, lat2, lon2, azi2, s12, m12, M12, M21, S12 = self._GenDirect(
      lat1, lon1, azi1, True, a12, outmask)
    outmask &= Geodesic.OUT_MASK
    result = {'lat1': Math.LatFix(lat1),
              'lon1': lon1 if outmask & Geodesic.LONG_UNROLL else
              Math.AngNormalize(lon1),
              'azi1': Math.AngNormalize(azi1),
              'a12': a12}
    if outmask & Geodesic.DISTANCE: result['s12'] = s12
    if outmask & Geodesic.LATITUDE: result['lat2'] = lat2
    if outmask & Geodesic.LONGITUDE: result['lon2'] = lon2
    if outmask & Geodesic.AZIMUTH: result['azi2'] = azi2
    if outmask & Geodesic.REDUCEDLENGTH: result['m12'] = m12
    if outmask & Geodesic.GEODESICSCALE:
      result['M12'] = M12; result['M21'] = M21
    if outmask & Geodesic.AREA: result['S12'] = S12
    return result

  def Line(self, lat1, lon1, azi1,
           caps = GeodesicCapability.STANDARD |
           GeodesicCapability.DISTANCE_IN):
    """Return a GeodesicLine object

    :param lat1: latitude of the first point in degrees
    :param lon1: longitude of the first point in degrees
    :param azi1: azimuth at the first point in degrees
    :param caps: the :ref:`capabilities <outmask>`
    :return: a :class:`~geographiclib.geodesicline.GeodesicLine`

    This allows points along a geodesic starting at (*lat1*, *lon1*),
    with azimuth *azi1* to be found.  The default value of *caps* is
    STANDARD | DISTANCE_IN, allowing direct geodesic problem to be
    solved.

    """

    from geographiclib.geodesicline import GeodesicLine
    return GeodesicLine(self, lat1, lon1, azi1, caps)

  def _GenDirectLine(self, lat1, lon1, azi1, arcmode, s12_a12,
                     caps = GeodesicCapability.STANDARD |
                     GeodesicCapability.DISTANCE_IN):
    """Private: general form of DirectLine"""
    from geographiclib.geodesicline import GeodesicLine
    # Automatically supply DISTANCE_IN if necessary
    if not arcmode: caps |= Geodesic.DISTANCE_IN
    line = GeodesicLine(self, lat1, lon1, azi1, caps)
    if arcmode:
      line.SetArc(s12_a12)
    else:
      line.SetDistance(s12_a12)
    return line

  def DirectLine(self, lat1, lon1, azi1, s12,
                 caps = GeodesicCapability.STANDARD |
                 GeodesicCapability.DISTANCE_IN):
    """Define a GeodesicLine object in terms of the direct geodesic
    problem specified in terms of spherical arc length

    :param lat1: latitude of the first point in degrees
    :param lon1: longitude of the first point in degrees
    :param azi1: azimuth at the first point in degrees
    :param s12: the distance from the first point to the second in
      meters
    :param caps: the :ref:`capabilities <outmask>`
    :return: a :class:`~geographiclib.geodesicline.GeodesicLine`

    This function sets point 3 of the GeodesicLine to correspond to
    point 2 of the direct geodesic problem.  The default value of *caps*
    is STANDARD | DISTANCE_IN, allowing direct geodesic problem to be
    solved.

    """

    return self._GenDirectLine(lat1, lon1, azi1, False, s12, caps)

  def ArcDirectLine(self, lat1, lon1, azi1, a12,
                 caps = GeodesicCapability.STANDARD |
                 GeodesicCapability.DISTANCE_IN):
    """Define a GeodesicLine object in terms of the direct geodesic
    problem specified in terms of spherical arc length

    :param lat1: latitude of the first point in degrees
    :param lon1: longitude of the first point in degrees
    :param azi1: azimuth at the first point in degrees
    :param a12: spherical arc length from the first point to the second
      in degrees
    :param caps: the :ref:`capabilities <outmask>`
    :return: a :class:`~geographiclib.geodesicline.GeodesicLine`

    This function sets point 3 of the GeodesicLine to correspond to
    point 2 of the direct geodesic problem.  The default value of *caps*
    is STANDARD | DISTANCE_IN, allowing direct geodesic problem to be
    solved.

    """

    return self._GenDirectLine(lat1, lon1, azi1, True, a12, caps)

  def InverseLine(self, lat1, lon1, lat2, lon2,
                  caps = GeodesicCapability.STANDARD |
                  GeodesicCapability.DISTANCE_IN):
    """Define a GeodesicLine object in terms of the invese geodesic problem

    :param lat1: latitude of the first point in degrees
    :param lon1: longitude of the first point in degrees
    :param lat2: latitude of the second point in degrees
    :param lon2: longitude of the second point in degrees
    :param caps: the :ref:`capabilities <outmask>`
    :return: a :class:`~geographiclib.geodesicline.GeodesicLine`

    This function sets point 3 of the GeodesicLine to correspond to
    point 2 of the inverse geodesic problem.  The default value of *caps*
    is STANDARD | DISTANCE_IN, allowing direct geodesic problem to be
    solved.

    """

    from geographiclib.geodesicline import GeodesicLine
    a12, _, salp1, calp1, _, _, _, _, _, _ = self._GenInverse(
      lat1, lon1, lat2, lon2, 0)
    azi1 = Math.atan2d(salp1, calp1)
    if caps & (Geodesic.OUT_MASK & Geodesic.DISTANCE_IN):
      caps |= Geodesic.DISTANCE
    line = GeodesicLine(self, lat1, lon1, azi1, caps, salp1, calp1)
    line.SetArc(a12)
    return line

  def Polygon(self, polyline = False):
    """Return a PolygonArea object

    :param polyline: if True then the object describes a polyline
      instead of a polygon
    :return: a :class:`~geographiclib.polygonarea.PolygonArea`

    """

    from geographiclib.polygonarea import PolygonArea
    return PolygonArea(self, polyline)

  EMPTY         = GeodesicCapability.EMPTY
  """No capabilities, no output."""
  LATITUDE      = GeodesicCapability.LATITUDE
  """Calculate latitude *lat2*."""
  LONGITUDE     = GeodesicCapability.LONGITUDE
  """Calculate longitude *lon2*."""
  AZIMUTH       = GeodesicCapability.AZIMUTH
  """Calculate azimuths *azi1* and *azi2*."""
  DISTANCE      = GeodesicCapability.DISTANCE
  """Calculate distance *s12*."""
  STANDARD      = GeodesicCapability.STANDARD
  """All of the above."""
  DISTANCE_IN   = GeodesicCapability.DISTANCE_IN
  """Allow distance *s12* to be used as input in the direct geodesic
  problem."""
  REDUCEDLENGTH = GeodesicCapability.REDUCEDLENGTH
  """Calculate reduced length *m12*."""
  GEODESICSCALE = GeodesicCapability.GEODESICSCALE
  """Calculate geodesic scales *M12* and *M21*."""
  AREA          = GeodesicCapability.AREA
  """Calculate area *S12*."""
  ALL           = GeodesicCapability.ALL
  """All of the above."""
  LONG_UNROLL   = GeodesicCapability.LONG_UNROLL
  """Unroll longitudes, rather than reducing them to the range
  [-180d,180d].

  """

Geodesic.WGS84 = Geodesic(Constants.WGS84_a, Constants.WGS84_f)
"""Instantiation for the WGS84 ellipsoid"""
