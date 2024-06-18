from typing import NoReturn, cast, Generic, TypeVar

T = TypeVar("T")


def unwrap(option: T | None) -> T:
    if not option:
        raise TypeError("Called unwrap on none value")
    return cast(T, option)


def unreachable(message: str) -> NoReturn:
    raise NotImplementedError(message)
