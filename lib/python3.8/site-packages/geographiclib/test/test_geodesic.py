import unittest

from geographiclib.geodesic import Geodesic
from geographiclib.geomath import Math

class GeodesicTest(unittest.TestCase):

  testcases = [
    [35.60777, -139.44815, 111.098748429560326,
     -11.17491, -69.95921, 129.289270889708762,
     8935244.5604818305, 80.50729714281974, 6273170.2055303837,
     0.16606318447386067, 0.16479116945612937, 12841384694976.432],
    [55.52454, 106.05087, 22.020059880982801,
     77.03196, 197.18234, 109.112041110671519,
     4105086.1713924406, 36.892740690445894, 3828869.3344387607,
     0.80076349608092607, 0.80101006984201008, 61674961290615.615],
    [-21.97856, 142.59065, -32.44456876433189,
     41.84138, 98.56635, -41.84359951440466,
     8394328.894657671, 75.62930491011522, 6161154.5773110616,
     0.24816339233950381, 0.24930251203627892, -6637997720646.717],
    [-66.99028, 112.2363, 173.73491240878403,
     -12.70631, 285.90344, 2.512956620913668,
     11150344.2312080241, 100.278634181155759, 6289939.5670446687,
     -0.17199490274700385, -0.17722569526345708, -121287239862139.744],
    [-17.42761, 173.34268, -159.033557661192928,
     -15.84784, 5.93557, -20.787484651536988,
     16076603.1631180673, 144.640108810286253, 3732902.1583877189,
     -0.81273638700070476, -0.81299800519154474, 97825992354058.708],
    [32.84994, 48.28919, 150.492927788121982,
     -56.28556, 202.29132, 48.113449399816759,
     16727068.9438164461, 150.565799985466607, 3147838.1910180939,
     -0.87334918086923126, -0.86505036767110637, -72445258525585.010],
    [6.96833, 52.74123, 92.581585386317712,
     -7.39675, 206.17291, 90.721692165923907,
     17102477.2496958388, 154.147366239113561, 2772035.6169917581,
     -0.89991282520302447, -0.89986892177110739, -1311796973197.995],
    [-50.56724, -16.30485, -105.439679907590164,
     -33.56571, -94.97412, -47.348547835650331,
     6455670.5118668696, 58.083719495371259, 5409150.7979815838,
     0.53053508035997263, 0.52988722644436602, 41071447902810.047],
    [-58.93002, -8.90775, 140.965397902500679,
     -8.91104, 133.13503, 19.255429433416599,
     11756066.0219864627, 105.755691241406877, 6151101.2270708536,
     -0.26548622269867183, -0.27068483874510741, -86143460552774.735],
    [-68.82867, -74.28391, 93.774347763114881,
     -50.63005, -8.36685, 34.65564085411343,
     3956936.926063544, 35.572254987389284, 3708890.9544062657,
     0.81443963736383502, 0.81420859815358342, -41845309450093.787],
    [-10.62672, -32.0898, -86.426713286747751,
     5.883, -134.31681, -80.473780971034875,
     11470869.3864563009, 103.387395634504061, 6184411.6622659713,
     -0.23138683500430237, -0.23155097622286792, 4198803992123.548],
    [-21.76221, 166.90563, 29.319421206936428,
     48.72884, 213.97627, 43.508671946410168,
     9098627.3986554915, 81.963476716121964, 6299240.9166992283,
     0.13965943368590333, 0.14152969707656796, 10024709850277.476],
    [-19.79938, -174.47484, 71.167275780171533,
     -11.99349, -154.35109, 65.589099775199228,
     2319004.8601169389, 20.896611684802389, 2267960.8703918325,
     0.93427001867125849, 0.93424887135032789, -3935477535005.785],
    [-11.95887, -116.94513, 92.712619830452549,
     4.57352, 7.16501, 78.64960934409585,
     13834722.5801401374, 124.688684161089762, 5228093.177931598,
     -0.56879356755666463, -0.56918731952397221, -9919582785894.853],
    [-87.85331, 85.66836, -65.120313040242748,
     66.48646, 16.09921, -4.888658719272296,
     17286615.3147144645, 155.58592449699137, 2635887.4729110181,
     -0.90697975771398578, -0.91095608883042767, 42667211366919.534],
    [1.74708, 128.32011, -101.584843631173858,
     -11.16617, 11.87109, -86.325793296437476,
     12942901.1241347408, 116.650512484301857, 5682744.8413270572,
     -0.44857868222697644, -0.44824490340007729, 10763055294345.653],
    [-25.72959, -144.90758, -153.647468693117198,
     -57.70581, -269.17879, -48.343983158876487,
     9413446.7452453107, 84.664533838404295, 6356176.6898881281,
     0.09492245755254703, 0.09737058264766572, 74515122850712.444],
    [-41.22777, 122.32875, 14.285113402275739,
     -7.57291, 130.37946, 10.805303085187369,
     3812686.035106021, 34.34330804743883, 3588703.8812128856,
     0.82605222593217889, 0.82572158200920196, -2456961531057.857],
    [11.01307, 138.25278, 79.43682622782374,
     6.62726, 247.05981, 103.708090215522657,
     11911190.819018408, 107.341669954114577, 6070904.722786735,
     -0.29767608923657404, -0.29785143390252321, 17121631423099.696],
    [-29.47124, 95.14681, -163.779130441688382,
     -27.46601, -69.15955, -15.909335945554969,
     13487015.8381145492, 121.294026715742277, 5481428.9945736388,
     -0.51527225545373252, -0.51556587964721788, 104679964020340.318]]

  def test_inverse(self):
    for l in GeodesicTest.testcases:
      (lat1, lon1, azi1, lat2, lon2, azi2,
       s12, a12, m12, M12, M21, S12) = l
      inv = Geodesic.WGS84.Inverse(lat1, lon1, lat2, lon2,
                     Geodesic.ALL | Geodesic.LONG_UNROLL)
      self.assertAlmostEqual(lon2, inv["lon2"], delta = 1e-13)
      self.assertAlmostEqual(azi1, inv["azi1"], delta = 1e-13)
      self.assertAlmostEqual(azi2, inv["azi2"], delta = 1e-13)
      self.assertAlmostEqual(s12, inv["s12"], delta = 1e-8)
      self.assertAlmostEqual(a12, inv["a12"], delta = 1e-13)
      self.assertAlmostEqual(m12, inv["m12"], delta = 1e-8)
      self.assertAlmostEqual(M12, inv["M12"], delta = 1e-15)
      self.assertAlmostEqual(M21, inv["M21"], delta = 1e-15)
      self.assertAlmostEqual(S12, inv["S12"], delta = 0.1)

  def test_direct(self):
    for l in GeodesicTest.testcases:
      (lat1, lon1, azi1, lat2, lon2, azi2,
       s12, a12, m12, M12, M21, S12) = l
      dir = Geodesic.WGS84.Direct(lat1, lon1, azi1, s12,
                    Geodesic.ALL | Geodesic.LONG_UNROLL)
      self.assertAlmostEqual(lat2, dir["lat2"], delta = 1e-13)
      self.assertAlmostEqual(lon2, dir["lon2"], delta = 1e-13)
      self.assertAlmostEqual(azi2, dir["azi2"], delta = 1e-13)
      self.assertAlmostEqual(a12, dir["a12"], delta = 1e-13)
      self.assertAlmostEqual(m12, dir["m12"], delta = 1e-8)
      self.assertAlmostEqual(M12, dir["M12"], delta = 1e-15)
      self.assertAlmostEqual(M21, dir["M21"], delta = 1e-15)
      self.assertAlmostEqual(S12, dir["S12"], delta = 0.1)

  def test_arcdirect(self):
    for l in GeodesicTest.testcases:
      (lat1, lon1, azi1, lat2, lon2, azi2,
       s12, a12, m12, M12, M21, S12) = l
      dir = Geodesic.WGS84.ArcDirect(lat1, lon1, azi1, a12,
                       Geodesic.ALL | Geodesic.LONG_UNROLL)
      self.assertAlmostEqual(lat2, dir["lat2"], delta = 1e-13)
      self.assertAlmostEqual(lon2, dir["lon2"], delta = 1e-13)
      self.assertAlmostEqual(azi2, dir["azi2"], delta = 1e-13)
      self.assertAlmostEqual(s12, dir["s12"], delta = 1e-8)
      self.assertAlmostEqual(m12, dir["m12"], delta = 1e-8)
      self.assertAlmostEqual(M12, dir["M12"], delta = 1e-15)
      self.assertAlmostEqual(M21, dir["M21"], delta = 1e-15)
      self.assertAlmostEqual(S12, dir["S12"], delta = 0.1)

