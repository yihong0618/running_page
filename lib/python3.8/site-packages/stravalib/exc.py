"""
Exceptions & Error Handling
============================
Exceptions and error handling for stravalib.
These are classes designed to capture and handle various errors encountered when interacting with the Strava API.
"""

from __future__ import division, absolute_import, print_function, unicode_literals

import requests.exceptions


class AuthError(RuntimeError):
    pass


class LoginFailed(AuthError):
    pass


class LoginRequired(AuthError):
    """
    Login is required to perform specified action.
    """


class UnboundEntity(RuntimeError):
    """
    Exception used to indicate that a model Entity is not bound to client instances.
    """


class Fault(requests.exceptions.HTTPError):
    """
    Container for exceptions raised by the remote server.
    """


class ObjectNotFound(Fault):
    """
    When we get a 404 back from an API call.
    """


class AccessUnauthorized(Fault):
    """
    When we get a 401 back from an API call.
    """


class RateLimitExceeded(RuntimeError):
    """
    Exception raised when the client rate limit has been exceeded.

    https://developers.strava.com/docs/rate-limits/
    """
    def __init__(self, msg, timeout=None, limit=None):
        super(RateLimitExceeded, self).__init__()
        self.limit = limit
        self.timeout = timeout


class RateLimitTimeout(RateLimitExceeded):
    """
    Exception raised when the client rate limit has been exceeded
    and the time to clear the limit (timeout) has not yet been reached

    https://developers.strava.com/docs/rate-limits/
    """


class ActivityUploadFailed(RuntimeError):
    pass


class ErrorProcessingActivity(ActivityUploadFailed):
    pass


class CreatedActivityDeleted(ActivityUploadFailed):
    pass


class TimeoutExceeded(RuntimeError):
    pass


class NotAuthenticatedAthlete(AuthError):
    """
    Exception when trying to access data which requires an authenticated athlete
    """
    pass
