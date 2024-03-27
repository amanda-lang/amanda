from __future__ import annotations
from abc import abstractmethod, ABC
from amanda.compiler.tokens import TokenType as TT
from dataclasses import dataclass
from typing import Any

from enum import auto, IntEnum, Enum
from dataclasses import dataclass


@dataclass
class Module:
    fpath: str
    ast: Any = None
    loaded: bool = False


class Symbol(ABC):
    def __init__(self, name: str):
        self.name = name
        self.out_id = name  # symbol id in compiled source program
        self.is_property = False  # Avoid this repitition
        self.is_global = False

    @abstractmethod
    def can_evaluate(self) -> bool: ...

    @abstractmethod
    def is_type(self) -> bool: ...

    @abstractmethod
    def is_callable(self) -> bool: ...


@dataclass
class Type(Symbol):
    def __init__(
        self,
        name: str,
        zero_initialized: bool = False,
    ):
        super().__init__(name)
        self.zero_initialized = zero_initialized
        self.is_global = True

    @abstractmethod
    def __eq__(self, other: object) -> bool: ...

    @abstractmethod
    def is_numeric(self) -> bool: ...

    def is_type(self) -> bool:
        return True

    @abstractmethod
    def is_generic(self) -> bool: ...

    @abstractmethod
    def __str__(self) -> str: ...

    @abstractmethod
    def is_operable(self) -> bool: ...

    def full_field_path(self, field: str) -> str:
        return self.name + "::" + field

    @abstractmethod
    def supports_fields(self) -> bool: ...

    def supports_methods(self) -> bool:
        return True

    def get_property(self, prop: str) -> Symbol | None:
        pass

    @abstractmethod
    def is_primitive(self) -> bool: ...

    def bind(self, **ty_args: dict[str, Type]) -> Type:
        raise NotImplementedError(
            "Bind must be implemented for types that support generics"
        )


class Typed(Symbol):
    def __init__(self, name: str, ty: Type):
        super().__init__(name)
        self.type = ty

    @abstractmethod
    def can_evaluate(self) -> bool: ...

    @abstractmethod
    def is_type(self) -> bool: ...

    @abstractmethod
    def is_callable(self) -> bool: ...

    def __str__(self):
        return f"<{self.__class__.__name__} ({self.name},{self.out_id},{self.type})>"
