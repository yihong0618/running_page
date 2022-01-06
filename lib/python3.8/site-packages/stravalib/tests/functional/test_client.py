from __future__ import division, absolute_import, print_function, unicode_literals

from stravalib import model, attributes, exc, unithelper as uh
from stravalib.client import Client
from stravalib.tests.functional import FunctionalTestBase
import datetime
import requests


class ClientTest(FunctionalTestBase):
    def test_get_starred_segment(self):
        """
        Test get_starred_segment
        """
        i = 0
        for segment in self.client.get_starred_segment(limit=5):
            self.assertIsInstance(segment, model.Segment)
            i+=1
        self.assertGreater(i, 0) # star at least one segment
        self.assertLessEqual(i, 5)


    def test_get_activity(self):
        """ Test basic activity fetching. """
        activity = self.client.get_activity(96089609)
        self.assertEqual('El Dorado County, CA, USA', activity.location_city)

        self.assertIsInstance(activity.start_latlng, attributes.LatLon)
        self.assertAlmostEqual(-120.4357631, activity.start_latlng.lon, places=2)
        self.assertAlmostEqual(38.74263759999999, activity.start_latlng.lat, places=2)

        self.assertIsInstance(activity.map, model.Map)

        self.assertIsInstance(activity.athlete, model.Athlete)
        self.assertEqual(1513, activity.athlete.id)

        #self.assertAlmostEqual(first, second, places, msg, delta)
        # Ensure that iw as read in with correct units
        self.assertEqual(22.5308, float(uh.kilometers(activity.distance)))

    def test_get_activity_and_segments(self):
        """ Test include_all_efforts parameter on activity fetching. """
        if not self.activity_id:
            self.fail("Include an activity_id in test.ini to test segment_efforts")

        activity = self.client.get_activity(self.activity_id, include_all_efforts=True)
        self.assertTrue(isinstance(activity.segment_efforts, list))

        # Check also when we have no parameters segment_efforts is None
        activity_no_segments = self.client.get_activity(self.activity_id)
        self.assertTrue(activity.segment_efforts, None)

    def test_get_route(self):
        route = self.client.get_route(3445913)

        self.assertEqual('Baveno - Mottarone', route.name)
        self.assertAlmostEqual(1265.20, float(uh.meters(route.elevation_gain)), 2)

    def test_get_activity_laps(self):
        activity = self.client.get_activity(165094211)
        laps = list(self.client.get_activity_laps(165094211))
        self.assertEqual(5, len(laps))
        # This obviously is far from comprehensive, just a sanity check
        self.assertEqual(u'Lap 1', laps[0].name)
        self.assertEqual(178.0, laps[0].max_heartrate)


    def test_get_activity_zones(self):
        """
        Test loading zones for activity.
        """
        zones = self.client.get_activity_zones(99895560)
        print(zones)
        self.assertEqual(1, len(zones))
        self.assertIsInstance(zones[0], model.PaceActivityZone)

        # Indirectly
        activity = self.client.get_activity(99895560)
        self.assertEqual(len(zones), len(activity.zones))
        self.assertEqual(zones[0].score, activity.zones[0].score)

    def test_activity_comments(self):
        """
        Test loading comments for already-loaded activity.
        """
        activity = self.client.get_activity(2290897)
        self.assertTrue(activity.comment_count > 0)
        comments= list(activity.comments)
        self.assertEqual(3, len(comments))
        self.assertEqual("I love Gordo's. I've been eating there for 20 years!", comments[0].text)

    def test_activity_photos(self):
        """
        Test photos on activity
        """
        activity = self.client.get_activity(643026323)
        self.assertTrue(activity.total_photo_count > 0)
        photos = list(activity.full_photos)
        self.assertEqual(len(photos), 1)
        self.assertEqual(len(photos), activity.total_photo_count)
        self.assertIsInstance(photos[0], model.ActivityPhoto)

    def test_activity_kudos(self):
        """
        Test kudos on activity
        """
        activity = self.client.get_activity(152668627)
        self.assertTrue(activity.kudos_count > 0)
        kudos = list(activity.kudos)
        self.assertGreater(len(kudos), 6)
        self.assertEqual(len(kudos), activity.kudos_count)
        self.assertIsInstance(kudos[0], model.ActivityKudos )

    def test_activity_streams(self):
        """
        Test activity streams
        """
        stypes = ['time', 'latlng', 'distance','altitude', 'velocity_smooth',
                  'heartrate', 'cadence', 'watts', 'temp', 'moving',
                  'grade_smooth']

        streams = self.client.get_activity_streams(152668627, stypes, 'low')

        self.assertGreater(len(streams.keys()), 3)
        for k in streams.keys():
            self.assertIn(k, stypes)

        # time stream
        self.assertIsInstance(streams['time'].data[0], int)
        self.assertGreater(streams['time'].original_size, 100)
        self.assertEqual(streams['time'].resolution, 'low')
        self.assertEqual(len(streams['time'].data), 100)

        # latlng stream
        self.assertIsInstance(streams['latlng'].data, list)
        self.assertIsInstance(streams['latlng'].data[0][0], float)

    def test_route_streams(self):
        """
        Test toute streams
        """
        stypes = ['latlng', 'distance', 'altitude']

        streams = self.client.get_route_streams(3445913)
        self.assertEqual(len(streams.keys()), 3)

        for t in stypes:
            self.assertIn(t, streams.keys())

    def test_related_activities(self):
        """
        Test get_related_activities on an activity and related property of Activity
        """
        activity_id = 152668627
        activity = self.client.get_activity(activity_id)
        related_activities = list(self.client.get_related_activities(activity_id))

        # Check the number of related_activities matches what activity would expect
        self.assertEqual(len(related_activities), activity.athlete_count-1)

        # Check the related property gives the same result
        related_activities_from_property = list(activity.related)
        self.assertEqual(related_activities, related_activities_from_property)

    def test_effort_streams(self):
        """
        Test effort streams
        """
        stypes = ['distance']

        activity = self.client.get_activity(165479860) #152668627)
        streams = self.client.get_effort_streams(activity.segment_efforts[0].id,
                                                stypes, 'medium')


        self.assertIn('distance', streams.keys())

        # distance stream
        self.assertIsInstance(streams['distance'].data[0], float) #xxx
        self.assertEqual(streams['distance'].resolution, 'medium')
        self.assertEqual(len(streams['distance'].data),
                         min(1000, streams['distance'].original_size))

    def test_get_curr_athlete(self):
        athlete = self.client.get_athlete()

        # Just some basic sanity checks here
        self.assertTrue(len(athlete.firstname) > 0)

        self.assertTrue(athlete.athlete_type in ["runner", "cyclist"])

    def test_get_athlete_clubs(self):
        clubs = self.client.get_athlete_clubs()
        self.assertEqual(3, len(clubs))
        self.assertEqual('Team Roaring Mouse', clubs[0].name)
        self.assertEqual('Team Strava Cycling', clubs[1].name)
        self.assertEqual('Team Strava Cyclocross', clubs[2].name)

        clubs_indirect = self.client.get_athlete().clubs
        self.assertEqual(3, len(clubs_indirect))
        self.assertEqual(clubs[0].name, clubs_indirect[0].name)
        self.assertEqual(clubs[1].name, clubs_indirect[1].name)
        self.assertEqual(clubs[2].name, clubs_indirect[2].name)

    def test_get_gear(self):
        g = self.client.get_gear("g69911")
        self.assertTrue(float(g.distance) >= 3264.67)
        self.assertEqual('Salomon XT Wings 2', g.name)
        self.assertEqual('Salomon', g.brand_name)
        self.assertTrue(g.primary)
        self.assertEqual(model.DETAILED, g.resource_state)
        self.assertEqual('g69911', g.id)
        self.assertEqual('XT Wings 2', g.model_name)
        self.assertEqual('', g.description)

    def test_get_segment_leaderboard(self):
        lb = self.client.get_segment_leaderboard(229781)
        print(lb.effort_count)
        print(lb.entry_count)
        for i,e in enumerate(lb):
            print('{0}: {1}'.format(i, e))

        self.assertEqual(10, len(lb.entries)) # 10 top results
        self.assertIsInstance(lb.entries[0], model.SegmentLeaderboardEntry)
        self.assertEqual(1, lb.entries[0].rank)
        self.assertTrue(lb.effort_count > 8000) # At time of writing 8206

        # Check the relationships
        athlete = lb[0].athlete
        print(athlete)
        self.assertEqual(lb[0].athlete_name, "{0} {1}".format(athlete.firstname, athlete.lastname))

        effort = lb[0].effort
        print(effort)
        self.assertIsInstance(effort, model.SegmentEffort)
        self.assertEqual('Hawk Hill', effort.name)

        activity = lb[0].activity
        self.assertIsInstance(activity, model.Activity)
        # Can't assert much since #1 ranked activity will likely change in the future.

    def test_get_segment(self):
        segment = self.client.get_segment(229781)
        self.assertIsInstance(segment, model.Segment)
        print(segment)
        self.assertEqual('Hawk Hill', segment.name)
        self.assertAlmostEqual(2.68, float(uh.kilometers(segment.distance)), places=2)

        # Fetch leaderboard
        lb = segment.leaderboard
        self.assertEqual(10, len(lb)) # 10 top results, 5 bottom results

    def test_get_segment_efforts(self):
        # test with string
        efforts = self.client.get_segment_efforts(4357415,
                                     start_date_local = "2012-12-23T00:00:00Z",
                                     end_date_local   = "2012-12-23T11:00:00Z",)
        print(efforts)

        i = 0
        for effort in efforts:
            print(effort)
            self.assertEqual(4357415, effort.segment.id)
            self.assertIsInstance(effort, model.BaseEffort)
            effort_date = effort.start_date_local
            self.assertEqual(effort_date.strftime("%Y-%m-%d"), "2012-12-23")
            i+=1
        print(i)

        self.assertGreater(i, 2)

        # also test with datetime object
        start_date = datetime.datetime(2012, 12, 31, 6, 0)
        end_date = start_date + datetime.timedelta(hours=12)
        efforts = self.client.get_segment_efforts(4357415,
                                        start_date_local = start_date,
                                        end_date_local = end_date,)
        print(efforts)

        i = 0
        for effort in efforts:
            print(effort)
            self.assertEqual(4357415, effort.segment.id)
            self.assertIsInstance(effort, model.BaseEffort)
            effort_date = effort.start_date_local
            self.assertEqual(effort_date.strftime("%Y-%m-%d"), "2012-12-31")
            i+=1
        print(i)

        self.assertGreater(i, 2)

    def test_segment_explorer(self):
        bounds = (37.821362,-122.505373,37.842038,-122.465977)
        results = self.client.explore_segments(bounds)

        # This might be brittle
        self.assertEqual('Hawk Hill', results[0].name)

        # Fetch full segment
        segment = results[0].segment
        self.assertEqual(results[0].name, segment.name)

        # For some reason these don't follow the simple math rules one might expect (so we round to int)
        self.assertAlmostEqual(results[0].elev_difference, segment.elevation_high - segment.elevation_low, places=0)


