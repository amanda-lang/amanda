from typing import NoReturn, cast, Generic, TypeVar

T = TypeVar("T")


def unwrap(option: T | None) -> T:
    return cast(T, option)


def unreachable(message: str) -> NoReturn:
    raise NotImplementedError(message)
