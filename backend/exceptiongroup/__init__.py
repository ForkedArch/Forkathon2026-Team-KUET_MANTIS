from __future__ import annotations
import sys
from typing import Callable, Sequence, TypeVar, Generic, Optional, Tuple

class BaseExceptionGroup(BaseException):
    message: str
    exceptions: tuple[BaseException, ...]

    def __new__(cls, message: str, exceptions: Sequence[BaseException]):
        if not isinstance(message, str):
            raise TypeError(f"argument 1 must be str, not {type(message).__name__}")
        if not isinstance(exceptions, Sequence):
            raise TypeError("argument 2 must be a sequence")
        for i, exc in enumerate(exceptions):
            if not isinstance(exc, BaseException):
                raise TypeError(f"item {i} of argument 2 is not an exception")

        instance = super().__new__(cls, message, exceptions)
        instance.message = message
        instance.exceptions = tuple(exceptions)
        return instance

    def derive(self, excs: Sequence[BaseException]) -> BaseExceptionGroup:
        return self.__class__(self.message, excs)

    def subgroup(self, condition: Callable[[BaseException], bool]) -> Optional[BaseExceptionGroup]:
        matched = []
        for exc in self.exceptions:
            if isinstance(exc, BaseExceptionGroup):
                sub = exc.subgroup(condition)
                if sub is not None:
                    matched.append(sub)
            elif condition(exc):
                matched.append(exc)
        if matched:
            return self.derive(matched)
        return None

    def split(self, condition: Callable[[BaseException], bool]) -> Tuple[Optional[BaseExceptionGroup], Optional[BaseExceptionGroup]]:
        m = self.subgroup(condition)
        u = self.subgroup(lambda e: not condition(e))
        return m, u

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.message!r}, {list(self.exceptions)!r})"

    def __str__(self) -> str:
        return f"{self.message} ({len(self.exceptions)} sub-exceptions)"


class ExceptionGroup(BaseExceptionGroup, Exception):
    def __new__(cls, message: str, exceptions: Sequence[Exception]):
        for i, exc in enumerate(exceptions):
            if not isinstance(exc, Exception):
                raise TypeError(f"Cannot nest BaseExceptions in an ExceptionGroup: {exc!r}")
        return super().__new__(cls, message, exceptions)


__all__ = ["BaseExceptionGroup", "ExceptionGroup"]
