"""
Utilities
==============
Rate limiter classes.

These are basically callables that when called register that a request was
issued.  Depending on how they are configured that may cause a pause or exception
if a rate limit has been exceeded.  Obviously it is up to the calling code to ensure
that these callables are invoked with every (successful?) call to the backend
API.  (There is probably a better way to hook these into the requests library
directly ... TBD.)

From the Strava docs:
  Strava API usage is limited on a per-application basis using a short term,
  15 minute, limit and a long term, daily, limit. The default rate limit allows
  600 requests every 15 minutes, with up to 30,000 requests per day.

  This limit allows applications to make 40 requests per minute for about
  half the day.
"""
from __future__ import division, absolute_import, print_function, unicode_literals

import collections
import logging
import time
from datetime import datetime, timedelta

import arrow

from stravalib import exc


def total_seconds(td):
    """Alternative to datetime.timedelta.total_seconds
    total_seconds() only available since Python 2.7
    https://docs.python.org/2/library/datetime.html#datetime.timedelta.total_seconds
    """
    return (td.microseconds + (td.seconds + td.days * 24 * 3600) * 10**6) / 10**6


RequestRate = collections.namedtuple('RequestRate', ['short_usage', 'long_usage', 'short_limit', 'long_limit'])


def get_rates_from_response_headers(headers):
    """
    Returns a namedtuple with values for short - and long usage and limit rates found in provided HTTP response headers
    :param headers: HTTP response headers
    :type headers: dict
    :return: namedtuple with request rates or None if no rate-limit headers present in response.
    :rtype: Optional[RequestRate]
    """
    try:
        usage_rates = [int(v) for v in headers['X-RateLimit-Usage'].split(',')]
        limit_rates = [int(v) for v in headers['X-RateLimit-Limit'].split(',')]

        return RequestRate(short_usage=usage_rates[0], long_usage=usage_rates[1],
                           short_limit=limit_rates[0], long_limit=limit_rates[1])
    except KeyError:
        return None


