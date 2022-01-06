# High level events that make up HTTP/1.1 conversations. Loosely inspired by
# the corresponding events in hyper-h2:
#
#     http://python-hyper.org/h2/en/stable/api.html#events
#
# Don't subclass these. Stuff will break.

import re

from . import _headers
from ._abnf import request_target
from ._util import bytesify, LocalProtocolError, validate

# Everything in __all__ gets re-exported as part of the h11 public API.
__all__ = [
    "Request",
    "InformationalResponse",
    "Response",
    "Data",
    "EndOfMessage",
    "ConnectionClosed",
]

request_target_re = re.compile(request_target.encode("ascii"))


class _EventBundle:
    _fields = []
    _defaults = {}

    def __init__(self, **kwargs):
        _parsed = kwargs.pop("_parsed", False)
        allowed = set(self._fields)
        for kwarg in kwargs:
            if kwarg not in allowed:
                raise TypeError(
                    "unrecognized kwarg {} for {}".format(
                        kwarg, self.__class__.__name__
                    )
                )
        required = allowed.difference(self._defaults)
        for field in required:
            if field not in kwargs:
                raise TypeError(
                    "missing required kwarg {} for {}".format(
                        field, self.__class__.__name__
                    )
                )
        self.__dict__.update(self._defaults)
        self.__dict__.update(kwargs)

        # Special handling for some fields

        if "headers" in self.__dict__:
            self.headers = _headers.normalize_and_validate(
                self.headers, _parsed=_parsed
            )

        if not _parsed:
            for field in ["method", "target", "http_version", "reason"]:
                if field in self.__dict__:
                    self.__dict__[field] = bytesify(self.__dict__[field])

            if "status_code" in self.__dict__:
                if not isinstance(self.status_code, int):
                    raise LocalProtocolError("status code must be integer")
                # Because IntEnum objects are instances of int, but aren't
                # duck-compatible (sigh), see gh-72.
                self.status_code = int(self.status_code)

        self._validate()

    def _validate(self):
        pass

    def __repr__(self):
        name = self.__class__.__name__
        kwarg_strs = [
            "{}={}".format(field, self.__dict__[field]) for field in self._fields
        ]
        kwarg_str = ", ".join(kwarg_strs)
        return "{}({})".format(name, kwarg_str)

    # Useful for tests
    def __eq__(self, other):
        return self.__class__ == other.__class__ and self.__dict__ == other.__dict__

    # This is an unhashable type.
    __hash__ = None


class Request(_EventBundle):
    """The beginning of an HTTP request.

    Fields:

    .. attribute:: method

       An HTTP method, e.g. ``b"GET"`` or ``b"POST"``. Always a byte
       string. :term:`Bytes-like objects <bytes-like object>` and native
       strings containing only ascii characters will be automatically
       converted to byte strings.

    .. attribute:: target

       The target of an HTTP request, e.g. ``b"/index.html"``, or one of the
       more exotic formats described in `RFC 7320, section 5.3
       <https://tools.ietf.org/html/rfc7230#section-5.3>`_. Always a byte
       string. :term:`Bytes-like objects <bytes-like object>` and native
       strings containing only ascii characters will be automatically
       converted to byte strings.

    .. attribute:: headers

       Request headers, represented as a list of (name, value) pairs. See
       :ref:`the header normalization rules <headers-format>` for details.

    .. attribute:: http_version

       The HTTP protocol version, represented as a byte string like
       ``b"1.1"``. See :ref:`the HTTP version normalization rules
       <http_version-format>` for details.

    """

    _fields = ["method", "target", "headers", "http_version"]
    _defaults = {"http_version": b"1.1"}

    def _validate(self):
        # "A server MUST respond with a 400 (Bad Request) status code to any
        # HTTP/1.1 request message that lacks a Host header field and to any
        # request message that contains more than one Host header field or a
        # Host header field with an invalid field-value."
        # -- https://tools.ietf.org/html/rfc7230#section-5.4
        host_count = 0
        for name, value in self.headers:
            if name == b"host":
                host_count += 1
        if self.http_version == b"1.1" and host_count == 0:
            raise LocalProtocolError("Missing mandatory Host: header")
        if host_count > 1:
            raise LocalProtocolError("Found multiple Host: headers")

        validate(request_target_re, self.target, "Illegal target characters")


