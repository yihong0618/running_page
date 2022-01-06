from __future__ import division, absolute_import, print_function, unicode_literals

import time

from stravalib import exc
from stravalib.tests.functional import FunctionalTestBase
from stravalib.util.limiter import DefaultRateLimiter
from stravalib.util.limiter import XRateLimitRule


class ClientDefaultRateLimiterTest(FunctionalTestBase):

    def test_fail_on_rate_limit_exceeded(self):
        """ Use this test as an example """

        # setup 'short' limit for testing
        self.client.protocol.rate_limiter.rules = []
        self.client.protocol.rate_limiter.rules.append(XRateLimitRule(
            {'short': {'usage': 0, 'limit': 600, 'time': 5, 'lastExceeded': None},
             'long': {'usage': 0, 'limit': 30000, 'time': 5, 'lastExceeded': None}}))

        # interact with api to get the limits
        self.client.get_athlete()

        # acces the default rate limit rule
        rate_limit_rule = self.client.protocol.rate_limiter.rules[0]

        # get any of the rate limits, ex the 'short'
        limit = rate_limit_rule.rate_limits['short']

        # get current usage
        usage = limit['usage']
        print('last rate limit usage is {0}'.format(usage))

        # for testing purpses set the limit to usage
        limit['limit'] = usage
        print('changing limit to {0}'.format(limit['limit']))

        # expect exception because of RateLimit has been
        #  exceeded (or reached max)
        with self.assertRaises(exc.RateLimitExceeded):
            self.client.get_athlete()

        # request fired to early (less than 5 sec) causes timeout exception
        with self.assertRaises(exc.RateLimitTimeout):
            self.client.get_athlete()
        
        # once rate limit has exceeded wait until another reuqest is possible
        #  check if timout has been set
        self.assertTrue(rate_limit_rule.limit_timeout > 0)
        print('limit timeout {0}'.format(rate_limit_rule.limit_timeout))

        # reseting limit
        # simulates Strava api - it would set the usage again to 0
        limit['limit'] = 600
        print('resetting limit to {0}'.format(limit['limit']))

        try:
            # waiting until timeout expires
            time.sleep(5)

            # this time it should work again
            self.client.get_athlete()
            self.assertTrue("No exception raised")
        except (exc.RateLimitExceeded) as e:
            self.fail("limiter raised RateLimitTimeout unexpectedly!")

        # continuse other tests with DefaultRateLimiter
        print('setting default rate limiter')
        self.client.protocol.rate_limiter = DefaultRateLimiter()