def get_seconds_until_next_quarter(now=None):
    """
    Returns the number of seconds until the next quarter of an hour. This is the short-term rate limit used by Strava.
    :param now: A (utc) timestamp
    :type now: arrow.arrow.Arrow
    :return: the number of seconds until the next quarter, as int
    """
    if now is None:
        now = arrow.utcnow()
    return 899 - (now - now.replace(minute=(now.minute // 15) * 15, second=0, microsecond=0)).seconds


def get_seconds_until_next_day(now=None):
    """
    Returns the number of seconds until the next day (utc midnight). This is the long-term rate limit used by Strava.
    :param now: A (utc) timestamp
    :type now: arrow.arrow.Arrow
    :return: the number of seconds until next day, as int
    """
    if now is None:
        now = arrow.utcnow()
    return (now.ceil('day') - now).seconds


class XRateLimitRule(object):

    def __init__(self, limits, force_limits=False):
        """

        :param limits: THe limits structure.
        :param force_limits: If False (default), this rule will set/update its limits based on what the Strava API
        tells it. If True, the provided limits will be enforced, i.e. ignoring the limits given by the API.
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.rate_limits = limits
        # should limit args be validated?
        self.limit_time_invalid = 0
        self.force_limits = force_limits

    @property
    def limit_timeout(self):
        return self.limit_time_invalid

    def __call__(self, response_headers):
        self._update_usage(response_headers)

        for limit in self.rate_limits.values():
            self._check_limit_time_invalid(limit)
            self._check_limit_rates(limit)

    def _update_usage(self, response_headers):
        rates = get_rates_from_response_headers(response_headers)

        if rates:
            self.log.debug("Updating rate-limit limits and usage from headers: {}".format(rates))
            self.rate_limits['short']['usage'] = rates.short_usage
            self.rate_limits['long']['usage'] = rates.long_usage

            if not self.force_limits:
                self.rate_limits['short']['limit'] = rates.short_limit
                self.rate_limits['long']['limit'] = rates.long_limit

    def _check_limit_rates(self, limit):
        if limit['usage'] >= limit['limit']:
            self.log.debug("Rate limit of {0} reached.".format(limit['limit']))
            limit['lastExceeded'] = datetime.now()
            self._raise_rate_limit_exception(limit['limit'], limit['time'])

    def _check_limit_time_invalid(self, limit):
        self.limit_time_invalid = 0
        if limit['lastExceeded'] is not None:
            delta = (datetime.now() - limit['lastExceeded']).total_seconds()
            if delta < limit['time']:
                self.limit_time_invalid = limit['time'] - delta
                self.log.debug("Rate limit invalid duration {0} seconds."
                               .format(self.limit_time_invalid))
                self._raise_rate_limit_timeout(self.limit_timeout, limit['limit'])

    def _raise_rate_limit_exception(self, timeout, limit_rate):
        raise exc.RateLimitExceeded("Rate limit of {0} exceeded. "
                                    "Try again in {1} seconds.".format(limit_rate, timeout),
                                    limit=limit_rate, timeout=timeout)

    def _raise_rate_limit_timeout(self, timeout, limit_rate):
        raise exc.RateLimitTimeout("Rate limit of {0} exceeded. "
                                   "Try again in {1} seconds.".format(limit_rate, timeout),
                                   limit=limit_rate, timeout=timeout)


class SleepingRateLimitRule(object):
    """
    A rate limit rule that can be prioritized and can dynamically adapt its limits based on API responses.
    Given its priority, it will enforce a variable "cool-down" period after each response. When rate limits
    are reached within their period, this limiter will wait until the end of that period. It will NOT raise
    any kind of exception in this case.
    """
    def __init__(self, priority='high', short_limit=10000, long_limit=1000000, force_limits=False):
        """
        Constructs a new SleepingRateLimitRule.
        :param priority: The priority for this rule. When 'low', the cool-down period after each request will be such
        that the long-term limits will not be exceeded. When 'medium', the cool-down period will be such that the
        short-term limits will not be exceeded. When 'high', there will be no cool-down period.
        :type priority: str
        :param short_limit: (Optional) explicit short-term limit
        :type short_limit: int
        :param long_limit: (Optional) explicit long-term limit
        :type long_limit: int
        :param force_limits: If False (default), this rule will set/update its limits based on what the Strava API
        tells it. If True, the provided limits will be enforced, i.e. ignoring the limits given by the API.
        """
        if priority not in ['low', 'medium', 'high']:
            raise ValueError('Invalid priority "{0}", expecting one of "low", "medium" or "high"'.format(priority))

        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.priority = priority
        self.short_limit = short_limit
        self.long_limit = long_limit
        self.force_limits = force_limits

    def _get_wait_time(self, short_usage, long_usage, seconds_until_short_limit, seconds_until_long_limit):
        if long_usage >= self.long_limit:
            self.log.warning('Long term API rate limit exceeded')
            return seconds_until_long_limit
        elif short_usage >= self.short_limit:
            self.log.warning('Short term API rate limit exceeded')
            return seconds_until_short_limit

        if self.priority == 'high':
            return 0
        elif self.priority == 'medium':
            return seconds_until_short_limit / (self.short_limit - short_usage)
        elif self.priority == 'low':
            return seconds_until_long_limit / (self.long_limit - long_usage)

    def __call__(self, response_headers):
        rates = get_rates_from_response_headers(response_headers)

        if rates:
            time.sleep(self._get_wait_time(rates.short_usage, rates.long_usage,
                                           get_seconds_until_next_quarter(), get_seconds_until_next_day()))
            if not self.force_limits:
                self.short_limit = rates.short_limit
                self.long_limit = rates.long_limit


class RateLimitRule(object):

    def __init__(self, requests, seconds, raise_exc=False):
        """
        :param requests: Number of requests for limit.
        :param seconds: The number of seconds for that number of requests (may be float)
        :param raise_exc: Whether to raise an exception when limit is reached (as opposed to pausing)
        """
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.timeframe = timedelta(seconds=seconds)
        self.requests = requests
        self.tab = collections.deque(maxlen=self.requests)
        self.raise_exc = raise_exc

    def __call__(self, args):
        """
        Register another request is being issued.

        Depending on configuration of the rule will pause if rate limit has
        been reached, or raise exception, etc.
        """
        # First check if the deque is full; that indicates that we'd better check whether
        # we need to pause.
        if len(self.tab) == self.requests:
            # Grab the oldest (leftmost) timestamp and check to see if it is greater than 1 second
            delta = datetime.now() - self.tab[0]
            if delta < self.timeframe:  # Has it been less than configured timeframe since oldest request?
                if self.raise_exc:
                    raise exc.RateLimitExceeded("Rate limit exceeded (can try again in {0})".format(self.timeframe - delta))
                else:
                    # Wait the difference between timeframe and the oldest request.
                    td = self.timeframe - delta
                    sleeptime = hasattr(td, 'total_seconds') and td.total_seconds() or total_seconds(td)
                    self.log.debug("Rate limit triggered; sleeping for {0}".format(sleeptime))
                    time.sleep(sleeptime)
        self.tab.append(datetime.now())


class RateLimiter(object):

    def __init__(self):
        self.log = logging.getLogger('{0.__module__}.{0.__name__}'.format(self.__class__))
        self.rules = []

    def __call__(self, args):
        """
        Register another request is being issued.
        """
        for r in self.rules:
            r(args)


class DefaultRateLimiter(RateLimiter):
    """
    Implements something similar to the default rate limit for Strava apps.

    To do this correctly we would actually need to change our logic to reset
    the limit at midnight, etc.  Will make this more complex in the future.

    Strava API usage is limited on a per-application basis using a short term,
    15 minute, limit and a long term, daily, limit. The default rate limit allows
    600 requests every 15 minutes, with up to 30,000 requests per day.
    """

    def __init__(self):
        """
        Strava API usage is limited on a per-application basis using a short term,
        15 minute, limit and a long term, daily, limit. The default rate limit
        allows 600 requests every 15 minutes, with up to 30,000 requests per day.
        This limit allows applications to make 40 requests per minute for about half the day.
        """

        super(DefaultRateLimiter, self).__init__()

        self.rules.append(XRateLimitRule(
            {'short': {'usageFieldIndex': 0, 'usage': 0,
                         # 60s * 15 = 15 min
                         'limit': 600, 'time': (60*15),
                         'lastExceeded': None},
             'long': {'usageFieldIndex': 1, 'usage': 0,
                        # 60s * 60m * 24 = 1 day
                        'limit': 30000, 'time': (60*60*24),
                        'lastExceeded': None}}))

        # XRateLimitRule used instead of timer based RateLimitRule
        # self.rules.append(RateLimitRule(requests=40, seconds=60, raise_exc=False))
        # self.rules.append(RateLimitRule(requests=30000, seconds=(3600 * 24), raise_exc=True))
