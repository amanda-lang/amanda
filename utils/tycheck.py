from typing import Never, cast, Generic, TypeVar

T = TypeVar("T")

def unwrap[T](option: T | None) -> T: 
    return cast(T, option)


def unreachable(message: str) -> Never: 
    raise NotImplementedError(message)
