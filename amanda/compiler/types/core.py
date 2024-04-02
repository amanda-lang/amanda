from __future__ import annotations
from enum import auto, IntEnum, Enum
from dataclasses import dataclass
from typing import Mapping, cast
from amanda.compiler.symbols.base import Symbol, Type, TypeVar, Typed
from amanda.compiler.symbols.core import VariableSymbol, MethodSym
from amanda.compiler.tokens import TokenType as TT


# Enum of types that are "known" to the compiler and may have
# special semantics
class Types(IntEnum):
    TINT = 0
    TREAL = auto()
    TBOOL = auto()
    TTEXTO = auto()
    TINDEF = auto()
    TVAZIO = auto()
    TVEC = auto()
    TREGISTO = auto()
    TNULO = auto()
    # unknown is a type used as a default type value
    # to avoid setting eval_type to null on ast nodes
    TUNKNOWN = auto()
    TGENERIC = auto()
    # Special type to represent nullable values
    TOpcao = auto()

    def __str__(self) -> str:
        if self == Types.TOpcao:
            return "Opcao"
        return self.name.lower()[1:]


@dataclass
class Primitive(Type):
    def __init__(self, tag: Types, zero_initialized: bool):
        super().__init__(str(tag), zero_initialized=zero_initialized)
        self.tag = tag
        self.is_global = True

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Primitive):
            return False
        return self.tag == other.tag

    def is_numeric(self) -> bool:
        return self.tag == Types.TINT or self.tag == Types.TREAL

    def is_type(self) -> bool:
        return True

    def is_generic(self) -> bool:
        return False

    def define_method(self, method: Symbol):
        raise NotImplementedError("TODO: implement method for primitives")

    def __str__(self) -> str:
        return str(self.tag)

    def is_operable(self) -> bool:
        return self.tag != Types.TVAZIO and self.tag != Types.TINDEF

    def supports_fields(self) -> bool:
        return False

    def cast_to(self, other: Type) -> bool:
        if not isinstance(other, Primitive):
            return False
        # Allowed conversions:
        # int -> real, bool,real,texto,indef
        # real -> int, bool,real,texto,indef
        # *bool -> texto,indef
        # texto -> int,real,bool,indef
        # indef -> int,real,bool,texto
        tag = self.tag
        other_tag = other.tag

        if tag == other_tag:
            return True

        primitives = (
            Types.TINT,
            Types.TTEXTO,
            Types.TBOOL,
            Types.TREAL,
            Types.TINDEF,
        )
        cast_table = {
            Types.TINT: primitives,
            Types.TREAL: primitives,
            Types.TTEXTO: primitives,
            Types.TBOOL: (Types.TTEXTO, Types.TINDEF),
            Types.TVEC: (Types.TINDEF,),
            Types.TREGISTO: (Types.TINDEF,),
            Types.TINDEF: (
                *primitives,
                Types.TREGISTO,
                Types.TVEC,
            ),
        }
        cast_types = cast_table.get(tag)

        return cast_types is not None and other_tag in cast_types

    def binop(self, op: TT, rhs: Type) -> Type | None:
        import amanda.compiler.ops as ops

        return ops.primitive_binop(self, op, rhs)

    def unaryop(self, op: TT) -> Type | None:
        match op:
            case TT.PLUS | TT.MINUS:
                if self.tag != Types.TINT and self.tag != Types.TREAL:
                    return None
                return self
            case TT.NAO:
                return self if self.tag == Types.TBOOL else None
            case _:
                return None

    def promotion_to(self, other: Type) -> Type | None:
        if not isinstance(other, Primitive):
            return None

        tag = self.tag
        other_tag = other.tag

        auto_cast_table = {
            Types.TINT: (Types.TREAL, Types.TINDEF),
            Types.TREAL: (Types.TINDEF,),
            Types.TBOOL: (Types.TINDEF,),
            Types.TTEXTO: (Types.TINDEF,),
        }
        auto_cast_types = auto_cast_table.get(tag)

        if not auto_cast_types or other_tag not in auto_cast_types:
            return None
        return other

    def supports_index_get(self) -> bool:
        return self.tag == Types.TTEXTO

    def supports_tam(self) -> bool:
        return self.tag == Types.TTEXTO

    def supports_index_set(self) -> bool:
        return False

    def index_ty(self) -> Type:
        if self.tag == Types.TTEXTO:
            return Primitive(Types.TINT, True)
        raise NotImplementedError("Invalid case.")

    def index_item_ty(self) -> Type:
        if self.tag == Types.TTEXTO:
            return Primitive(Types.TTEXTO, True)
        raise NotImplementedError("Invalid case.")

    def get_property(self, prop: str) -> Symbol | None:
        return None

    def is_primitive(self) -> bool:
        return self.tag in (
            Types.TINT,
            Types.TTEXTO,
            Types.TBOOL,
            Types.TREAL,
            Types.TINDEF,
        )

    def bind(self, **ty_args: dict[str, Type]) -> ConstructedTy:
        raise NotImplementedError(
            "Bind must be implemented for types that support generics"
        )