class AuthenticatedAthleteTest(FunctionalTestBase):
    """
    Tests the function is_authenticated_athlete in model.Athlete
    """
    def test_caching(self):
        a = model.Athlete()
        a._is_authenticated = "Not None"
        self.assertEqual(a.is_authenticated_athlete(), "Not None")

    def test_correct_athlete_returns_true(self):
        a = self.client.get_athlete()
        self.assertTrue(a.is_authenticated_athlete())

    def test_detailed_resource_state_means_true(self):
        a = model.Athlete()
        a.resource_state = attributes.DETAILED
        self.assertTrue(a.is_authenticated_athlete())

    def test_correct_athlete_not_detailed_returns_true(self):
        a = self.client.get_athlete()
        a.resource_state = attributes.SUMMARY
        # Now will have to do a look up for the authenticated athlete and check the ids match
        self.assertTrue(a.is_authenticated_athlete())

    def test_not_authenticated_athlete_is_false(self):
        CAV_ID = 1353775
        a = self.client.get_athlete(CAV_ID)
        self.assertEqual(a.resource_state, attributes.SUMMARY)
        self.assertFalse(a.is_authenticated_athlete())


class AthleteStatsTest(FunctionalTestBase):
    """
    Tests the functionality for collecting athlete statistics
    https://developers.strava.com/docs/reference/#api-Athletes-getStats
    """
    def test_basic_get_from_client(self):
        stats = self.client.get_athlete_stats()
        self.assertIsInstance(stats, model.AthleteStats)
        self.assertIsInstance(stats.recent_ride_totals, model.ActivityTotals)
        print("Biggest climb: {!r}".format(stats.biggest_climb_elevation_gain))

        # Check biggest_climb_elevation_gain has been set
        self.assertTrue(uh.meters(stats.biggest_climb_elevation_gain) >= uh.meters(0))

    def test_get_from_client_with_authenticated_id(self):
        athlete_id = self.client.get_athlete().id
        stats = self.client.get_athlete_stats(athlete_id)
        self.assertIsInstance(stats, model.AthleteStats)
        # Check same as before
        self.assertEqual(stats.biggest_climb_elevation_gain, self.client.get_athlete_stats().biggest_climb_elevation_gain)

    def test_get_from_client_with_wrong_id(self):
        CAV_ID = 1353775
        # Currently raises a requests.exceptions.HTTPError, TODO: better error handling
        self.assertRaises(requests.exceptions.HTTPError, self.client.get_athlete_stats, CAV_ID)

    def test_athlete_stats_property_option(self):
        a = self.client.get_athlete()
        stats = a.stats
        self.assertIsInstance(stats, model.AthleteStats)

    def test_athlete_stats_cached(self):
        a = self.client.get_athlete()
        a._stats = "Not None"
        stats = a.stats
        self.assertEqual(stats, "Not None")

    def test_athlete_property_not_authenticated(self):
        with self.assertRaises(NotImplementedError):
            cav = self.client.get_athlete(1353775)
