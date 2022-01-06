from __future__ import division, absolute_import, print_function, unicode_literals
from stravalib.client import Client
from stravalib.tests import TestBase
import datetime
import pytz
from six.moves.urllib import parse as urlparse


class ClientUtilsTest(TestBase):
    client = Client()

    def test_utc_datetime_to_epoch_utc_datetime_given_correct_epoch_returned(self):
        dt = pytz.utc.localize(datetime.datetime(2014, 1, 1, 0, 0, 0))
        self.assertEqual(1388534400, self.client._utc_datetime_to_epoch(dt))


class ClientAuthorizationUrlTest(TestBase):
    client = Client()

    def get_url_param(self, url, key):
        """
        >>> get_url_param("http://www.example.com/?key=1", "key")
        1
        """
        return urlparse.parse_qs(urlparse.urlparse(url).query)[key][0]

    def test_incorrect_scope_raises(self):
        self.assertRaises(Exception, self.client.authorization_url, 1, "www.example.com", scope="wrong")
        self.assertRaises(Exception, self.client.authorization_url, 1, "www.example.com", scope=["wrong"])

    def test_correct_scope(self):
        url = self.client.authorization_url(1, "www.example.com", scope="activity:write")
        self.assertEqual(self.get_url_param(url, "scope"), "activity:write")
        # Check also with two params
        url = self.client.authorization_url(1, "www.example.com", scope="activity:write,activity:read_all")
        self.assertEqual(self.get_url_param(url, "scope"), "write,view_private")

    def test_scope_may_be_list(self):
        url = self.client.authorization_url(1, "www.example.com", scope=["activity:write", "activity:read_all"])
        self.assertEqual(self.get_url_param(url, "scope"), "activity:write,activity:read_all")

    def test_incorrect_approval_prompt_raises(self):
        self.assertRaises(Exception, self.client.authorization_url, 1, "www.example.com", approval_prompt="wrong")

    def test_state_param(self):
        url = self.client.authorization_url(1, "www.example.com", state="my_state")
        self.assertEqual(self.get_url_param(url, "state"), "my_state")

    def test_params(self):
        url = self.client.authorization_url(1, "www.example.com")
        self.assertEqual(self.get_url_param(url, "client_id"), "1")
        self.assertEqual(self.get_url_param(url, "redirect_uri"), "www.example.com")
        self.assertEqual(self.get_url_param(url, "approval_prompt"), "auto")