class Vector(Type):
    def __init__(self, element_type: Type):
        super().__init__(str(Types.TVEC))
        self.element_type: Type = element_type

    def get_type(self) -> Type:
        if self.element_type.kind != Types.TVEC:
            return self.element_type

        el_type = cast(Vector, self).element_type
        while el_type.kind != Types.TVEC:
            el_type = cast(Vector, el_type).element_type
        return el_type

    def binop(self, op: TT, rhs: Type) -> Type | None:
        return None

    def unaryop(self, op: TT) -> Type | None:
        return None

    def supports_index_get(self) -> bool:
        return True

    def supports_index_set(self) -> bool:
        return True

    def supports_tam(self) -> bool:
        return True

    def index_ty(self) -> Type:
        return Primitive(Types.TINT, True)

    def index_item_ty(self) -> Type:
        return self.element_type

    def __str__(self) -> str:
        return f"[{str(self.element_type)}]"

    def __eq__(self, other: object) -> bool:
        return (
            isinstance(other, Vector)
            and self.element_type == other.element_type
        )

    def is_generic(self) -> bool:
        return False

    def is_primitive(self) -> bool:
        return False

    def define_method(self, method: Symbol):
        raise NotImplementedError("Do not know what I have to do here")
        # self.methods[method.name] = cast(MethodSym, method)

    def promotion_to(self, other: Type) -> Type | None:
        if not isinstance(other, Primitive):
            return None
        return other if other.tag in (Types.TINDEF,) else None

    def supports_fields(self) -> bool:
        return False


class Registo(Type):
    def __init__(
        self,
        name: str,
        fields: dict[str, VariableSymbol],
        ty_params: set[TypeVar] | None = None,
    ):
        super().__init__(name)
        self.name = name
        self.fields = fields
        self.methods: dict[str, MethodSym] = {}
        self.ty_params: set[TypeVar] = ty_params if ty_params else set()
        self._ty_names = set(map(lambda t: t.name, self.ty_params))

    def is_callable(self) -> bool:
        return True

    def _is_opcao(self) -> bool:
        return self.name == str(Types.TOpcao)

    def supports_index_get(self) -> bool:
        return False

    def supports_index_set(self) -> bool:
        return False

    def supports_tam(self) -> bool:
        return False

    def is_generic(self) -> bool:
        return self.ty_params is not None

    def is_primitive(self) -> bool:
        return False

    def binop(self, op: TT, rhs: Type) -> Type | None:
        match (self, op, rhs):
            case [_, (TT.DOUBLEEQUAL | TT.NOTEQUAL), Registo()]:
                return Primitive(Types.TBOOL, zero_initialized=True)
            case [
                Registo(name="Opcao"),
                (TT.DOUBLEEQUAL | TT.NOTEQUAL),
                Primitive(tag=Types.TNULO),
            ]:
                return Primitive(Types.TBOOL, zero_initialized=True)
            case _:
                return None

    def unaryop(self, op: TT) -> Type | None:
        return None

    def promotion_to(self, other: Type) -> Type | None:
        if not isinstance(other, Primitive):
            return None
        return other if other.tag in (Types.TINDEF,) else None

    def bind(self, **ty_args: Type) -> ConstructedTy:
        if self.ty_params is None:
            raise NotImplementedError(
                "Cannot bind type params of non generic Registo"
            )
        for ty_arg in ty_args:
            if ty_arg not in self._ty_names:
                raise ValueError(f"Invalid type argument: {ty_arg}")
        return ConstructedTy(self, ty_args)

    def __eq__(self, other: object) -> bool:
        return isinstance(other, Registo) and self.name == other.name

    def __str__(self) -> str:
        return self.name

    def get_property(self, prop) -> Symbol | None:
        return self.fields.get(prop, self.methods.get(prop))

    def define_method(self, method: Symbol):
        self.methods[method.name] = cast(MethodSym, method)

    def supports_fields(self) -> bool:
        return True


