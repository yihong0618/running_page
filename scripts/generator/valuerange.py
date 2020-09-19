from typing import Optional


class ValueRange:
    def __init__(self) -> None:
        self._min: Optional[float] = None
        self._max: Optional[float] = None

    def __str__(self) -> str:
        if self.empty():
            return "[]"
        if self.singleton():
            return f"[{self.min()}]"
        return f"[{self.min()}, {self.max()}]"

    def empty(self) -> bool:
        return self._min is None

    def singleton(self) -> bool:
        return self._min == self._max

    def min(self) -> Optional[float]:
        return self._min

    def max(self) -> Optional[float]:
        return self._max

    def add(self, value: float) -> None:
        if self.empty():
            self._min = value
            self._max = value
            return

        assert self._min is not None
        assert self._max is not None

        if value < self._min:
            self._min = value
        elif value > self._max:
            self._max = value

    def adjust(self, delta_min: float, delta_max: float) -> None:
        if self.empty():
            return

        assert self._min is not None
        assert self._max is not None

        self._min += delta_min
        self._max += delta_max
        if self._min > self._max:
            self._min = None
            self._max = None

    def contains(self, value: float, slack: float = 0) -> bool:
        if self.empty():
            return False

        assert self._min is not None
        assert self._max is not None

        return self._min - slack <= value <= self._max + slack
