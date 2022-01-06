import ssl
import typing

from .base import AsyncNetworkBackend, AsyncNetworkStream, NetworkBackend, NetworkStream


class MockSSLObject:
    def __init__(self, http2: bool):
        self._http2 = http2

    def selected_alpn_protocol(self) -> str:
        return "h2" if self._http2 else "http/1.1"


class MockStream(NetworkStream):
    def __init__(self, buffer: typing.List[bytes], http2: bool = False) -> None:
        self._buffer = buffer
        self._http2 = http2

    def read(self, max_bytes: int, timeout: float = None) -> bytes:
        if not self._buffer:
            return b""
        return self._buffer.pop(0)

    def write(self, buffer: bytes, timeout: float = None) -> None:
        pass

    def close(self) -> None:
        pass

    def start_tls(
        self,
        ssl_context: ssl.SSLContext,
        server_hostname: str = None,
        timeout: float = None,
    ) -> NetworkStream:
        return self

    def get_extra_info(self, info: str) -> typing.Any:
        return MockSSLObject(http2=self._http2) if info == "ssl_object" else None


class MockBackend(NetworkBackend):
    def __init__(self, buffer: typing.List[bytes], http2: bool = False) -> None:
        self._buffer = buffer
        self._http2 = http2

    def connect_tcp(
        self, host: str, port: int, timeout: float = None, local_address: str = None
    ) -> NetworkStream:
        return MockStream(list(self._buffer), http2=self._http2)

    def connect_unix_socket(self, path: str, timeout: float = None) -> NetworkStream:
        return MockStream(list(self._buffer), http2=self._http2)

    def sleep(self, seconds: float) -> None:
        pass


class AsyncMockStream(AsyncNetworkStream):
    def __init__(self, buffer: typing.List[bytes], http2: bool = False) -> None:
        self._original_buffer = buffer
        self._current_buffer = list(self._original_buffer)
        self._http2 = http2

    async def read(self, max_bytes: int, timeout: float = None) -> bytes:
        if not self._current_buffer:
            self._current_buffer = list(self._original_buffer)
        return self._current_buffer.pop(0)

    async def write(self, buffer: bytes, timeout: float = None) -> None:
        pass

    async def aclose(self) -> None:
        pass

    async def start_tls(
        self,
        ssl_context: ssl.SSLContext,
        server_hostname: str = None,
        timeout: float = None,
    ) -> AsyncNetworkStream:
        return self

    def get_extra_info(self, info: str) -> typing.Any:
        return MockSSLObject(http2=self._http2) if info == "ssl_object" else None


class AsyncMockBackend(AsyncNetworkBackend):
    def __init__(self, buffer: typing.List[bytes], http2: bool = False) -> None:
        self._buffer = buffer
        self._http2 = http2

    async def connect_tcp(
        self, host: str, port: int, timeout: float = None, local_address: str = None
    ) -> AsyncNetworkStream:
        return AsyncMockStream(list(self._buffer), http2=self._http2)

    async def connect_unix_socket(
        self, path: str, timeout: float = None
    ) -> AsyncNetworkStream:
        return AsyncMockStream(list(self._buffer), http2=self._http2)

    async def sleep(self, seconds: float) -> None:
        pass
