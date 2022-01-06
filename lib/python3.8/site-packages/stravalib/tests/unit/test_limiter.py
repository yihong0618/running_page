import arrow

from stravalib.tests import TestBase
from stravalib.util.limiter import get_rates_from_response_headers, XRateLimitRule, get_seconds_until_next_quarter, \
    get_seconds_until_next_day, SleepingRateLimitRule

test_response = {'Status': '404 Not Found', 'X-Request-Id': 'a1a4a4973962ffa7e0f18d7c485fe741',
                 'Content-Encoding': 'gzip', 'Content-Length': '104', 'Connection': 'keep-alive',
                 'X-RateLimit-Limit': '600,30000', 'X-UA-Compatible': 'IE=Edge,chrome=1',
                 'Cache-Control': 'no-cache, private', 'Date': 'Tue, 14 Nov 2017 11:29:15 GMT',
                 'X-FRAME-OPTIONS': 'DENY', 'Content-Type': 'application/json; charset=UTF-8',
                 'X-RateLimit-Usage': '4,67'}

test_response_no_rates = {'Status': '200 OK', 'X-Request-Id': 'd465159561420f6e0239dc24429a7cf3',
                          'Content-Encoding': 'gzip', 'Content-Length': '371', 'Connection': 'keep-alive',
                          'X-UA-Compatible': 'IE=Edge,chrome=1', 'Cache-Control': 'max-age=0, private, must-revalidate',
                          'Date': 'Tue, 14 Nov 2017 13:19:31 GMT', 'X-FRAME-OPTIONS': 'DENY',
                          'Content-Type': 'application/json; charset=UTF-8'}


class LimiterTest(TestBase):
    def test_get_rates_from_response_headers(self):
        """Should return namedtuple with rates"""
        request_rates = get_rates_from_response_headers(test_response)
        self.assertEqual(600, request_rates.short_limit)
        self.assertEqual(30000, request_rates.long_limit)
        self.assertEqual(4, request_rates.short_usage)
        self.assertEqual(67, request_rates.long_usage)

    def test_get_rates_from_response_headers_missing_rates(self):
        """Should return namedtuple with None values for rates in case of missing rates in headers"""
        self.assertIsNone(get_rates_from_response_headers(test_response_no_rates))

    def test_get_seconds_until_next_quarter(self):
        """Should return number of seconds to next quarter of an hour"""
        self.assertEqual(59, get_seconds_until_next_quarter(arrow.get(2017, 11, 1, 17, 14, 0, 0)))
        self.assertEqual(59, get_seconds_until_next_quarter(arrow.get(2017, 11, 1, 17, 59, 0, 0)))
        self.assertEqual(0, get_seconds_until_next_quarter(arrow.get(2017, 11, 1, 17, 59, 59, 999999)))
        self.assertEqual(899, get_seconds_until_next_quarter(arrow.get(2017, 11, 1, 17, 0, 0, 1)))

    def test_get_seconds_until_next_day(self):
        """Should return the number of seconds until next day"""
        self.assertEqual(59, get_seconds_until_next_day(arrow.get(2017, 11, 1, 23, 59, 0, 0)))
        self.assertEqual(86399, get_seconds_until_next_day(arrow.get(2017, 11, 1, 0, 0, 0, 0)))


class XRateLimitRuleTest(TestBase):
    def test_rule_normal_response(self):
        rule = XRateLimitRule({'short': {'usage': 0, 'limit': 600, 'time': (60*15), 'lastExceeded': None},
                               'long': {'usage': 0, 'limit': 30000, 'time': (60*60*24), 'lastExceeded': None}})
        rule(test_response)
        self.assertEqual(4, rule.rate_limits['short']['usage'])
        self.assertEqual(67, rule.rate_limits['long']['usage'])

    def test_rule_missing_rates_response(self):
        rule = XRateLimitRule({'short': {'usage': 0, 'limit': 600, 'time': (60*15), 'lastExceeded': None},
                               'long': {'usage': 0, 'limit': 30000, 'time': (60*60*24), 'lastExceeded': None}})
        rule(test_response_no_rates)
        self.assertEqual(0, rule.rate_limits['short']['usage'])
        self.assertEqual(0, rule.rate_limits['long']['usage'])


class SleepingRateLimitRuleTest(TestBase):
    def setUp(self):
        self.test_response = test_response.copy()

    def test_invalid_priority(self):
        """Should raise ValueError in case of invalid priority"""
        with self.assertRaises(ValueError):
            SleepingRateLimitRule(priority='foobar')

    def test_get_wait_time_high_priority(self):
        """Should never sleep/wait after high priority requests"""
        self.assertEqual(0, SleepingRateLimitRule()._get_wait_time(42, 42, 60, 3600))

    def test_get_wait_time_medium_priority(self):
        """Should return number of seconds to next short limit divided by number of remaining requests
        for that period"""
        rule = SleepingRateLimitRule(priority='medium', short_limit=11)
        self.assertEqual(1, rule._get_wait_time(1, 1, 10, 1000))
        self.assertEqual(0.5, rule._get_wait_time(1, 1, 5, 1000))

    def test_get_wait_time_low_priority(self):
        """Should return number of seconds to next long limit divided by number of remaining requests
        for that period"""
        rule = SleepingRateLimitRule(priority='low', long_limit=11)
        self.assertEqual(1, rule._get_wait_time(1, 1, 1, 10))
        self.assertEqual(0.5, rule._get_wait_time(1, 1, 1, 5))

    def test_get_wait_time_limit_reached(self):
        """Should wait until end of period when limit is reached, regardless priority"""
        rule = SleepingRateLimitRule(short_limit=10, long_limit=100)
        self.assertEqual(42, rule._get_wait_time(10, 10, 42, 1000))
        self.assertEqual(42, rule._get_wait_time(1234, 10, 42, 1000))
        self.assertEqual(21, rule._get_wait_time(10, 100, 42, 21))
        self.assertEqual(21, rule._get_wait_time(10, 1234, 42, 21))

    def test_invocation_unchanged_limits(self):
        """Should not update limits if these don't change"""
        self.test_response['X-RateLimit-Usage'] = '0, 0'
        self.test_response['X-RateLimit-Limit'] = '10000, 1000000'
        rule = SleepingRateLimitRule()
        self.assertEqual(10000, rule.short_limit)
        self.assertEqual(1000000, rule.long_limit)
        rule(self.test_response)
        self.assertEqual(10000, rule.short_limit)
        self.assertEqual(1000000, rule.long_limit)

    def test_invocation_changed_limits(self):
        """Should update limits in case of changes, depending on limit enforcement"""
        self.test_response['X-RateLimit-Usage'] = '0, 0'
        self.test_response['X-RateLimit-Limit'] = '600, 30000'

        # without limit enforcement (default)
        rule = SleepingRateLimitRule()
        rule(self.test_response)
        self.assertEqual(600, rule.short_limit)
        self.assertEqual(30000, rule.long_limit)

        # with limit enforcement
        rule = SleepingRateLimitRule(force_limits=True)
        rule(self.test_response)
        self.assertEqual(10000, rule.short_limit)
        self.assertEqual(1000000, rule.long_limit)
