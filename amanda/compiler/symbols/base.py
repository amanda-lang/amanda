from __future__ import annotations
from abc import abstractmethod, ABC
from dataclasses import dataclass
from enum import Enum
from typing import Any, TYPE_CHECKING, Literal, Protocol

from dataclasses import dataclass

from amanda.compiler.module import Module
from amanda.compiler.tokens import TokenType
from utils.tycheck import unreachable

if TYPE_CHECKING:
    from amanda.compiler.ast import Annotation


class Symbol(ABC):
    def __init__(
        self,
        name: str,
        module: Module,
        annotations: list[Annotation] | None = None,
    ):
        self.name = name
        self.out_id = name  # symbol id in compiled source program
        self.is_property = False  # Avoid this repitition
        self.module = module
        self.is_global = False
        self.annotations: list[Annotation] = (
            annotations if annotations is not None else []
        )

    @abstractmethod
    def can_evaluate(self) -> bool: ...

    @abstractmethod
    def is_type(self) -> bool: ...

    @abstractmethod
    def is_callable(self) -> bool: ...

    def set_annotations(self, annotations: list[Annotation] | None):
        self.annotations: list[Annotation] = (
            annotations if annotations is not None else []
        )

    def is_builtin(self) -> bool:
        return any(map(lambda s: s.name == "embutido", self.annotations))

    def is_external(self, ctx_mod: Module) -> bool:
        return self.module.fpath != ctx_mod.fpath


@dataclass
class Type(Symbol):
    def __init__(
        self,
        name: str,
        module: Module,
        zero_initialized: bool = False,
    ):
        super().__init__(name, module)
        self.zero_initialized = zero_initialized
        self.is_global = True

    @abstractmethod
    def __eq__(self, other: object) -> bool: ...

    @abstractmethod
    def is_generic(self) -> bool: ...

    @abstractmethod
    def __str__(self) -> str: ...

    @abstractmethod
    def is_primitive(self) -> bool: ...

    @abstractmethod
    def promotion_to(self, other: Type) -> Type | None: ...

    @abstractmethod
    def supports_fields(self) -> bool: ...

    @abstractmethod
    def binop(self, op: TokenType, rhs: Type) -> Type | None: ...

    @abstractmethod
    def unaryop(self, op: TokenType) -> Type | None: ...

    @abstractmethod
    def supports_index_get(self) -> bool: ...

    @abstractmethod
    def supports_index_set(self) -> bool: ...

    @abstractmethod
    def supports_tam(self) -> bool: ...

    @abstractmethod
    def define_method(self, method: Symbol): ...

    def has_finite_constructors(self) -> bool:
        return False

    def get_constructors(self) -> list[Constructor]:
        if self.has_finite_constructors():
            unreachable(
                "Method must be implemented for types with finite constructors"
            )
        else:
            unreachable("Type has infinite constructors")

    def is_type_var(self) -> bool:
        return False

    def is_numeric(self) -> bool:
        return False

    def is_type(self) -> bool:
        return True

    def can_evaluate(self) -> bool:
        return False

    def is_callable(self) -> bool:
        return False

    def is_module(self) -> bool:
        return False

    def is_operable(self) -> bool:
        return False

    def is_constructed_from(self, generic_ty: Type) -> bool:
        return False

    def cast_to(self, other: Type) -> bool:
        return False

    def cast_from(self, other: Type) -> bool:
        return False

    def promotion_from(self, other: Type) -> Type | None:
        return None

    def full_field_path(self, field: str) -> str:
        return self.name + "::" + field

    def check_cast(self, other: Type) -> bool:
        return self.cast_to(other) or other.cast_from(self)

    def is_external(self, ctx_mod: Module) -> bool:
        return self.module.fpath != ctx_mod.fpath

    def promote_to(self, other: Type) -> Type | None:
        result = self.promotion_to(other)
        return result if result else other.promotion_from(self)

    def supports_methods(self) -> bool:
        return True

    def index_ty(self) -> Type:
        raise NotImplementedError(
            "Method must be overriden for classes that support index get"
        )

    def index_item_ty(self) -> Type:
        raise NotImplementedError(
            "Method must be overriden for classes that support index get"
        )

    def get_property(self, prop: str) -> Symbol | None:
        pass

    def bind(self, **ty_args: dict[str, Type]) -> Type:
        raise NotImplementedError(
            "Bind must be implemented for types that support generics"
        )


@dataclass
class TypeVar(Type):
    name: str
    constraints: list

    def __init__(self, name: str, module: Module):
        super().__init__(name, module)
        self.zero_initialized = False
        self.is_global = False
        self.constraints = []

    def __eq__(self, other: object) -> bool:
        return isinstance(other, TypeVar) and self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def is_generic(self) -> bool:
        return False

    def binop(self, op: TokenType, rhs: Type) -> Type | None:
        return None

    def unaryop(self, op: TokenType) -> Type | None:
        return None

    def define_method(self, method: Symbol):
        raise NotImplementedError(
            "Type var does not support method definitions"
        )

    def __str__(self) -> str:
        return self.name

    def is_primitive(self) -> bool:
        return False

    def supports_index_get(self) -> bool:
        return False

    def supports_tam(self) -> bool:
        return False

    def supports_index_set(self) -> bool:
        return False

    def promotion_to(self, other: Type) -> Type | None:
        return None

    def supports_fields(self) -> bool:
        return False

    def is_type_var(self) -> bool:
        return True


class Typed(Symbol):
    def __init__(self, name: str, ty: Type, module: Module):
        super().__init__(name, module)
        self.type = ty

    @abstractmethod
    def can_evaluate(self) -> bool: ...

    def is_type(self) -> bool:
        return False

    @abstractmethod
    def is_callable(self) -> bool: ...

    @abstractmethod
    def bind(self, **ty_args: Type) -> Typed: ...

    def __str__(self):
        return f"<{self.__class__.__name__} ({self.name},{self.out_id},{self.type})>"


@dataclass
class Constructor(Protocol):

    def index(self) -> int: ...
    def args(self) -> list[Type]: ...