@dataclass
class ConstructedTy(Type):
    generic_ty: Type
    bound_ty_args: dict[str, Type]

    def __init__(self, generic_ty: Type, bound_ty_args):
        super().__init__(generic_ty.name)
        self.generic_ty = generic_ty
        self.bound_ty_args = bound_ty_args

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ConstructedTy):
            return False
        if self.generic_ty != other.generic_ty:
            return False
        # Compare bound type arguments
        for ty_param, ty_arg in self.bound_ty_args.items():
            other_ty_arg = other.bound_ty_args.get(ty_param)
            if not other_ty_arg or other_ty_arg != ty_arg:
                return False
        return True

    def supports_fields(self) -> bool:
        return self.generic_ty.supports_fields()

    def is_primitive(self) -> bool:
        return False

    def is_operable(self) -> bool:
        return self.generic_ty.is_operable()

    def supports_index_get(self) -> bool:
        return self.generic_ty.supports_index_get()

    def supports_index_set(self) -> bool:
        return self.generic_ty.supports_index_set()

    def supports_tam(self) -> bool:
        return self.generic_ty.supports_tam()

    def unaryop(self, op: TT) -> Type | None:
        return self.generic_ty.unaryop(op)

    def _is_opcao(self) -> bool:
        return self.generic_ty.name == str(Types.TOpcao)

    def define_method(self, method: Symbol):
        self.generic_ty.define_method(method)

    def cast_from(self, other: Type) -> bool:
        # Only Constructed generic we know of is "Opcao". Ignore the rest
        if not isinstance(other, Primitive) or not self._is_opcao():
            return False

        inner_ty = self.bound_ty_args["T"]
        return other.tag == Types.TNULO or other.check_cast(inner_ty)

    def promotion_to(self, other: Type) -> Type | None:
        if not isinstance(other, Primitive):
            return None
        return other if other.tag in (Types.TINDEF,) else None

    def binop(self, op: TT, rhs: Type) -> Type | None:
        return self.generic_ty.binop(
            op, rhs.generic_ty if isinstance(rhs, ConstructedTy) else rhs
        )

    def promotion_from(self, other: Type) -> Type | None:
        # If not of type Talvez, return
        if not isinstance(other, Primitive) or self.generic_ty.name != str(
            Types.TOpcao
        ):
            return None

        inner_ty = self.bound_ty_args["T"]
        return (
            self
            if inner_ty == other
            or other.promote_to(inner_ty)
            or other.tag == Types.TNULO
            else None
        )

    def is_generic(self) -> bool:
        return False

    def get_property(self, prop) -> Symbol | None:
        prop = self.generic_ty.get_property(prop)
        return (
            prop if not prop else cast(Typed, prop).bind(**self.bound_ty_args)
        )

    def __str__(self) -> str:
        if self.name == str(Types.TOpcao):
            ty_arg = self.bound_ty_args["T"]
            return f"{ty_arg}?"
        return self.name