class GeodSolveTest(unittest.TestCase):

  def test_GeodSolve0(self):
    inv = Geodesic.WGS84.Inverse(40.6, -73.8, 49.01666667, 2.55)
    self.assertAlmostEqual(inv["azi1"], 53.47022, delta = 0.5e-5)
    self.assertAlmostEqual(inv["azi2"], 111.59367, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 5853226, delta = 0.5)

  def test_GeodSolve1(self):
    dir = Geodesic.WGS84.Direct(40.63972222, -73.77888889, 53.5, 5850e3)
    self.assertAlmostEqual(dir["lat2"], 49.01467, delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon2"], 2.56106, delta = 0.5e-5)
    self.assertAlmostEqual(dir["azi2"], 111.62947, delta = 0.5e-5)

  def test_GeodSolve2(self):
    # Check fix for antipodal prolate bug found 2010-09-04
    geod = Geodesic(6.4e6, -1/150.0)
    inv = geod.Inverse(0.07476, 0, -0.07476, 180)
    self.assertAlmostEqual(inv["azi1"], 90.00078, delta = 0.5e-5)
    self.assertAlmostEqual(inv["azi2"], 90.00078, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 20106193, delta = 0.5)
    inv = geod.Inverse(0.1, 0, -0.1, 180)
    self.assertAlmostEqual(inv["azi1"], 90.00105, delta = 0.5e-5)
    self.assertAlmostEqual(inv["azi2"], 90.00105, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 20106193, delta = 0.5)

  def test_GeodSolve4(self):
    # Check fix for short line bug found 2010-05-21
    inv = Geodesic.WGS84.Inverse(36.493349428792, 0,
                   36.49334942879201, 0.0000008)
    self.assertAlmostEqual(inv["s12"], 0.072, delta = 0.5e-3)

  def test_GeodSolve5(self):
    # Check fix for point2=pole bug found 2010-05-03
    dir = Geodesic.WGS84.Direct(0.01777745589997, 30, 0, 10e6)
    self.assertAlmostEqual(dir["lat2"], 90, delta = 0.5e-5)
    if dir["lon2"] < 0:
      self.assertAlmostEqual(dir["lon2"], -150, delta = 0.5e-5)
      self.assertAlmostEqual(abs(dir["azi2"]), 180, delta = 0.5e-5)
    else:
      self.assertAlmostEqual(dir["lon2"], 30, delta = 0.5e-5)
      self.assertAlmostEqual(dir["azi2"], 0, delta = 0.5e-5)

  def test_GeodSolve6(self):
    # Check fix for volatile sbet12a bug found 2011-06-25 (gcc 4.4.4
    # x86 -O3).  Found again on 2012-03-27 with tdm-mingw32 (g++ 4.6.1).
    inv = Geodesic.WGS84.Inverse(88.202499451857, 0,
                   -88.202499451857, 179.981022032992859592)
    self.assertAlmostEqual(inv["s12"], 20003898.214, delta = 0.5e-3)
    inv = Geodesic.WGS84.Inverse(89.262080389218, 0,
                   -89.262080389218, 179.992207982775375662)
    self.assertAlmostEqual(inv["s12"], 20003925.854, delta = 0.5e-3)
    inv = Geodesic.WGS84.Inverse(89.333123580033, 0,
                   -89.333123580032997687,
                   179.99295812360148422)
    self.assertAlmostEqual(inv["s12"], 20003926.881, delta = 0.5e-3)

  def test_GeodSolve9(self):
    # Check fix for volatile x bug found 2011-06-25 (gcc 4.4.4 x86 -O3)
    inv = Geodesic.WGS84.Inverse(56.320923501171, 0,
                   -56.320923501171, 179.664747671772880215)
    self.assertAlmostEqual(inv["s12"], 19993558.287, delta = 0.5e-3)

  def test_GeodSolve10(self):
    # Check fix for adjust tol1_ bug found 2011-06-25 (Visual Studio
    # 10 rel + debug)
    inv = Geodesic.WGS84.Inverse(52.784459512564, 0,
                   -52.784459512563990912,
                   179.634407464943777557)
    self.assertAlmostEqual(inv["s12"], 19991596.095, delta = 0.5e-3)

  def test_GeodSolve11(self):
    # Check fix for bet2 = -bet1 bug found 2011-06-25 (Visual Studio
    # 10 rel + debug)
    inv = Geodesic.WGS84.Inverse(48.522876735459, 0,
                   -48.52287673545898293,
                   179.599720456223079643)
    self.assertAlmostEqual(inv["s12"], 19989144.774, delta = 0.5e-3)

  def test_GeodSolve12(self):
    # Check fix for inverse geodesics on extreme prolate/oblate
    # ellipsoids Reported 2012-08-29 Stefan Guenther
    # <stefan.gunther@embl.de>; fixed 2012-10-07
    geod = Geodesic(89.8, -1.83)
    inv = geod.Inverse(0, 0, -10, 160)
    self.assertAlmostEqual(inv["azi1"], 120.27, delta = 1e-2)
    self.assertAlmostEqual(inv["azi2"], 105.15, delta = 1e-2)
    self.assertAlmostEqual(inv["s12"], 266.7, delta = 1e-1)

  def test_GeodSolve14(self):
    # Check fix for inverse ignoring lon12 = nan
    inv = Geodesic.WGS84.Inverse(0, 0, 1, Math.nan)
    self.assertTrue(Math.isnan(inv["azi1"]))
    self.assertTrue(Math.isnan(inv["azi2"]))
    self.assertTrue(Math.isnan(inv["s12"]))

  def test_GeodSolve15(self):
    # Initial implementation of Math::eatanhe was wrong for e^2 < 0.  This
    # checks that this is fixed.
    geod = Geodesic(6.4e6, -1/150.0)
    dir = geod.Direct(1, 2, 3, 4, Geodesic.AREA)
    self.assertAlmostEqual(dir["S12"], 23700, delta = 0.5)

  def test_GeodSolve17(self):
    # Check fix for LONG_UNROLL bug found on 2015-05-07
    dir = Geodesic.WGS84.Direct(40, -75, -10, 2e7,
                  Geodesic.STANDARD | Geodesic.LONG_UNROLL)
    self.assertAlmostEqual(dir["lat2"], -39, delta = 1)
    self.assertAlmostEqual(dir["lon2"], -254, delta = 1)
    self.assertAlmostEqual(dir["azi2"], -170, delta = 1)
    line = Geodesic.WGS84.Line(40, -75, -10)
    dir = line.Position(2e7, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
    self.assertAlmostEqual(dir["lat2"], -39, delta = 1)
    self.assertAlmostEqual(dir["lon2"], -254, delta = 1)
    self.assertAlmostEqual(dir["azi2"], -170, delta = 1)
    dir = Geodesic.WGS84.Direct(40, -75, -10, 2e7)
    self.assertAlmostEqual(dir["lat2"], -39, delta = 1)
    self.assertAlmostEqual(dir["lon2"], 105, delta = 1)
    self.assertAlmostEqual(dir["azi2"], -170, delta = 1)
    dir = line.Position(2e7)
    self.assertAlmostEqual(dir["lat2"], -39, delta = 1)
    self.assertAlmostEqual(dir["lon2"], 105, delta = 1)
    self.assertAlmostEqual(dir["azi2"], -170, delta = 1)

  def test_GeodSolve26(self):
    # Check 0/0 problem with area calculation on sphere 2015-09-08
    geod = Geodesic(6.4e6, 0)
    inv = geod.Inverse(1, 2, 3, 4, Geodesic.AREA)
    self.assertAlmostEqual(inv["S12"], 49911046115.0, delta = 0.5)

  def test_GeodSolve28(self):
    # Check for bad placement of assignment of r.a12 with |f| > 0.01 (bug in
    # Java implementation fixed on 2015-05-19).
    geod = Geodesic(6.4e6, 0.1)
    dir = geod.Direct(1, 2, 10, 5e6)
    self.assertAlmostEqual(dir["a12"], 48.55570690, delta = 0.5e-8)

  def test_GeodSolve29(self):
    # Check longitude unrolling with inverse calculation 2015-09-16
    dir = Geodesic.WGS84.Inverse(0, 539, 0, 181)
    self.assertAlmostEqual(dir["lon1"], 179, delta = 1e-10)
    self.assertAlmostEqual(dir["lon2"], -179, delta = 1e-10)
    self.assertAlmostEqual(dir["s12"], 222639, delta = 0.5)
    dir = Geodesic.WGS84.Inverse(0, 539, 0, 181,
                   Geodesic.STANDARD | Geodesic.LONG_UNROLL)
    self.assertAlmostEqual(dir["lon1"], 539, delta = 1e-10)
    self.assertAlmostEqual(dir["lon2"], 541, delta = 1e-10)
    self.assertAlmostEqual(dir["s12"], 222639, delta = 0.5)

  def test_GeodSolve33(self):
    # Check max(-0.0,+0.0) issues 2015-08-22 (triggered by bugs in
    # Octave -- sind(-0.0) = +0.0 -- and in some version of Visual
    # Studio -- fmod(-0.0, 360.0) = +0.0.
    inv = Geodesic.WGS84.Inverse(0, 0, 0, 179)
    self.assertAlmostEqual(inv["azi1"], 90.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["azi2"], 90.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 19926189, delta = 0.5)
    inv = Geodesic.WGS84.Inverse(0, 0, 0, 179.5)
    self.assertAlmostEqual(inv["azi1"], 55.96650, delta = 0.5e-5)
    self.assertAlmostEqual(inv["azi2"], 124.03350, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 19980862, delta = 0.5)
    inv = Geodesic.WGS84.Inverse(0, 0, 0, 180)
    self.assertAlmostEqual(inv["azi1"], 0.00000, delta = 0.5e-5)
    self.assertAlmostEqual(abs(inv["azi2"]), 180.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 20003931, delta = 0.5)
    inv = Geodesic.WGS84.Inverse(0, 0, 1, 180)
    self.assertAlmostEqual(inv["azi1"], 0.00000, delta = 0.5e-5)
    self.assertAlmostEqual(abs(inv["azi2"]), 180.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 19893357, delta = 0.5)
    geod = Geodesic(6.4e6, 0)
    inv = geod.Inverse(0, 0, 0, 179)
    self.assertAlmostEqual(inv["azi1"], 90.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["azi2"], 90.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 19994492, delta = 0.5)
    inv = geod.Inverse(0, 0, 0, 180)
    self.assertAlmostEqual(inv["azi1"], 0.00000, delta = 0.5e-5)
    self.assertAlmostEqual(abs(inv["azi2"]), 180.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 20106193, delta = 0.5)
    inv = geod.Inverse(0, 0, 1, 180)
    self.assertAlmostEqual(inv["azi1"], 0.00000, delta = 0.5e-5)
    self.assertAlmostEqual(abs(inv["azi2"]), 180.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 19994492, delta = 0.5)
    geod = Geodesic(6.4e6, -1/300.0)
    inv = geod.Inverse(0, 0, 0, 179)
    self.assertAlmostEqual(inv["azi1"], 90.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["azi2"], 90.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 19994492, delta = 0.5)
    inv = geod.Inverse(0, 0, 0, 180)
    self.assertAlmostEqual(inv["azi1"], 90.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["azi2"], 90.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 20106193, delta = 0.5)
    inv = geod.Inverse(0, 0, 0.5, 180)
    self.assertAlmostEqual(inv["azi1"], 33.02493, delta = 0.5e-5)
    self.assertAlmostEqual(inv["azi2"], 146.97364, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 20082617, delta = 0.5)
    inv = geod.Inverse(0, 0, 1, 180)
    self.assertAlmostEqual(inv["azi1"], 0.00000, delta = 0.5e-5)
    self.assertAlmostEqual(abs(inv["azi2"]), 180.00000, delta = 0.5e-5)
    self.assertAlmostEqual(inv["s12"], 20027270, delta = 0.5)

  def test_GeodSolve55(self):
    # Check fix for nan + point on equator or pole not returning all nans in
    # Geodesic::Inverse, found 2015-09-23.
    inv = Geodesic.WGS84.Inverse(Math.nan, 0, 0, 90)
    self.assertTrue(Math.isnan(inv["azi1"]))
    self.assertTrue(Math.isnan(inv["azi2"]))
    self.assertTrue(Math.isnan(inv["s12"]))
    inv = Geodesic.WGS84.Inverse(Math.nan, 0, 90, 9)
    self.assertTrue(Math.isnan(inv["azi1"]))
    self.assertTrue(Math.isnan(inv["azi2"]))
    self.assertTrue(Math.isnan(inv["s12"]))

  def test_GeodSolve59(self):
    # Check for points close with longitudes close to 180 deg apart.
    inv = Geodesic.WGS84.Inverse(5, 0.00000000000001, 10, 180)
    self.assertAlmostEqual(inv["azi1"], 0.000000000000035, delta = 1.5e-14)
    self.assertAlmostEqual(inv["azi2"], 179.99999999999996, delta = 1.5e-14)
    self.assertAlmostEqual(inv["s12"], 18345191.174332713, delta = 5e-9)

  def test_GeodSolve61(self):
    # Make sure small negative azimuths are west-going
    dir = Geodesic.WGS84.Direct(45, 0, -0.000000000000000003, 1e7,
                  Geodesic.STANDARD | Geodesic.LONG_UNROLL)
    self.assertAlmostEqual(dir["lat2"], 45.30632, delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon2"], -180, delta = 0.5e-5)
    self.assertAlmostEqual(abs(dir["azi2"]), 180, delta = 0.5e-5)
    line = Geodesic.WGS84.InverseLine(45, 0, 80, -0.000000000000000003)
    dir = line.Position(1e7, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
    self.assertAlmostEqual(dir["lat2"], 45.30632, delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon2"], -180, delta = 0.5e-5)
    self.assertAlmostEqual(abs(dir["azi2"]), 180, delta = 0.5e-5)

  def test_GeodSolve65(self):
    # Check for bug in east-going check in GeodesicLine (needed to check for
    # sign of 0) and sign error in area calculation due to a bogus override
    # of the code for alp12.  Found/fixed on 2015-12-19.
    line = Geodesic.WGS84.InverseLine(30, -0.000000000000000001, -31, 180,
                                      Geodesic.ALL)
    dir = line.Position(1e7, Geodesic.ALL | Geodesic.LONG_UNROLL)
    self.assertAlmostEqual(dir["lat1"], 30.00000  , delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon1"], -0.00000  , delta = 0.5e-5)
    self.assertAlmostEqual(abs(dir["azi1"]), 180.00000, delta = 0.5e-5)
    self.assertAlmostEqual(dir["lat2"], -60.23169 , delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon2"], -0.00000  , delta = 0.5e-5)
    self.assertAlmostEqual(abs(dir["azi2"]), 180.00000, delta = 0.5e-5)
    self.assertAlmostEqual(dir["s12"] , 10000000  , delta = 0.5)
    self.assertAlmostEqual(dir["a12"] , 90.06544  , delta = 0.5e-5)
    self.assertAlmostEqual(dir["m12"] , 6363636   , delta = 0.5)
    self.assertAlmostEqual(dir["M12"] , -0.0012834, delta = 0.5e7)
    self.assertAlmostEqual(dir["M21"] , 0.0013749 , delta = 0.5e-7)
    self.assertAlmostEqual(dir["S12"] , 0         , delta = 0.5)
    dir = line.Position(2e7, Geodesic.ALL | Geodesic.LONG_UNROLL)
    self.assertAlmostEqual(dir["lat1"], 30.00000  , delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon1"], -0.00000  , delta = 0.5e-5)
    self.assertAlmostEqual(abs(dir["azi1"]), 180.00000, delta = 0.5e-5)
    self.assertAlmostEqual(dir["lat2"], -30.03547 , delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon2"], -180.00000, delta = 0.5e-5)
    self.assertAlmostEqual(dir["azi2"], -0.00000  , delta = 0.5e-5)
    self.assertAlmostEqual(dir["s12"] , 20000000  , delta = 0.5)
    self.assertAlmostEqual(dir["a12"] , 179.96459 , delta = 0.5e-5)
    self.assertAlmostEqual(dir["m12"] , 54342     , delta = 0.5)
    self.assertAlmostEqual(dir["M12"] , -1.0045592, delta = 0.5e7)
    self.assertAlmostEqual(dir["M21"] , -0.9954339, delta = 0.5e-7)
    self.assertAlmostEqual(dir["S12"] , 127516405431022.0, delta = 0.5)

  def test_GeodSolve66(self):
    # Check for InverseLine if line is slightly west of S and that s13 is
    # correctly set.
    line = Geodesic.WGS84.InverseLine(-5, -0.000000000000002, -10, 180)
    dir = line.Position(2e7, Geodesic.STANDARD | Geodesic.LONG_UNROLL)
    self.assertAlmostEqual(dir["lat2"], 4.96445   , delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon2"], -180.00000, delta = 0.5e-5)
    self.assertAlmostEqual(dir["azi2"], -0.00000  , delta = 0.5e-5)
    dir = line.Position(0.5 * line.s13,
                        Geodesic.STANDARD | Geodesic.LONG_UNROLL)
    self.assertAlmostEqual(dir["lat2"], -87.52461 , delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon2"], -0.00000  , delta = 0.5e-5)
    self.assertAlmostEqual(dir["azi2"], -180.00000, delta = 0.5e-5)

  def test_GeodSolve71(self):
    # Check that DirectLine sets s13.
    line = Geodesic.WGS84.DirectLine(1, 2, 45, 1e7)
    dir = line.Position(0.5 * line.s13,
                        Geodesic.STANDARD | Geodesic.LONG_UNROLL)
    self.assertAlmostEqual(dir["lat2"], 30.92625, delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon2"], 37.54640, delta = 0.5e-5)
    self.assertAlmostEqual(dir["azi2"], 55.43104, delta = 0.5e-5)

  def test_GeodSolve73(self):
    # Check for backwards from the pole bug reported by Anon on 2016-02-13.
    # This only affected the Java implementation.  It was introduced in Java
    # version 1.44 and fixed in 1.46-SNAPSHOT on 2016-01-17.
    # Also the + sign on azi2 is a check on the normalizing of azimuths
    # (converting -0.0 to +0.0).
    dir = Geodesic.WGS84.Direct(90, 10, 180, -1e6)
    self.assertAlmostEqual(dir["lat2"], 81.04623, delta = 0.5e-5)
    self.assertAlmostEqual(dir["lon2"], -170, delta = 0.5e-5)
    self.assertAlmostEqual(dir["azi2"], 0, delta = 0.5e-5)
    self.assertTrue(Math.copysign(1, dir["azi2"]) > 0)

  def test_GeodSolve74(self):
    # Check fix for inaccurate areas, bug introduced in v1.46, fixed
    # 2015-10-16.
    inv = Geodesic.WGS84.Inverse(54.1589, 15.3872, 54.1591, 15.3877,
                                 Geodesic.ALL)
    self.assertAlmostEqual(inv["azi1"], 55.723110355, delta = 5e-9)
    self.assertAlmostEqual(inv["azi2"], 55.723515675, delta = 5e-9)
    self.assertAlmostEqual(inv["s12"],  39.527686385, delta = 5e-9)
    self.assertAlmostEqual(inv["a12"],   0.000355495, delta = 5e-9)
    self.assertAlmostEqual(inv["m12"],  39.527686385, delta = 5e-9)
    self.assertAlmostEqual(inv["M12"],   0.999999995, delta = 5e-9)
    self.assertAlmostEqual(inv["M21"],   0.999999995, delta = 5e-9)
    self.assertAlmostEqual(inv["S12"], 286698586.30197, delta = 5e-4)

  def test_GeodSolve76(self):
    # The distance from Wellington and Salamanca (a classic failure of
    # Vincenty)
    inv = Geodesic.WGS84.Inverse(-(41+19/60.0), 174+49/60.0,
                                 40+58/60.0, -(5+30/60.0))
    self.assertAlmostEqual(inv["azi1"], 160.39137649664, delta = 0.5e-11)
    self.assertAlmostEqual(inv["azi2"],  19.50042925176, delta = 0.5e-11)
    self.assertAlmostEqual(inv["s12"],  19960543.857179, delta = 0.5e-6)

  def test_GeodSolve78(self):
    # An example where the NGS calculator fails to converge
    inv = Geodesic.WGS84.Inverse(27.2, 0.0, -27.1, 179.5)
    self.assertAlmostEqual(inv["azi1"],  45.82468716758, delta = 0.5e-11)
    self.assertAlmostEqual(inv["azi2"], 134.22776532670, delta = 0.5e-11)
    self.assertAlmostEqual(inv["s12"],  19974354.765767, delta = 0.5e-6)

  def test_GeodSolve80(self):
    # Some tests to add code coverage: computing scale in special cases + zero
    # length geodesic (includes GeodSolve80 - GeodSolve83) + using an incapable
    # line.
    inv = Geodesic.WGS84.Inverse(0, 0, 0, 90, Geodesic.GEODESICSCALE)
    self.assertAlmostEqual(inv["M12"], -0.00528427534, delta = 0.5e-10)
    self.assertAlmostEqual(inv["M21"], -0.00528427534, delta = 0.5e-10)

    inv = Geodesic.WGS84.Inverse(0, 0, 1e-6, 1e-6, Geodesic.GEODESICSCALE)
    self.assertAlmostEqual(inv["M12"], 1, delta = 0.5e-10)
    self.assertAlmostEqual(inv["M21"], 1, delta = 0.5e-10)

    inv = Geodesic.WGS84.Inverse(20.001, 0, 20.001, 0, Geodesic.ALL)
    self.assertAlmostEqual(inv["a12"], 0, delta = 1e-13)
    self.assertAlmostEqual(inv["s12"], 0, delta = 1e-8)
    self.assertAlmostEqual(inv["azi1"], 180, delta = 1e-13)
    self.assertAlmostEqual(inv["azi2"], 180, delta = 1e-13)
    self.assertAlmostEqual(inv["m12"], 0, delta =  1e-8)
    self.assertAlmostEqual(inv["M12"], 1, delta = 1e-15)
    self.assertAlmostEqual(inv["M21"], 1, delta = 1e-15)
    self.assertAlmostEqual(inv["S12"], 0, delta = 1e-10)
    self.assertTrue(Math.copysign(1, inv["a12"]) > 0)
    self.assertTrue(Math.copysign(1, inv["s12"]) > 0)
    self.assertTrue(Math.copysign(1, inv["m12"]) > 0)

    inv = Geodesic.WGS84.Inverse(90, 0, 90, 180, Geodesic.ALL)
    self.assertAlmostEqual(inv["a12"], 0, delta = 1e-13)
    self.assertAlmostEqual(inv["s12"], 0, delta = 1e-8)
    self.assertAlmostEqual(inv["azi1"], 0, delta = 1e-13)
    self.assertAlmostEqual(inv["azi2"], 180, delta = 1e-13)
    self.assertAlmostEqual(inv["m12"], 0, delta = 1e-8)
    self.assertAlmostEqual(inv["M12"], 1, delta = 1e-15)
    self.assertAlmostEqual(inv["M21"], 1, delta = 1e-15)
    self.assertAlmostEqual(inv["S12"], 127516405431022.0, delta = 0.5)

    # An incapable line which can't take distance as input
    line = Geodesic.WGS84.Line(1, 2, 90, Geodesic.LATITUDE)
    dir = line.Position(1000, Geodesic.EMPTY)
    self.assertTrue(Math.isnan(dir["a12"]))

  def test_GeodSolve84(self):
    # Tests for python implementation to check fix for range errors with
    # {fmod,sin,cos}(inf) (includes GeodSolve84 - GeodSolve91).
    dir = Geodesic.WGS84.Direct(0, 0, 90, Math.inf)
    self.assertTrue(Math.isnan(dir["lat2"]))
    self.assertTrue(Math.isnan(dir["lon2"]))
    self.assertTrue(Math.isnan(dir["azi2"]))
    dir = Geodesic.WGS84.Direct(0, 0, 90, Math.nan)
    self.assertTrue(Math.isnan(dir["lat2"]))
    self.assertTrue(Math.isnan(dir["lon2"]))
    self.assertTrue(Math.isnan(dir["azi2"]))
    dir = Geodesic.WGS84.Direct(0, 0, Math.inf, 1000)
    self.assertTrue(Math.isnan(dir["lat2"]))
    self.assertTrue(Math.isnan(dir["lon2"]))
    self.assertTrue(Math.isnan(dir["azi2"]))
    dir = Geodesic.WGS84.Direct(0, 0, Math.nan, 1000)
    self.assertTrue(Math.isnan(dir["lat2"]))
    self.assertTrue(Math.isnan(dir["lon2"]))
    self.assertTrue(Math.isnan(dir["azi2"]))
    dir = Geodesic.WGS84.Direct(0, Math.inf, 90, 1000)
    self.assertTrue(dir["lat1"] == 0)
    self.assertTrue(Math.isnan(dir["lon2"]))
    self.assertTrue(dir["azi2"] == 90)
    dir = Geodesic.WGS84.Direct(0, Math.nan, 90, 1000)
    self.assertTrue(dir["lat1"] == 0)
    self.assertTrue(Math.isnan(dir["lon2"]))
    self.assertTrue(dir["azi2"] == 90)
    dir = Geodesic.WGS84.Direct(Math.inf, 0, 90, 1000)
    self.assertTrue(Math.isnan(dir["lat2"]))
    self.assertTrue(Math.isnan(dir["lon2"]))
    self.assertTrue(Math.isnan(dir["azi2"]))
    dir = Geodesic.WGS84.Direct(Math.nan, 0, 90, 1000)
    self.assertTrue(Math.isnan(dir["lat2"]))
    self.assertTrue(Math.isnan(dir["lon2"]))
    self.assertTrue(Math.isnan(dir["azi2"]))

  def test_GeodSolve92(self):
    # Check fix for inaccurate hypot with python 3.[89].  Problem reported
    # by agdhruv https://github.com/geopy/geopy/issues/466 ; see
    # https://bugs.python.org/issue43088
    inv = Geodesic.WGS84.Inverse(37.757540000000006, -122.47018,
                                 37.75754,           -122.470177)
    self.assertAlmostEqual(inv["azi1"], 89.99999923, delta = 1e-7  )
    self.assertAlmostEqual(inv["azi2"], 90.00000106, delta = 1e-7  )
    self.assertAlmostEqual(inv["s12"],   0.264,      delta = 0.5e-3)

class PlanimeterTest(unittest.TestCase):

  polygon = Geodesic.WGS84.Polygon(False)
  polyline = Geodesic.WGS84.Polygon(True)

  def Planimeter(points):
    PlanimeterTest.polygon.Clear()
    for p in points:
      PlanimeterTest.polygon.AddPoint(p[0], p[1])
    return PlanimeterTest.polygon.Compute(False, True)
  Planimeter = staticmethod(Planimeter)

  def PolyLength(points):
    PlanimeterTest.polyline.Clear()
    for p in points:
      PlanimeterTest.polyline.AddPoint(p[0], p[1])
    return PlanimeterTest.polyline.Compute(False, True)
  PolyLength = staticmethod(PolyLength)

  def test_Planimeter0(self):
    # Check fix for pole-encircling bug found 2011-03-16
    points = [[89, 0], [89, 90], [89, 180], [89, 270]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 631819.8745, delta = 1e-4)
    self.assertAlmostEqual(area, 24952305678.0, delta = 1)
    points = [[-89, 0], [-89, 90], [-89, 180], [-89, 270]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 631819.8745, delta = 1e-4)
    self.assertAlmostEqual(area, -24952305678.0, delta = 1)

    points = [[0, -1], [-1, 0], [0, 1], [1, 0]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 627598.2731, delta = 1e-4)
    self.assertAlmostEqual(area, 24619419146.0, delta = 1)

    points = [[90, 0], [0, 0], [0, 90]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 30022685, delta = 1)
    self.assertAlmostEqual(area, 63758202715511.0, delta = 1)
    num, perimeter, area = PlanimeterTest.PolyLength(points)
    self.assertAlmostEqual(perimeter, 20020719, delta = 1)
    self.assertTrue(Math.isnan(area))

  def test_Planimeter5(self):
    # Check fix for Planimeter pole crossing bug found 2011-06-24
    points = [[89, 0.1], [89, 90.1], [89, -179.9]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 539297, delta = 1)
    self.assertAlmostEqual(area, 12476152838.5, delta = 1)

  def test_Planimeter6(self):
    # Check fix for Planimeter lon12 rounding bug found 2012-12-03
    points = [[9, -0.00000000000001], [9, 180], [9, 0]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 36026861, delta = 1)
    self.assertAlmostEqual(area, 0, delta = 1)
    points = [[9, 0.00000000000001], [9, 0], [9, 180]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 36026861, delta = 1)
    self.assertAlmostEqual(area, 0, delta = 1)
    points = [[9, 0.00000000000001], [9, 180], [9, 0]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 36026861, delta = 1)
    self.assertAlmostEqual(area, 0, delta = 1)
    points = [[9, -0.00000000000001], [9, 0], [9, 180]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 36026861, delta = 1)
    self.assertAlmostEqual(area, 0, delta = 1)

  def test_Planimeter12(self):
    # Area of arctic circle (not really -- adjunct to rhumb-area test)
    points = [[66.562222222, 0], [66.562222222, 180]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 10465729, delta = 1)
    self.assertAlmostEqual(area, 0, delta = 1)

  def test_Planimeter13(self):
    # Check encircling pole twice
    points = [[89,-360], [89,-240], [89,-120], [89,0], [89,120], [89,240]]
    num, perimeter, area = PlanimeterTest.Planimeter(points)
    self.assertAlmostEqual(perimeter, 1160741, delta = 1)
    self.assertAlmostEqual(area, 32415230256.0, delta = 1)

  def test_Planimeter15(self):
    # Coverage tests, includes Planimeter15 - Planimeter18 (combinations of
    # reverse and sign) + calls to testpoint, testedge.
    lat = [2, 1, 3]
    lon = [1, 2, 3]
    r = 18454562325.45119
    a0 = 510065621724088.5093   # ellipsoid area
    PlanimeterTest.polygon.Clear()
    PlanimeterTest.polygon.AddPoint(lat[0], lon[0])
    PlanimeterTest.polygon.AddPoint(lat[1], lon[1])
    num, perimeter, area = PlanimeterTest.polygon.TestPoint(lat[2], lon[2],
                                                            False, True)
    self.assertAlmostEqual(area, r, delta = 0.5)
    num, perimeter, area = PlanimeterTest.polygon.TestPoint(lat[2], lon[2],
                                                            False, False)
    self.assertAlmostEqual(area, r, delta = 0.5)
    num, perimeter, area = PlanimeterTest.polygon.TestPoint(lat[2], lon[2],
                                                            True, True)
    self.assertAlmostEqual(area, -r, delta = 0.5)
    num, perimeter, area = PlanimeterTest.polygon.TestPoint(lat[2], lon[2],
                                                            True, False)
    self.assertAlmostEqual(area, a0-r, delta = 0.5)
    inv = Geodesic.WGS84.Inverse(lat[1], lon[1], lat[2], lon[2])
    azi1 = inv["azi1"]
    s12 = inv["s12"]
    num, perimeter, area = PlanimeterTest.polygon.TestEdge(azi1, s12,
                                                           False, True)
    self.assertAlmostEqual(area, r, delta = 0.5)
    num, perimeter, area = PlanimeterTest.polygon.TestEdge(azi1, s12,
                                                           False, False)
    self.assertAlmostEqual(area, r, delta = 0.5)
    num, perimeter, area = PlanimeterTest.polygon.TestEdge(azi1, s12,
                                                           True, True)
    self.assertAlmostEqual(area, -r, delta = 0.5)
    num, perimeter, area = PlanimeterTest.polygon.TestEdge(azi1, s12,
                                                           True, False)
    self.assertAlmostEqual(area, a0-r, delta = 0.5)
    PlanimeterTest.polygon.AddPoint(lat[2], lon[2])
    num, perimeter, area = PlanimeterTest.polygon.Compute(False, True)
    self.assertAlmostEqual(area, r, delta = 0.5)
    num, perimeter, area = PlanimeterTest.polygon.Compute(False, False)
    self.assertAlmostEqual(area, r, delta = 0.5)
    num, perimeter, area = PlanimeterTest.polygon.Compute(True, True)
    self.assertAlmostEqual(area, -r, delta = 0.5)
    num, perimeter, area = PlanimeterTest.polygon.Compute(True, False)
    self.assertAlmostEqual(area, a0-r, delta = 0.5)

  def test_Planimeter19(self):
    # Coverage tests, includes Planimeter19 - Planimeter20 (degenerate
    # polygons) + extra cases.
    PlanimeterTest.polygon.Clear()
    num, perimeter, area = PlanimeterTest.polygon.Compute(False, True)
    self.assertTrue(area == 0)
    self.assertTrue(perimeter == 0)
    num, perimeter, area = PlanimeterTest.polygon.TestPoint(1, 1,
                                                            False, True)
    self.assertTrue(area == 0)
    self.assertTrue(perimeter == 0)
    num, perimeter, area = PlanimeterTest.polygon.TestEdge(90, 1000,
                                                           False, True)
    self.assertTrue(Math.isnan(area))
    self.assertTrue(Math.isnan(perimeter))
    PlanimeterTest.polygon.AddPoint(1, 1)
    num, perimeter, area = PlanimeterTest.polygon.Compute(False, True)
    self.assertTrue(area == 0)
    self.assertTrue(perimeter == 0)
    PlanimeterTest.polyline.Clear()
    num, perimeter, area = PlanimeterTest.polyline.Compute(False, True)
    self.assertTrue(perimeter == 0)
    num, perimeter, area = PlanimeterTest.polyline.TestPoint(1, 1,
                                                             False, True)
    self.assertTrue(perimeter == 0)
    num, perimeter, area = PlanimeterTest.polyline.TestEdge(90, 1000,
                                                            False, True)
    self.assertTrue(Math.isnan(perimeter))
    PlanimeterTest.polyline.AddPoint(1, 1)
    num, perimeter, area = PlanimeterTest.polyline.Compute(False, True)
    self.assertTrue(perimeter == 0)
    PlanimeterTest.polygon.AddPoint(1, 1)
    num, perimeter, area = PlanimeterTest.polyline.TestEdge(90, 1000,
                                                            False, True)
    self.assertAlmostEqual(perimeter, 1000, delta = 1e-10)
    num, perimeter, area = PlanimeterTest.polyline.TestPoint(2, 2,
                                                             False, True)
    self.assertAlmostEqual(perimeter, 156876.149, delta = 0.5e-3)

  def test_Planimeter21(self):
    # Some test to add code coverage: multiple circlings of pole (includes
    # Planimeter21 - Planimeter28) + invocations via testpoint and testedge.
    lat = 45
    azi = 39.2144607176828184218
    s = 8420705.40957178156285
    r = 39433884866571.4277     # Area for one circuit
    a0 = 510065621724088.5093   # Ellipsoid area
    PlanimeterTest.polygon.Clear()
    PlanimeterTest.polygon.AddPoint(lat,  60)
    PlanimeterTest.polygon.AddPoint(lat, 180)
    PlanimeterTest.polygon.AddPoint(lat, -60)
    PlanimeterTest.polygon.AddPoint(lat,  60)
    PlanimeterTest.polygon.AddPoint(lat, 180)
    PlanimeterTest.polygon.AddPoint(lat, -60)
    for i in [3, 4]:
      PlanimeterTest.polygon.AddPoint(lat,  60)
      PlanimeterTest.polygon.AddPoint(lat, 180)
      num, perimeter, area = PlanimeterTest.polygon.TestPoint(lat, -60,
                                                              False, True)
      self.assertAlmostEqual(area,  i*r, delta = 0.5)
      num, perimeter, area = PlanimeterTest.polygon.TestPoint(lat, -60,
                                                              False, False)
      self.assertAlmostEqual(area,  i*r, delta = 0.5)
      num, perimeter, area = PlanimeterTest.polygon.TestPoint(lat, -60,
                                                              True, True)
      self.assertAlmostEqual(area, -i*r, delta = 0.5)
      num, perimeter, area = PlanimeterTest.polygon.TestPoint(lat, -60,
                                                              True, False)
      self.assertAlmostEqual(area, -i*r + a0, delta = 0.5)
      num, perimeter, area = PlanimeterTest.polygon.TestEdge(azi, s,
                                                             False, True)
      self.assertAlmostEqual(area,  i*r, delta = 0.5)
      num, perimeter, area = PlanimeterTest.polygon.TestEdge(azi, s,
                                                             False, False)
      self.assertAlmostEqual(area,  i*r, delta = 0.5)
      num, perimeter, area = PlanimeterTest.polygon.TestEdge(azi, s,
                                                             True, True)
      self.assertAlmostEqual(area, -i*r, delta = 0.5)
      num, perimeter, area = PlanimeterTest.polygon.TestEdge(azi, s,
                                                             True, False)
      self.assertAlmostEqual(area, -i*r + a0, delta = 0.5)
      PlanimeterTest.polygon.AddPoint(lat, -60)
      num, perimeter, area = PlanimeterTest.polygon.Compute(False, True)
      self.assertAlmostEqual(area,  i*r, delta = 0.5)
      num, perimeter, area = PlanimeterTest.polygon.Compute(False, False)
      self.assertAlmostEqual(area,  i*r, delta = 0.5)
      num, perimeter, area = PlanimeterTest.polygon.Compute(True, True)
      self.assertAlmostEqual(area, -i*r, delta = 0.5)
      num, perimeter, area = PlanimeterTest.polygon.Compute(True, False)
      self.assertAlmostEqual(area, -i*r + a0, delta = 0.5)

  def test_Planimeter29(self):
    # Check fix to transitdirect vs transit zero handling inconsistency
    PlanimeterTest.polygon.Clear()
    PlanimeterTest.polygon.AddPoint(0, 0)
    PlanimeterTest.polygon.AddEdge( 90, 1000)
    PlanimeterTest.polygon.AddEdge(  0, 1000)
    PlanimeterTest.polygon.AddEdge(-90, 1000)
    num, perimeter, area = PlanimeterTest.polygon.Compute(False, True)
    # The area should be 1e6.  Prior to the fix it was 1e6 - A/2, where
    # A = ellipsoid area.
    self.assertAlmostEqual(area, 1000000.0, delta = 0.01)
