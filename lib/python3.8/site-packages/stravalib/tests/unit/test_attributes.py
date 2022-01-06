from __future__ import division, absolute_import, print_function, unicode_literals

import six

from stravalib.attributes import EntityAttribute, SUMMARY, DETAILED, ChoicesAttribute, LocationAttribute, LatLon
from stravalib.model import Athlete, SubscriptionCallback
from stravalib.tests import TestBase


class EntityAttributeTest(TestBase):

    def setUp(self):
        super(EntityAttributeTest, self).setUp()

    def test_unmarshal_non_ascii_chars(self):
        NON_ASCII_DATA = {
            'profile': 'http://dgalywyr863hv.cloudfront.net/pictures/athletes/874283/198397/1/large.jpg',
            'city': 'Ljubljana',
            'premium': True,
            'firstname': 'Bla\u017e',
            'updated_at': '2014-05-13T06:16:29Z',
            'lastname': 'Vizjak',
            'created_at': '2012-08-01T07:49:43Z',
            'follower': None,
            'sex': 'M',
            'state': 'Ljubljana',
            'country': 'Slovenia',
            'resource_state': 2,
            'profile_medium': 'http://dgalywyr863hv.cloudfront.net/pictures/athletes/874283/198397/1/medium.jpg',
            'id': 874283,
            'friend': None
        }
        athlete = EntityAttribute(Athlete, (SUMMARY, DETAILED))
        athlete.unmarshal(NON_ASCII_DATA)

    def test_identifier_char_transform(self):
        d = {
            "hub.mode": "subscribe",
            "hub.verify_token": "STRAVA",
            "hub.challenge": "15f7d1a91c1f40f8a748fd134752feb3"
        }
        scb = SubscriptionCallback.deserialize(d)
        print(scb)
        print(dir(scb))
        self.assertEqual(d['hub.mode'], scb.hub_mode)
        self.assertEqual(d['hub.verify_token'], scb.hub_verify_token)


class LocationAttributeTest(TestBase):
    def test_with_location(self):
        location = LocationAttribute((SUMMARY, DETAILED))
        self.assertEqual(LatLon(1., 2.), location.unmarshal([1., 2.]))

    def test_without_location(self):
        location = LocationAttribute((SUMMARY, DETAILED))
        self.assertIsNone(location.unmarshal([]))


class ChoicesAttributeTest(TestBase):

    def test_no_choices_kwarg_means_choices_empty_dict(self):
        c = ChoicesAttribute(six.text_type, (SUMMARY, ))
        self.assertEqual(c.choices, {})

    def test_choices_kwarg_init_works(self):
        c = ChoicesAttribute(six.text_type, (SUMMARY, ), choices={1: "one", 2: "two"})
        self.assertEqual(c.choices, {1: "one", 2: "two"})

    def test_unmarshal_data(self):
        c = ChoicesAttribute(six.text_type, (SUMMARY, ), choices={1: "one", 2: "two"})
        self.assertEqual(c.unmarshal(2), "two")
        self.assertEqual(c.unmarshal(1), "one")

    def test_unmarshal_val_not_in_choices_gives_sam_val(self):
        # TODO: Test that logging is done as well
        c = ChoicesAttribute(six.text_type, (SUMMARY, ), choices={1: "one", 2: "two"})
        self.assertEqual(c.unmarshal(0), 0)
        self.assertEqual(c.unmarshal(None), None)

    def test_marshal_data(self):
        c = ChoicesAttribute(six.text_type, (SUMMARY, ), choices={1: "one", 2: "two"})
        self.assertEqual(c.marshal("two"), 2)
        self.assertEqual(c.marshal("one"), 1)

    def test_marshal_no_key(self):
        c = ChoicesAttribute(six.text_type, (SUMMARY, ), choices={1: "one", 2: "two"})
        self.assertRaises(NotImplementedError, c.marshal, "zero")

    def test_marshal_too_many_keys(self):
        c = ChoicesAttribute(six.text_type, (SUMMARY, ), choices={1: "one", 2: "one"})
        self.assertRaises(NotImplementedError, c.marshal, "one")

    def test_with_athlete_type_example_on_model(self):
        a = Athlete.deserialize({"athlete_type": 1})
        self.assertEqual(a.athlete_type, "runner")

    def test_wrong_athlete_type(self):
        # Only allowed options are 0 and 1
        a = Athlete.deserialize({"athlete_type": 100})
        self.assertEqual(a.athlete_type, 100)
