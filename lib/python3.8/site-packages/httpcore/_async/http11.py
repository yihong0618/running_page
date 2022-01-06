import enum
import time
from types import TracebackType
from typing import AsyncIterable, AsyncIterator, List, Optional, Tuple, Type, Union

import h11

from .._exceptions import (
    ConnectionNotAvailable,
    LocalProtocolError,
    RemoteProtocolError,
    map_exceptions,
)
from .._models import Origin, Request, Response
from .._synchronization import AsyncLock
from .._trace import Trace
from ..backends.base import AsyncNetworkStream
from .interfaces import AsyncConnectionInterface

H11Event = Union[
    h11.Request,
    h11.Response,
    h11.InformationalResponse,
    h11.Data,
    h11.EndOfMessage,
    h11.ConnectionClosed,
]


class HTTPConnectionState(enum.IntEnum):
    NEW = 0
    ACTIVE = 1
    IDLE = 2
    CLOSED = 3


class AsyncHTTP11Connection(AsyncConnectionInterface):
    READ_NUM_BYTES = 64 * 1024

    def __init__(
        self, origin: Origin, stream: AsyncNetworkStream, keepalive_expiry: float = None
    ) -> None:
        self._origin = origin
        self._network_stream = stream
        self._keepalive_expiry: Optional[float] = keepalive_expiry
        self._expire_at: Optional[float] = None
        self._state = HTTPConnectionState.NEW
        self._state_lock = AsyncLock()
        self._request_count = 0
        self._h11_state = h11.Connection(our_role=h11.CLIENT)

    async def handle_async_request(self, request: Request) -> Response:
        if not self.can_handle_request(request.url.origin):
            raise RuntimeError(
                f"Attempted to send request to {request.url.origin} on connection "
                f"to {self._origin}"
            )

        async with self._state_lock:
            if self._state in (HTTPConnectionState.NEW, HTTPConnectionState.IDLE):
                self._request_count += 1
                self._state = HTTPConnectionState.ACTIVE
                self._expire_at = None
            else:
                raise ConnectionNotAvailable()

        try:
            kwargs = {"request": request}
            async with Trace("http11.send_request_headers", request, kwargs) as trace:
                await self._send_request_headers(**kwargs)
            async with Trace("http11.send_request_body", request, kwargs) as trace:
                await self._send_request_body(**kwargs)
            async with Trace(
                "http11.receive_response_headers", request, kwargs
            ) as trace:
                (
                    http_version,
                    status,
                    reason_phrase,
                    headers,
                ) = await self._receive_response_headers(**kwargs)
                trace.return_value = (
                    http_version,
                    status,
                    reason_phrase,
                    headers,
                )

            return Response(
                status=status,
                headers=headers,
                content=HTTP11ConnectionByteStream(self, request),
                extensions={
                    "http_version": http_version,
                    "reason_phrase": reason_phrase,
                    "network_stream": self._network_stream,
                },
            )
        except BaseException as exc:
            async with Trace("http11.response_closed", request) as trace:
                await self._response_closed()
            raise exc

    # Sending the request...

    async def _send_request_headers(self, request: Request) -> None:
        timeouts = request.extensions.get("timeout", {})
        timeout = timeouts.get("write", None)

        with map_exceptions({h11.LocalProtocolError: LocalProtocolError}):
            event = h11.Request(
                method=request.method,
                target=request.url.target,
                headers=request.headers,
            )
        await self._send_event(event, timeout=timeout)

    async def _send_request_body(self, request: Request) -> None:
        timeouts = request.extensions.get("timeout", {})
        timeout = timeouts.get("write", None)

        assert isinstance(request.stream, AsyncIterable)
        async for chunk in request.stream:
            event = h11.Data(data=chunk)
            await self._send_event(event, timeout=timeout)

        event = h11.EndOfMessage()
        await self._send_event(event, timeout=timeout)

    async def _send_event(self, event: H11Event, timeout: float = None) -> None:
        bytes_to_send = self._h11_state.send(event)
        await self._network_stream.write(bytes_to_send, timeout=timeout)

    # Receiving the response...

    async def _receive_response_headers(
        self, request: Request
    ) -> Tuple[bytes, int, bytes, List[Tuple[bytes, bytes]]]:
        timeouts = request.extensions.get("timeout", {})
        timeout = timeouts.get("read", None)

        while True:
            event = await self._receive_event(timeout=timeout)
            if isinstance(event, h11.Response):
                break

        http_version = b"HTTP/" + event.http_version

        # h11 version 0.11+ supports a `raw_items` interface to get the
        # raw header casing, rather than the enforced lowercase headers.
        headers = event.headers.raw_items()

        return http_version, event.status_code, event.reason, headers

    async def _receive_response_body(self, request: Request) -> AsyncIterator[bytes]:
        timeouts = request.extensions.get("timeout", {})
        timeout = timeouts.get("read", None)

        while True:
            event = await self._receive_event(timeout=timeout)
            if isinstance(event, h11.Data):
                yield bytes(event.data)
            elif isinstance(event, (h11.EndOfMessage, h11.PAUSED)):
                break

    async def _receive_event(self, timeout: float = None) -> H11Event:
        while True:
            with map_exceptions({h11.RemoteProtocolError: RemoteProtocolError}):
                event = self._h11_state.next_event()

            if event is h11.NEED_DATA:
                data = await self._network_stream.read(
                    self.READ_NUM_BYTES, timeout=timeout
                )
                self._h11_state.receive_data(data)
            else:
                return event

    async def _response_closed(self) -> None:
        async with self._state_lock:
            if (
                self._h11_state.our_state is h11.DONE
                and self._h11_state.their_state is h11.DONE
            ):
                self._state = HTTPConnectionState.IDLE
                self._h11_state.start_next_cycle()
                if self._keepalive_expiry is not None:
                    now = time.monotonic()
                    self._expire_at = now + self._keepalive_expiry
            else:
                await self.aclose()

    # Once the connection is no longer required...

    async def aclose(self) -> None:
        # Note that this method unilaterally closes the connection, and does
        # not have any kind of locking in place around it.
        self._state = HTTPConnectionState.CLOSED
        await self._network_stream.aclose()

    # The AsyncConnectionInterface methods provide information about the state of
    # the connection, allowing for a connection pooling implementation to
    # determine when to reuse and when to close the connection...

    def can_handle_request(self, origin: Origin) -> bool:
        return origin == self._origin

    def is_available(self) -> bool:
        # Note that HTTP/1.1 connections in the "NEW" state are not treated as
        # being "available". The control flow which created the connection will
        # be able to send an outgoing request, but the connection will not be
        # acquired from the connection pool for any other request.
        return self._state == HTTPConnectionState.IDLE

    def has_expired(self) -> bool:
        now = time.monotonic()
        keepalive_expired = self._expire_at is not None and now > self._expire_at

        # If the HTTP connection is idle but the socket is readable, then the
        # only valid state is that the socket is about to return b"", indicating
        # a server-initiated disconnect.
        server_disconnected = (
            self._state == HTTPConnectionState.IDLE
            and self._network_stream.get_extra_info("is_readable")
        )

        return keepalive_expired or server_disconnected

    def is_idle(self) -> bool:
        return self._state == HTTPConnectionState.IDLE

    def is_closed(self) -> bool:
        return self._state == HTTPConnectionState.CLOSED

    def info(self) -> str:
        origin = str(self._origin)
        return (
            f"{origin!r}, HTTP/1.1, {self._state.name}, "
            f"Request Count: {self._request_count}"
        )

    def __repr__(self) -> str:
        class_name = self.__class__.__name__
        origin = str(self._origin)
        return (
            f"<{class_name} [{origin!r}, {self._state.name}, "
            f"Request Count: {self._request_count}]>"
        )

    # These context managers are not used in the standard flow, but are
    # useful for testing or working with connection instances directly.

    async def __aenter__(self) -> "AsyncHTTP11Connection":
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None,
    ) -> None:
        await self.aclose()


class HTTP11ConnectionByteStream:
    def __init__(self, connection: AsyncHTTP11Connection, request: Request) -> None:
        self._connection = connection
        self._request = request

    async def __aiter__(self) -> AsyncIterator[bytes]:
        kwargs = {"request": self._request}
        async with Trace("http11.receive_response_body", self._request, kwargs):
            async for chunk in self._connection._receive_response_body(**kwargs):
                yield chunk

    async def aclose(self) -> None:
        async with Trace("http11.response_closed", self._request):
            await self._connection._response_closed()