class _ResponseBase(_EventBundle):
    _fields = ["status_code", "headers", "http_version", "reason"]
    _defaults = {"http_version": b"1.1", "reason": b""}


class InformationalResponse(_ResponseBase):
    """An HTTP informational response.

    Fields:

    .. attribute:: status_code

       The status code of this response, as an integer. For an
       :class:`InformationalResponse`, this is always in the range [100,
       200).

    .. attribute:: headers

       Request headers, represented as a list of (name, value) pairs. See
       :ref:`the header normalization rules <headers-format>` for
       details.

    .. attribute:: http_version

       The HTTP protocol version, represented as a byte string like
       ``b"1.1"``. See :ref:`the HTTP version normalization rules
       <http_version-format>` for details.

    .. attribute:: reason

       The reason phrase of this response, as a byte string. For example:
       ``b"OK"``, or ``b"Not Found"``.

    """

    def _validate(self):
        if not (100 <= self.status_code < 200):
            raise LocalProtocolError(
                "InformationalResponse status_code should be in range "
                "[100, 200), not {}".format(self.status_code)
            )


class Response(_ResponseBase):
    """The beginning of an HTTP response.

    Fields:

    .. attribute:: status_code

       The status code of this response, as an integer. For an
       :class:`Response`, this is always in the range [200,
       600).

    .. attribute:: headers

       Request headers, represented as a list of (name, value) pairs. See
       :ref:`the header normalization rules <headers-format>` for details.

    .. attribute:: http_version

       The HTTP protocol version, represented as a byte string like
       ``b"1.1"``. See :ref:`the HTTP version normalization rules
       <http_version-format>` for details.

    .. attribute:: reason

       The reason phrase of this response, as a byte string. For example:
       ``b"OK"``, or ``b"Not Found"``.

    """

    def _validate(self):
        if not (200 <= self.status_code < 600):
            raise LocalProtocolError(
                "Response status_code should be in range [200, 600), not {}".format(
                    self.status_code
                )
            )


class Data(_EventBundle):
    """Part of an HTTP message body.

    Fields:

    .. attribute:: data

       A :term:`bytes-like object` containing part of a message body. Or, if
       using the ``combine=False`` argument to :meth:`Connection.send`, then
       any object that your socket writing code knows what to do with, and for
       which calling :func:`len` returns the number of bytes that will be
       written -- see :ref:`sendfile` for details.

    .. attribute:: chunk_start

       A marker that indicates whether this data object is from the start of a
       chunked transfer encoding chunk. This field is ignored when when a Data
       event is provided to :meth:`Connection.send`: it is only valid on
       events emitted from :meth:`Connection.next_event`. You probably
       shouldn't use this attribute at all; see
       :ref:`chunk-delimiters-are-bad` for details.

    .. attribute:: chunk_end

       A marker that indicates whether this data object is the last for a
       given chunked transfer encoding chunk. This field is ignored when when
       a Data event is provided to :meth:`Connection.send`: it is only valid
       on events emitted from :meth:`Connection.next_event`. You probably
       shouldn't use this attribute at all; see
       :ref:`chunk-delimiters-are-bad` for details.

    """

    _fields = ["data", "chunk_start", "chunk_end"]
    _defaults = {"chunk_start": False, "chunk_end": False}


# XX FIXME: "A recipient MUST ignore (or consider as an error) any fields that
# are forbidden to be sent in a trailer, since processing them as if they were
# present in the header section might bypass external security filters."
# https://svn.tools.ietf.org/svn/wg/httpbis/specs/rfc7230.html#chunked.trailer.part
# Unfortunately, the list of forbidden fields is long and vague :-/
class EndOfMessage(_EventBundle):
    """The end of an HTTP message.

    Fields:

    .. attribute:: headers

       Default value: ``[]``

       Any trailing headers attached to this message, represented as a list of
       (name, value) pairs. See :ref:`the header normalization rules
       <headers-format>` for details.

       Must be empty unless ``Transfer-Encoding: chunked`` is in use.

    """

    _fields = ["headers"]
    _defaults = {"headers": []}


class ConnectionClosed(_EventBundle):
    """This event indicates that the sender has closed their outgoing
    connection.

    Note that this does not necessarily mean that they can't *receive* further
    data, because TCP connections are composed to two one-way channels which
    can be closed independently. See :ref:`closing` for details.

    No fields.
    """

    pass
