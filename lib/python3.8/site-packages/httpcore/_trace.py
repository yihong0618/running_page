from types import TracebackType
from typing import Any, Type

from ._models import Request


class Trace:
    def __init__(self, name: str, request: Request, kwargs: dict = None) -> None:
        self.name = name
        self.trace = request.extensions.get("trace")
        self.kwargs = kwargs or {}
        self.return_value: Any = None

    def __enter__(self) -> "Trace":
        if self.trace is not None:
            info = self.kwargs
            self.trace(f"{self.name}.started", info)
        return self

    def __exit__(
        self,
        exc_type: Type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None,
    ) -> None:
        if self.trace is not None:
            if exc_value is None:
                info: dict = {"return_value": self.return_value}
                self.trace(f"{self.name}.complete", info)
            else:
                info = {"exception": exc_value}
                self.trace(f"{self.name}.failed", info)

    async def __aenter__(self) -> "Trace":
        if self.trace is not None:
            info = self.kwargs
            await self.trace(f"{self.name}.started", info)
        return self

    async def __aexit__(
        self,
        exc_type: Type[BaseException] = None,
        exc_value: BaseException = None,
        traceback: TracebackType = None,
    ) -> None:
        if self.trace is not None:
            if exc_value is None:
                info: dict = {"return_value": self.return_value}
                await self.trace(f"{self.name}.complete", info)
            else:
                info = {"exception": exc_value}
                await self.trace(f"{self.name}.failed", info)
